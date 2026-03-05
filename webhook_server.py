"""
webhook_server.py
─────────────────
Listens for Stripe payment events and automatically adds them to donations.json
so they appear live on the Streamlit tracker without anyone manually entering them.

HOW IT WORKS:
  Person pays on Stripe → Stripe sends a POST to this server → server writes
  to donations.json → Streamlit tracker picks it up on next refresh

DEPLOY THIS FOR FREE ON RAILWAY.APP:
  1. Go to railway.app → New Project → Deploy from GitHub repo
  2. Select the same repo as your Streamlit app
  3. Railway will detect this is a Python app and deploy it
  4. Go to your Railway project → Settings → Networking → Generate Domain
     (you'll get a URL like https://your-app.up.railway.app)
  5. Copy that URL — you need it for the Stripe webhook setup below

SET UP THE STRIPE WEBHOOK:
  1. stripe.com → Dashboard → Developers → Webhooks → + Add endpoint
  2. Endpoint URL: https://your-railway-url.up.railway.app/webhook
  3. Events to listen for: tick "checkout.session.completed"
  4. Click Add endpoint → copy the "Signing secret" (starts with whsec_...)
  5. Paste it below as STRIPE_WEBHOOK_SECRET

ENVIRONMENT VARIABLES (set in Railway dashboard → Variables):
  STRIPE_WEBHOOK_SECRET = whsec_your_secret_here
  ADMIN_PASSWORD        = church2025   (same as in app.py)

SHARED STORAGE:
  Both this server and app.py must read/write the SAME donations.json file.
  On Railway + Streamlit Cloud they are separate servers, so use one of:

  Option A (simplest) — GitHub commit approach:
    This server commits donations.json back to GitHub after each payment.
    Streamlit Cloud pulls the latest file on each rerun. See option A code below.

  Option B — External database:
    Use a free Supabase table instead of donations.json.
    Both app.py and this server connect to Supabase.
    See the README for Supabase upgrade instructions.
"""

import os
import json
import hmac
import hashlib
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Config ────────────────────────────────────────────────────────────────────
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_YOUR_SECRET_HERE")
DATA_FILE             = "donations.json"
PORT                  = int(os.environ.get("PORT", 8080))

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_donations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_donations(donations):
    with open(DATA_FILE, "w") as f:
        json.dump(donations, f, indent=2)

def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify the request genuinely came from Stripe."""
    try:
        parts = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = parts.get("t", "")
        v1_sig    = parts.get("v1", "")
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, v1_sig)
    except Exception:
        return False

def add_stripe_donation(session: dict):
    """Extract payment info from Stripe session and save it."""
    amount_total  = session.get("amount_total", 0) / 100   # Stripe uses pence
    currency      = session.get("currency", "gbp").upper()
    customer_name = "Anonymous Donor"
    anonymous     = True

    # Try to get the donor name from metadata or customer details
    metadata = session.get("metadata", {})
    if metadata.get("donor_name"):
        customer_name = metadata["donor_name"]
        anonymous     = False
    elif session.get("customer_details", {}).get("name"):
        customer_name = session["customer_details"]["name"]
        anonymous     = False

    if currency != "GBP":
        print(f"[webhook] Skipping non-GBP payment: {currency}")
        return

    donation = {
        "name":      customer_name,
        "amount":    float(amount_total),
        "anonymous": anonymous,
        "source":    "stripe",
        "stripe_id": session.get("id", ""),
        "time":      datetime.now().isoformat(),
    }

    donations = load_donations()

    # Prevent duplicate webhook deliveries
    existing_ids = {d.get("stripe_id") for d in donations}
    if donation["stripe_id"] and donation["stripe_id"] in existing_ids:
        print(f"[webhook] Duplicate, skipping: {donation['stripe_id']}")
        return

    donations.append(donation)
    save_donations(donations)
    print(f"[webhook] ✅ Saved donation: £{amount_total:.2f} from {customer_name}")

    # ── Push donations.json to GitHub so Streamlit Cloud picks it up ─────────
    try:
        import requests, base64
        token   = os.environ["GIT_TOKEN"]
        repo    = os.environ.get("GIT_REPO", "rakeshchurchdev/budget_tracker")
        api_url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
        headers = {"Authorization": f"token {token}"}
        get_resp = requests.get(api_url, headers=headers).json()
        sha = get_resp.get("sha", "")
        with open(DATA_FILE, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        put_resp = requests.put(api_url, headers=headers, json={
            "message": f"donation: £{amount_total:.2f} from {customer_name}",
            "content": content,
            "sha": sha,
        })
        if put_resp.status_code in (200, 201):
            print(f"[webhook] ✅ Pushed donations.json to GitHub")
        else:
            print(f"[webhook] ⚠️ GitHub push returned {put_resp.status_code}: {put_resp.text}")
    except Exception as e:
        print(f"[webhook] ❌ GitHub push failed: {e}")

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Health check — useful for Railway to confirm the server is up."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Conference Fund Webhook Server is running.")

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        payload        = self.rfile.read(content_length)
        sig_header     = self.headers.get("Stripe-Signature", "")

        if not verify_stripe_signature(payload, sig_header, STRIPE_WEBHOOK_SECRET):
            print("[webhook] ❌ Invalid signature — request ignored")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        event_type = event.get("type", "")
        print(f"[webhook] Event received: {event_type}")

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            if session.get("payment_status") == "paid":
                add_stripe_donation(session)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[webhook] 🚀 Webhook server starting on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    server.serve_forever()
