import streamlit as st
import json
import os
import time
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Conference Fund 2025",
    page_icon="✝️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

GOAL           = 50_000
DATA_FILE      = "donations.json"
ADMIN_PASSWORD = "church2025"          # ← change before deploying!

# ─────────────────────────────────────────────────────────────────────────────
# STRIPE PAYMENT LINK — paste yours here after creating it on stripe.com
# How to create one (free, 2 min):
#   1. stripe.com → Dashboard → Payment Links → + New
#   2. Add a product called "Conference Donation", price = customer chooses, GBP
#   3. Copy the https://buy.stripe.com/... link and paste below
# ─────────────────────────────────────────────────────────────────────────────
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/test_fZu28r9ZSaLogNmc6v3ks00"

# GitHub repo where donations.json is stored (same repo as webhook_server.py pushes to)
GITHUB_REPO      = "rakeshchurchdev/budget_tracker"
GITHUB_FILE      = "donations.json"
GITHUB_API_URL   = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_donations():
    """Load donations via GitHub API — always returns latest committed version."""
    try:
        import urllib.request, base64
        token   = st.secrets.get("GIT_TOKEN", os.environ.get("GIT_TOKEN", ""))
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode())
            # GitHub API returns file content as base64
            decoded = base64.b64decode(payload["content"]).decode("utf-8")
            return json.loads(decoded)
    except Exception:
        # Fallback to local file
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return []

def save_donations(donations):
    """Save donations locally (used for manual entries — webhook handles Stripe ones)."""
    with open(DATA_FILE, "w") as f:
        json.dump(donations, f, indent=2)

def push_to_github(donations):
    """Push updated donations.json to GitHub after a manual entry."""
    try:
        import urllib.request, urllib.error, base64
        token   = st.secrets.get("GIT_TOKEN", os.environ.get("GIT_TOKEN", ""))
        if not token:
            return  # No token configured, skip push
        headers = {"Authorization": f"token {token}", "Content-Type": "application/json",
                   "Accept": "application/vnd.github.v3+json"}
        # Get current SHA
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req) as resp:
            sha = json.loads(resp.read()).get("sha", "")
        # Push updated file
        data = json.dumps({
            "message": "manual donation entry",
            "content": base64.b64encode(json.dumps(donations, indent=2).encode()).decode(),
            "sha": sha,
        }).encode()
        req = urllib.request.Request(GITHUB_API_URL, data=data, headers=headers, method="PUT")
        urllib.request.urlopen(req)
    except Exception as e:
        pass  # Silently fail — donation is still saved locally

def total_raised(donations):
    return sum(d["amount"] for d in donations)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,400&display=swap');

html, body, [class*="css"] { background-color: #0a0e1a !important; color: #e8dfc8 !important; }
.stApp { background: #0a0e1a; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; }

.hero-title {
    font-family: 'Cinzel', serif;
    font-size: clamp(2rem, 6vw, 3.8rem);
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #f5d06b 0%, #e8b84b 40%, #c8922a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.05em;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-family: 'Crimson Pro', serif;
    font-size: 1.15rem;
    text-align: center;
    color: #9ba8c0;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}
.stats-row { display: flex; gap: 1rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap; }
.stat-card {
    background: linear-gradient(145deg, #131929, #0e1420);
    border: 1px solid #2a3550; border-radius: 16px;
    padding: 1.2rem 2rem; text-align: center; flex: 1; min-width: 140px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(245,208,107,0.08);
}
.stat-value { font-family: 'Cinzel', serif; font-size: 1.9rem; font-weight: 700; color: #f5d06b; line-height: 1; }
.stat-label { font-family: 'Crimson Pro', serif; font-size: 0.85rem; color: #6a7a99; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 0.3rem; }
.progress-wrap {
    background: #131929; border: 1px solid #2a3550; border-radius: 50px;
    height: 36px; overflow: hidden; margin-bottom: 0.5rem;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.5); position: relative;
}
.progress-fill {
    height: 100%; border-radius: 50px;
    background: linear-gradient(90deg, #c8922a, #e8b84b, #f5d06b, #fff0a0, #f5d06b);
    background-size: 200% 100%; animation: shimmer 2.5s linear infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.progress-pct { font-family: 'Cinzel', serif; font-size: 0.85rem; color: #9ba8c0; text-align: right; margin-bottom: 2rem; }

.pay-box {
    background: linear-gradient(145deg, #12200e, #0a1408);
    border: 1px solid #3a5a2a; border-radius: 20px;
    padding: 2rem 1.5rem; text-align: center; margin: 1.5rem 0;
}
.pay-title { font-family: 'Cinzel', serif; font-size: 1.2rem; color: #f5d06b; letter-spacing: 0.1em; margin-bottom: 0.5rem; }
.pay-sub { font-family: 'Crimson Pro', serif; font-size: 0.95rem; color: #6a8a5a; margin-bottom: 1.5rem; }
.pay-btn {
    display: inline-block;
    background: linear-gradient(135deg, #2e7d2e, #3aaa3a);
    color: #ffffff !important; font-family: 'Cinzel', serif;
    font-weight: 700; font-size: 1.1rem; letter-spacing: 0.1em;
    text-decoration: none !important; padding: 0.85rem 2.5rem;
    border-radius: 50px; box-shadow: 0 4px 20px rgba(58,170,58,0.35);
}
.pay-note { font-family: 'Crimson Pro', serif; font-size: 0.8rem; color: #3a5a2a; margin-top: 1rem; }
.stripe-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #0d1520; border: 1px solid #2a3550; border-radius: 8px;
    padding: 0.3rem 0.8rem; font-family: 'Crimson Pro', serif;
    font-size: 0.75rem; color: #6a7a99; margin-top: 0.8rem;
}
.presets { display: flex; gap: 0.6rem; justify-content: center; flex-wrap: wrap; margin-bottom: 1.2rem; }
.preset-chip {
    background: #0e1420; border: 1px solid #2a3550; border-radius: 50px;
    padding: 0.35rem 1rem; font-family: 'Cinzel', serif; font-size: 0.85rem;
    color: #9ba8c0; text-decoration: none;
}
.preset-chip:hover { background: #1a2535; border-color: #f5d06b; color: #f5d06b; }

.section-heading {
    font-family: 'Cinzel', serif; font-size: 1rem; color: #f5d06b;
    letter-spacing: 0.2em; text-transform: uppercase;
    border-bottom: 1px solid #2a3550; padding-bottom: 0.5rem;
    margin-bottom: 1.2rem; margin-top: 2rem;
}
.donor-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.75rem 1rem; border-radius: 10px;
    background: #0e1420; border: 1px solid #1e2a40;
    margin-bottom: 0.5rem; animation: fadeIn 0.4s ease;
}
.donor-row:first-child { border-color: #3a4d20; background: linear-gradient(90deg, #0e1a10, #0e1420); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.donor-name { font-family: 'Crimson Pro', serif; font-size: 1.05rem; color: #d4c9a8; }
.donor-amount { font-family: 'Cinzel', serif; font-size: 1rem; font-weight: 700; color: #f5d06b; }
.donor-time { font-size: 0.72rem; color: #4a5a78; font-family: 'Crimson Pro', serif; }
.donor-source { font-size: 0.68rem; font-family: 'Crimson Pro', serif; padding: 1px 7px; border-radius: 20px; margin-left: 0.4rem; }
.source-stripe { background: #0d1e30; color: #5b9bd5; border: 1px solid #1a3550; }
.source-manual { background: #1a1a0e; color: #9b9b5d; border: 1px solid #3a3a1a; }
.new-badge {
    background: #2a4a2a; color: #7ddb7d; font-size: 0.65rem; font-family: 'Cinzel', serif;
    letter-spacing: 0.1em; padding: 2px 8px; border-radius: 20px; border: 1px solid #3a6a3a; margin-left: 0.5rem;
}
.empty-state {
    text-align: center; padding: 3rem 1rem; color: #3a4a68;
    font-family: 'Crimson Pro', serif; font-size: 1.1rem; font-style: italic;
    border: 1px dashed #1e2a40; border-radius: 12px;
}
.goal-complete {
    background: linear-gradient(135deg, #1a3a1a, #0a1e0a); border: 2px solid #4a8a4a;
    border-radius: 16px; padding: 1.5rem; text-align: center;
    font-family: 'Cinzel', serif; font-size: 1.5rem; color: #7ddb7d;
    margin: 1rem 0 2rem; animation: glow 2s ease-in-out infinite alternate;
}
@keyframes glow { from { box-shadow: 0 0 10px rgba(125,219,125,0.2); } to { box-shadow: 0 0 30px rgba(125,219,125,0.5); } }
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: #0e1420 !important; border: 1px solid #2a3550 !important;
    color: #e8dfc8 !important; border-radius: 8px !important; font-family: 'Crimson Pro', serif !important;
}
.stTextInput label, .stNumberInput label { color: #9ba8c0 !important; font-family: 'Crimson Pro', serif !important; }
div[data-testid="stForm"] { background: #0e1420; border: 1px solid #2a3550; border-radius: 16px; padding: 1.5rem; }
.stButton > button {
    width: 100%; background: linear-gradient(135deg, #c8922a, #e8b84b) !important;
    color: #0a0e1a !important; font-family: 'Cinzel', serif !important; font-weight: 700 !important;
    font-size: 1rem !important; letter-spacing: 0.1em !important; border: none !important;
    border-radius: 8px !important; padding: 0.6rem 0 !important;
}
.stCheckbox > label { color: #9ba8c0 !important; font-family: 'Crimson Pro', serif !important; }
.info-box {
    background: #0d1520; border: 1px solid #1e2a40; border-radius: 12px;
    padding: 1rem 1.2rem; font-family: 'Crimson Pro', serif;
    font-size: 0.9rem; color: #6a7a99; margin-top: 1rem; line-height: 1.6;
}
.info-box b { color: #9ba8c0; }
hr { border-color: #1e2a40 !important; margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
donations   = load_donations()
raised      = total_raised(donations)
pct         = min(raised / GOAL * 100, 100)
remaining   = max(GOAL - raised, 0)
donor_count = len(donations)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">✝ Conference Fund 2025</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Together we rise · £50,000 Goal</div>', unsafe_allow_html=True)

if raised >= GOAL:
    st.markdown('<div class="goal-complete">🎉 GOAL REACHED — PRAISE GOD! 🎉</div>', unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-value">£{raised:,.0f}</div><div class="stat-label">Raised</div></div>
  <div class="stat-card"><div class="stat-value">£{GOAL:,.0f}</div><div class="stat-label">Goal</div></div>
  <div class="stat-card"><div class="stat-value">£{remaining:,.0f}</div><div class="stat-label">Remaining</div></div>
  <div class="stat-card"><div class="stat-value">{donor_count}</div><div class="stat-label">Donors</div></div>
</div>
""", unsafe_allow_html=True)

# ── Progress bar ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="progress-wrap">
  <div class="progress-fill" style="width:{pct:.1f}%"></div>
</div>
<div class="progress-pct">{pct:.1f}% of goal reached</div>
""", unsafe_allow_html=True)

# ── Stripe Pay Section ────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">💳 Give Online</div>', unsafe_allow_html=True)

stripe_configured = "YOUR_LINK_HERE" not in STRIPE_PAYMENT_LINK

if stripe_configured:
    st.markdown(f"""
    <div class="pay-box">
      <div class="pay-title">✝ Give to the Conference</div>
      <div class="pay-sub">Click below · On the checkout page, set the <b style="color:#a0c070;">Quantity = your donation in £</b><br>
      e.g. Quantity <b style="color:#f5d06b;">50</b> = £50 &nbsp;·&nbsp; Quantity <b style="color:#f5d06b;">100</b> = £100</div>
      <div class="presets">
        <a class="preset-chip" href="{STRIPE_PAYMENT_LINK}" target="_blank">£10 → qty 10</a>
        <a class="preset-chip" href="{STRIPE_PAYMENT_LINK}" target="_blank">£25 → qty 25</a>
        <a class="preset-chip" href="{STRIPE_PAYMENT_LINK}" target="_blank">£50 → qty 50</a>
        <a class="preset-chip" href="{STRIPE_PAYMENT_LINK}" target="_blank">£100 → qty 100</a>
        <a class="preset-chip" href="{STRIPE_PAYMENT_LINK}" target="_blank">£250 → qty 250</a>
      </div>
      <a class="pay-btn" href="{STRIPE_PAYMENT_LINK}" target="_blank">💛 Donate Now</a>
      <div class="pay-note">🔢 On the next page — type your £ amount into the <b>Quantity</b> box</div>
      <div><span class="stripe-badge">🔒 Powered by Stripe · Card, Apple Pay & Google Pay accepted</span></div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="pay-box" style="border-color:#3a3020; background: linear-gradient(145deg,#1e1a0a,#141008);">
      <div class="pay-title" style="color:#9b8a4a;">⚙️ Online Payment Not Yet Set Up</div>
      <div class="pay-sub" style="color:#6a5a3a;">Admin: replace STRIPE_PAYMENT_LINK in app.py with your Stripe link</div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("📖 How to set up Stripe payments (5 min, free account)"):
        st.markdown("""
**Step 1 — Create a free Stripe account**
Go to [stripe.com](https://stripe.com) → Sign up. No monthly fee. They take **1.5% + 20p per UK card transaction**.

**Step 2 — Create a Payment Link**
- Dashboard → **Payment Links** → **+ New**
- Click **+ Add a product** → Name: `Conference Donation`
- Price: tick **"Customer chooses price"** → Currency: **GBP**
- Click **Create link** → copy the `https://buy.stripe.com/...` URL

**Step 3 — Paste into app.py**
```python
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/paste_your_link_here"
```
Commit to GitHub → app updates automatically ✅

**Step 4 — Auto-record Stripe payments to the tracker**
When someone pays via Stripe, you need the webhook server (`webhook_server.py`) running so donations appear automatically on the tracker. See that file for setup instructions.
        """)

# ── Donor feed ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">🙏 Our Generous Donors</div>', unsafe_allow_html=True)

if not donations:
    st.markdown('<div class="empty-state">Be the first to give — every pound brings us closer to our vision.</div>', unsafe_allow_html=True)
else:
    recent = sorted(donations, key=lambda d: d["time"], reverse=True)
    for i, d in enumerate(recent[:20]):
        badge        = '<span class="new-badge">NEW</span>' if i == 0 else ""
        name_display = d["name"] if not d.get("anonymous") else "Anonymous Donor"
        ts           = d["time"][:16].replace("T", " ")
        source       = d.get("source", "manual")
        src_badge    = (
            '<span class="donor-source source-stripe">via Stripe</span>' if source == "stripe"
            else '<span class="donor-source source-manual">cash/manual</span>'
        )
        st.markdown(f"""
        <div class="donor-row">
          <div>
            <span class="donor-name">{name_display}</span>{badge}{src_badge}
            <div class="donor-time">{ts}</div>
          </div>
          <div class="donor-amount">£{d['amount']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Manual / cash donation form ───────────────────────────────────────────────
st.markdown('<div class="section-heading">✏️ Record a Cash / Manual Donation</div>', unsafe_allow_html=True)
st.markdown('<div class="info-box">Use this for <b>cash gifts, bank transfers, or cheques</b> collected in person.<br>Online card payments via Stripe are added automatically by the webhook.</div>', unsafe_allow_html=True)

with st.form("donate_form", clear_on_submit=True):
    name      = st.text_input("Donor Name", placeholder="e.g. John Smith")
    amount    = st.number_input("Amount (£)", min_value=1.0, max_value=50000.0, step=1.0, value=50.0)
    anonymous = st.checkbox("Keep name private (show as Anonymous)")
    submitted = st.form_submit_button("✝ Record Donation")

    if submitted:
        if not name.strip():
            st.error("Please enter a name.")
        else:
            new_donation = {
                "name":      name.strip(),
                "amount":    float(amount),
                "anonymous": anonymous,
                "source":    "manual",
                "time":      datetime.now().isoformat(),
            }
            donations.append(new_donation)
            save_donations(donations)
            push_to_github(donations)
            st.success(f"Recorded £{amount:,.2f} from {'Anonymous' if anonymous else name}. God bless! 🙏")
            time.sleep(0.5)
            st.rerun()

# ── Admin panel ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🔐 Admin Panel"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Access granted.")
        if donations:
            st.markdown("**Remove a donation:**")
            options = {
                f"{d['name']} — £{d['amount']:,.2f} ({d['time'][:10]}) [{d.get('source','manual')}]": i
                for i, d in enumerate(donations)
            }
            to_delete = st.selectbox("Select donation", list(options.keys()))
            if st.button("🗑 Delete Selected"):
                donations.pop(options[to_delete])
                save_donations(donations)
                st.success("Removed.")
                st.rerun()
        if st.button("⚠️ Reset ALL donations"):
            save_donations([])
            st.success("All cleared.")
            st.rerun()
    elif pwd:
        st.error("Incorrect password.")

# ── Footer / auto-refresh ─────────────────────────────────────────────────────
st.markdown(
    '<p style="text-align:center;color:#2a3550;font-family:\'Crimson Pro\',serif;font-size:0.8rem;margin-top:2rem;">'
    'Page refreshes every 15 seconds · Built with ❤️ for the Church</p>',
    unsafe_allow_html=True
)
time.sleep(15)
st.rerun()
