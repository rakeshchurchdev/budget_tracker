import streamlit as st
import json
import os
import time
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Conference Fund 2026",
    page_icon="✝️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

GOAL = 50_000
DATA_FILE = "donations.json"
ADMIN_PASSWORD = "church2025"   # change this!

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_donations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_donations(donations):
    with open(DATA_FILE, "w") as f:
        json.dump(donations, f, indent=2)

def total_raised(donations):
    return sum(d["amount"] for d in donations)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,400&display=swap');

/* ---- base ---- */
html, body, [class*="css"] {
    background-color: #0a0e1a !important;
    color: #e8dfc8 !important;
}
.stApp { background: #0a0e1a; }

/* hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; }

/* ---- hero title ---- */
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

/* ---- stat cards ---- */
.stats-row {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}
.stat-card {
    background: linear-gradient(145deg, #131929, #0e1420);
    border: 1px solid #2a3550;
    border-radius: 16px;
    padding: 1.2rem 2rem;
    text-align: center;
    flex: 1;
    min-width: 140px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(245,208,107,0.08);
}
.stat-value {
    font-family: 'Cinzel', serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: #f5d06b;
    line-height: 1;
}
.stat-label {
    font-family: 'Crimson Pro', serif;
    font-size: 0.85rem;
    color: #6a7a99;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* ---- progress bar ---- */
.progress-wrap {
    background: #131929;
    border: 1px solid #2a3550;
    border-radius: 50px;
    height: 36px;
    overflow: hidden;
    margin-bottom: 0.5rem;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
    position: relative;
}
.progress-fill {
    height: 100%;
    border-radius: 50px;
    background: linear-gradient(90deg, #c8922a, #e8b84b, #f5d06b, #fff0a0, #f5d06b);
    background-size: 200% 100%;
    animation: shimmer 2.5s linear infinite;
    transition: width 1s cubic-bezier(.4,0,.2,1);
    position: relative;
}
.progress-fill::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 60px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
    border-radius: 0 50px 50px 0;
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
.progress-pct {
    font-family: 'Cinzel', serif;
    font-size: 0.85rem;
    color: #9ba8c0;
    text-align: right;
    margin-bottom: 2rem;
}

/* ---- section headings ---- */
.section-heading {
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    color: #f5d06b;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    border-bottom: 1px solid #2a3550;
    padding-bottom: 0.5rem;
    margin-bottom: 1.2rem;
    margin-top: 2rem;
}

/* ---- donor row ---- */
.donor-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    background: #0e1420;
    border: 1px solid #1e2a40;
    margin-bottom: 0.5rem;
    animation: fadeIn 0.4s ease;
}
.donor-row:first-child {
    border-color: #3a4d20;
    background: linear-gradient(90deg, #0e1a10, #0e1420);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.donor-name {
    font-family: 'Crimson Pro', serif;
    font-size: 1.05rem;
    color: #d4c9a8;
}
.donor-amount {
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    font-weight: 700;
    color: #f5d06b;
}
.donor-time {
    font-size: 0.72rem;
    color: #4a5a78;
    font-family: 'Crimson Pro', serif;
}
.new-badge {
    background: #2a4a2a;
    color: #7ddb7d;
    font-size: 0.65rem;
    font-family: 'Cinzel', serif;
    letter-spacing: 0.1em;
    padding: 2px 8px;
    border-radius: 20px;
    border: 1px solid #3a6a3a;
    margin-left: 0.5rem;
}

/* ---- empty state ---- */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #3a4a68;
    font-family: 'Crimson Pro', serif;
    font-size: 1.1rem;
    font-style: italic;
    border: 1px dashed #1e2a40;
    border-radius: 12px;
}

/* ---- complete banner ---- */
.goal-complete {
    background: linear-gradient(135deg, #1a3a1a, #0a1e0a);
    border: 2px solid #4a8a4a;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    font-family: 'Cinzel', serif;
    font-size: 1.5rem;
    color: #7ddb7d;
    margin: 1rem 0 2rem;
    animation: glow 2s ease-in-out infinite alternate;
}
@keyframes glow {
    from { box-shadow: 0 0 10px rgba(125,219,125,0.2); }
    to   { box-shadow: 0 0 30px rgba(125,219,125,0.5); }
}

/* ---- streamlit widget overrides ---- */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #0e1420 !important;
    border: 1px solid #2a3550 !important;
    color: #e8dfc8 !important;
    border-radius: 8px !important;
    font-family: 'Crimson Pro', serif !important;
}
.stTextInput label, .stNumberInput label {
    color: #9ba8c0 !important;
    font-family: 'Crimson Pro', serif !important;
    letter-spacing: 0.05em;
}
div[data-testid="stForm"] {
    background: #0e1420;
    border: 1px solid #2a3550;
    border-radius: 16px;
    padding: 1.5rem;
}
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #c8922a, #e8b84b) !important;
    color: #0a0e1a !important;
    font-family: 'Cinzel', serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 0.1em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 0 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(200,146,42,0.4) !important;
}
.stCheckbox > label { color: #9ba8c0 !important; font-family: 'Crimson Pro', serif !important; }
.stSuccess { background: #0e1e0e !important; border-color: #3a6a3a !important; }
.stError   { background: #1e0e0e !important; border-color: #6a2a2a !important; }

/* divider */
hr { border-color: #1e2a40 !important; margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
donations = load_donations()
raised = total_raised(donations)
pct = min(raised / GOAL * 100, 100)
remaining = max(GOAL - raised, 0)
donor_count = len(donations)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">✝ Conference Fund 2025</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Together we rise · £50,000 Goal</div>', unsafe_allow_html=True)

# ── Goal complete banner ───────────────────────────────────────────────────────
if raised >= GOAL:
    st.markdown('<div class="goal-complete">🎉 GOAL REACHED — PRAISE GOD! 🎉</div>', unsafe_allow_html=True)

# ── Stats row ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-value">£{raised:,.0f}</div>
    <div class="stat-label">Raised</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">£{GOAL:,.0f}</div>
    <div class="stat-label">Goal</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">£{remaining:,.0f}</div>
    <div class="stat-label">Remaining</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{donor_count}</div>
    <div class="stat-label">Donors</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Progress bar ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="progress-wrap">
  <div class="progress-fill" style="width:{pct:.1f}%"></div>
</div>
<div class="progress-pct">{pct:.1f}% of goal reached</div>
""", unsafe_allow_html=True)

# ── Donor feed ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">🙏 Our Generous Donors</div>', unsafe_allow_html=True)

if not donations:
    st.markdown('<div class="empty-state">Be the first to give — every pound brings us closer to our vision.</div>', unsafe_allow_html=True)
else:
    recent = sorted(donations, key=lambda d: d["time"], reverse=True)
    for i, d in enumerate(recent[:20]):
        badge = '<span class="new-badge">NEW</span>' if i == 0 else ""
        name_display = d["name"] if not d.get("anonymous") else "Anonymous Donor"
        ts = d["time"][:16].replace("T", " ")
        st.markdown(f"""
        <div class="donor-row">
          <div>
            <span class="donor-name">{name_display}</span>{badge}
            <div class="donor-time">{ts}</div>
          </div>
          <div class="donor-amount">£{d['amount']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Add donation ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-heading">💛 Record a Donation</div>', unsafe_allow_html=True)

with st.form("donate_form", clear_on_submit=True):
    name = st.text_input("Your Name", placeholder="e.g. John Smith")
    amount = st.number_input("Amount (£)", min_value=1.0, max_value=50000.0, step=1.0, value=50.0)
    anonymous = st.checkbox("Keep my name private (show as Anonymous)")
    submitted = st.form_submit_button("✝ Record My Donation")

    if submitted:
        if not name.strip():
            st.error("Please enter your name.")
        else:
            new_donation = {
                "name": name.strip(),
                "amount": float(amount),
                "anonymous": anonymous,
                "time": datetime.now().isoformat(),
            }
            donations.append(new_donation)
            save_donations(donations)
            st.success(f"Thank you, {'Anonymous' if anonymous else name}! £{amount:,.2f} recorded. God bless you! 🙏")
            time.sleep(0.5)
            st.rerun()

# ── Admin panel ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🔐 Admin Panel"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Access granted.")

        # Delete a donation
        if donations:
            st.markdown("**Remove a donation:**")
            options = {
                f"{d['name']} — £{d['amount']:,.2f} ({d['time'][:10]})": i
                for i, d in enumerate(donations)
            }
            to_delete = st.selectbox("Select donation to remove", list(options.keys()))
            if st.button("🗑 Delete Selected"):
                idx = options[to_delete]
                donations.pop(idx)
                save_donations(donations)
                st.success("Donation removed.")
                st.rerun()

        # Reset all
        if st.button("⚠️ Reset ALL donations", type="primary"):
            save_donations([])
            st.success("All donations cleared.")
            st.rerun()

    elif pwd:
        st.error("Incorrect password.")

# ── Auto-refresh every 15s ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#2a3550;font-family:\'Crimson Pro\',serif;font-size:0.8rem;">'
    'Page auto-refreshes every 15 seconds · Built with ❤️ for the Church</p>',
    unsafe_allow_html=True
)
time.sleep(15)
st.rerun()
