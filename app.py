# ==============================
# 1. IMPORTS
# ==============================
import pickle
import html
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ==============================
# 2. LOGGING
# ==============================
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ==============================
# 3. PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 4. CONSTANTS
# ==============================
WEEKS_PER_MONTH: float = 4.333
DAYS_PER_MONTH: int = 30
CHAT_HEIGHT_PX: int = 450
ADMIN_CHAT_HEIGHT_PX: int = 450
AUTO_REFRESH_SECONDS: int = 3

# ==============================
# 5. THEME & STYLES
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.block-container {
    padding-top: 3rem !important;
    padding-bottom: 1rem !important;
}

html, body {
    background-color: #0e1117;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

/* --- Sidebar --- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220, #0e1622);
    border-right: 1px solid #1f2a36;
}

section[data-testid="stSidebar"] .stRadio > div { gap: 10px; }

section[data-testid="stSidebar"] label {
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    white-space: nowrap !important;
    width: 100% !important;
    box-sizing: border-box;
}

section[data-testid="stSidebar"] label:hover { background: #1a2330; }

section[data-testid="stSidebar"] label[data-selected="true"] {
    background: #2563eb;
    color: white;
}

/* --- Login Page --- */
.title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    color: #A0AEC0;
    text-align: center;
    margin-bottom: 40px;
    font-size: 16px;
}

.section {
    font-size: 22px;
    font-weight: 600;
    text-align: center;
    color: white;
    margin-bottom: 8px;
}

.small {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 24px;
    font-size: 14px;
}

/* Input fields */
.stTextInput > div > div > input {
    background: #1a222c;
    border: 1px solid #2a3748;
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    width: 100% !important;
    box-sizing: border-box;
    transition: border-color 0.2s;
}

.stTextInput > div > div > input:focus {
    border-color: #3b82f6;
    outline: none;
}

/* Buttons */
.stButton > button {
    background: #1f77ff;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 12px 24px;
    font-weight: 600;
    width: 100%;
    transition: all 0.2s;
    height: 45px;
}

.stButton > button:hover {
    background: #155edb;
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(31, 119, 255, 0.3);
}

/* Login footer */
.login-footer {
    text-align: center;
    margin-top: 16px;
    color: #8a94a3;
}

.login-footer a { color: #3b82f6; text-decoration: none; }

/* Alert override */
.stAlert {
    background: transparent;
    color: #ef4444;
    border: none;
    padding: 8px 0;
}

/* --- App styles --- */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #1f2a36;
    margin-bottom: 20px;
}

.app-subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 20px;
}

.role-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.role-badge.admin {
    background: #7c3aed22;
    color: #a78bfa;
    border: 1px solid #7c3aed44;
}

.role-badge.user {
    background: #0369a122;
    color: #38bdf8;
    border: 1px solid #0369a144;
}

.unified-chat {
    background: #0b1220;
    border-radius: 20px;
    border: 1px solid #1f2a36;
    overflow: hidden;
    margin-bottom: 20px;
}

.chat-input-container {
    padding: 16px 20px;
    background: #0e1622;
    border-top: 1px solid #1f2a36;
    margin-top: 0;
}

.chat-input-container .stTextInput > div > div > input {
    background: #1a2330;
    border: 1px solid #2a3748;
    border-radius: 24px;
    color: white;
    padding: 12px 18px;
}

.chat-input-container .stButton > button {
    border-radius: 24px;
    height: auto;
    padding: 10px 20px;
}

.chat-input-container .stForm { margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# ==============================
# 6. SUPABASE CLIENT
# ==============================
@st.cache_resource
def get_supabase_client() -> Client:
    """Cached Supabase client — created once per server process."""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

supabase: Client = get_supabase_client()

# ==============================
# 7. SESSION STATE
# ==============================
_SESSION_DEFAULTS: Dict[str, Any] = {
    "authenticated": False,
    "user": None,           # dict: id, username, email, role
    "role": None,           # "user" | "admin"  — always read from DB
    "selected_user_id": None,
    "auto_refresh": False,
    "draft_message": "",
}

for _key, _default in _SESSION_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ==============================
# 8. MODEL
# ==============================
@st.cache_resource
def load_model():
    """Load the pickled loan risk model exactly once."""
    with open("loan_model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# ==============================
# 9. AUTH FUNCTIONS
# ==============================

def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Sign in via Supabase Auth.
    Role is ALWAYS read from public.users — never from UI input.
    Password hashing is handled entirely by Supabase Auth.
    Returns a clean user profile dict (no password) on success.
    """
    try:
        # Step 1 — Supabase Auth validates credentials
        auth_res = supabase.auth.sign_in_with_password({
            "email": email.lower().strip(),
            "password": password,
        })

        if not auth_res.user:
            return None

        # Step 2 — Fetch role + profile from public.users
        profile_res = (
            supabase.table("users")
            .select("id, username, email, role")
            .eq("id", str(auth_res.user.id))
            .single()
            .execute()
        )

        if not profile_res.data:
            logger.error("Auth succeeded but no public.users row for %s", auth_res.user.id)
            return None

        # Step 3 — Return profile only (password never touches session)
        return profile_res.data

    except Exception as exc:
        logger.error("Authentication error: %s", exc)
        return None


def require_role(allowed_roles: List[str]) -> None:
    """
    Guard function — call at the top of every page.
    Stops execution immediately if the user's role is not allowed.
    Role is always read from session state which was set from the DB at login.
    """
    current_role = st.session_state.get("role")
    if current_role not in allowed_roles:
        st.error("⛔ Access denied. You don't have permission to view this page.")
        st.stop()


def logout() -> None:
    """Sign out of Supabase Auth and completely wipe session state."""
    try:
        supabase.auth.sign_out()
    except Exception as exc:
        logger.error("Sign out error: %s", exc)
    # Wipe every key — no stale data left behind
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ==============================
# 10. HELPER FUNCTIONS
# ==============================

def relative_time(ts: str) -> str:
    """Convert an ISO-8601 timestamp to a human-readable relative string."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(tz=dt.tzinfo or timezone.utc)
        total_seconds = (now - dt).total_seconds()
        days = int(total_seconds // 86400)
        if total_seconds < 60:
            return "just now"
        if total_seconds < 3600:
            return f"{int(total_seconds // 60)} min ago"
        if total_seconds < 86400:
            h = int(total_seconds // 3600)
            return f"{h} hour{'s' if h > 1 else ''} ago"
        if days < 7:
            return f"{days} day{'s' if days > 1 else ''} ago"
        return dt.strftime("%b %d, %I:%M %p")
    except (ValueError, OverflowError) as exc:
        logger.warning("relative_time parse error for %r: %s", ts, exc)
        return ts


def get_unread_reply_count(user_id: str) -> int:
    """Count replies the user hasn't read yet."""
    try:
        msgs = (
            supabase.table("messages")
            .select("id, reply, read_by_customer")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        return sum(1 for m in msgs if m.get("reply") and not m.get("read_by_customer", False))
    except Exception as exc:
        logger.error("get_unread_reply_count: %s", exc)
        return 0


def mark_messages_as_read(user_id: str) -> None:
    """Mark all of this user's messages as read."""
    try:
        (
            supabase.table("messages")
            .update({"read_by_customer": True})
            .eq("user_id", user_id)
            .eq("read_by_customer", False)
            .execute()
        )
    except Exception as exc:
        logger.error("mark_messages_as_read: %s", exc)


def explain_risk_with_citations(
    df: pd.DataFrame,
) -> Tuple[List[str], List[Dict[str, str]]]:
    """Return plain-language risk factors and source citations."""
    row = df.iloc[0]
    reasons: List[str] = []
    citations: List[Dict[str, str]] = []

    if row["income_to_loan_ratio"] < 0.3:
        reasons.append("📉 Low income relative to loan amount")
        citations.append({"source": "Lending Policy §2.4", "confidence": "High"})
    if row["loan_to_value_ratio"] > 0.8:
        reasons.append("🚗 Loan too high relative to car value")
        citations.append({"source": "Asset Valuation Guide", "confidence": "Medium"})
    if row["previous_defaults"] > 0:
        reasons.append("⚠️ Prior defaults on record")
        citations.append({"source": "Credit History Database", "confidence": "High"})

    if not reasons:
        reasons.append("✅ Strong applicant profile")
        citations.append({"source": "All checks passed", "confidence": "High"})

    return reasons, citations


def suggest_improvements(df: pd.DataFrame) -> List[str]:
    """Return actionable improvement suggestions."""
    row = df.iloc[0]
    suggestions: List[str] = []
    if row["income_to_loan_ratio"] < 0.3:
        suggestions.append("Increase monthly income or reduce the requested loan amount.")
    if row["loan_to_value_ratio"] > 0.8:
        suggestions.append("Provide additional collateral or reduce the loan amount.")
    return suggestions


def build_chat_html(
    messages: List[Dict[str, Any]],
    height_px: int = CHAT_HEIGHT_PX,
    show_timeline: bool = False,
) -> str:
    """
    Build a self-contained HTML chat window.
    Shared between the user Contact page and Admin Dashboard.
    """
    # Build timeline data if needed
    timeline_data: List[Dict[str, Any]] = []
    if show_timeline:
        date_groups: Dict[str, Dict[str, Any]] = {}
        for i, msg in enumerate(messages):
            try:
                dt = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                date_key = dt.strftime("%Y-%m-%d")
                display = dt.strftime("%b %d")
            except (ValueError, KeyError):
                date_key = "unknown"
                display = "Unknown"
            if date_key not in date_groups:
                date_groups[date_key] = {"display": display, "first_index": i}
        timeline_data = [
            {"date": k, "display": v["display"], "index": v["first_index"]}
            for k, v in date_groups.items()
        ]

    timeline_css = ""
    if show_timeline:
        timeline_css = """
        .chat-wrapper { display: flex; width: 100%; }
        .timeline {
            width: 40px; background: transparent; display: flex;
            flex-direction: column; align-items: center; padding: 20px 5px;
            border-left: 1px dashed #2a3748;
        }
        .timeline-dot {
            width: 8px; height: 8px; background: #4b5a6a; border-radius: 50%;
            margin: 8px 0; cursor: pointer; transition: all 0.2s; position: relative;
        }
        .timeline-dot:hover { background: #3b82f6; transform: scale(1.5); }
        .timeline-dot.active { background: #3b82f6; box-shadow: 0 0 8px #3b82f6; }
        .timeline-dot::after {
            content: attr(data-date); position: absolute; right: 20px; top: -4px;
            background: #1e2630; color: #e4e8f0; padding: 2px 8px;
            border-radius: 12px; font-size: 10px; white-space: nowrap;
            opacity: 0; pointer-events: none; transition: opacity 0.2s;
            border: 1px solid #2a3748;
        }
        .timeline-dot:hover::after { opacity: 1; }
        """

    base_css = f"""
        body {{ margin:0; background:#0b1220; font-family:'Inter',sans-serif; color:#e6edf3; }}
        .chat-messages {{
            flex:1; overflow-y:auto; height:{height_px}px;
            padding:20px 10px 20px 20px;
            scrollbar-width:thin; scrollbar-color:#3a4450 transparent;
        }}
        .chat-messages::-webkit-scrollbar {{ width:6px; }}
        .chat-messages::-webkit-scrollbar-thumb {{ background:#3a4450; border-radius:10px; }}
        .chat-bubble-row {{ display:flex; margin-bottom:12px; }}
        .chat-bubble-row.user {{ justify-content:flex-end; }}
        .chat-bubble-row.admin {{ justify-content:flex-start; }}
        .chat-bubble {{
            max-width:70%; padding:12px 16px; border-radius:18px;
            font-size:14px; line-height:1.5; word-break:break-word;
            box-shadow:0 1px 2px rgba(0,0,0,0.15);
        }}
        .user .chat-bubble {{ background:#0084ff; color:white; border-bottom-right-radius:4px; }}
        .admin .chat-bubble {{ background:#3a3b3c; color:#e4e6eb; border-bottom-left-radius:4px; }}
        .chat-timestamp {{ font-size:11px; color:#8a8d91; margin-top:4px; text-align:right; }}
        .user .chat-timestamp {{ color:#b0d4ff; }}
        .reply-badge {{
            background:#1d4ed8; color:white; border-radius:16px;
            padding:4px 12px; font-size:12px; margin-bottom:8px; display:inline-block;
        }}
        .read-receipt {{ font-size:11px; color:#8a8d91; margin-left:8px; }}
        {timeline_css}
    """

    parts = [
        f"<html><head><meta charset='UTF-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        f"<style>{base_css}</style></head><body>"
        f"<div class='chat-wrapper'>"
        f"<div class='chat-messages' id='chatMessages'>"
    ]

    for msg in messages:
        ts = relative_time(msg.get("timestamp", ""))
        safe_msg = html.escape(msg.get("message", ""))
        receipt = "✓✓ Read" if msg.get("read_by_customer") else "✓ Delivered"
        parts.append(f"""
        <div class="chat-bubble-row user" data-message-id="{msg.get('id','')}">
            <div style="display:flex;flex-direction:column;align-items:flex-end;max-width:70%">
                <div class="chat-bubble">{safe_msg}</div>
                <div style="display:flex;align-items:center">
                    <div class="chat-timestamp">{ts}</div>
                    <div class="read-receipt">{receipt}</div>
                </div>
            </div>
        </div>""")

        if msg.get("reply"):
            r_ts = relative_time(msg.get("replied_at", ""))
            safe_reply = html.escape(msg["reply"])
            parts.append(f"""
        <div class="chat-bubble-row admin">
            <div style="display:flex;flex-direction:column;max-width:70%">
                <div class="reply-badge">Reply</div>
                <div class="chat-bubble">{safe_reply}</div>
                <div class="chat-timestamp">{r_ts}</div>
            </div>
        </div>""")

    parts.append("</div>")  # close #chatMessages

    if show_timeline and timeline_data:
        parts.append('<div class="timeline" id="timeline">')
        for item in timeline_data:
            parts.append(
                f'<div class="timeline-dot" data-date="{item["display"]}" '
                f'data-index="{item["index"]}"></div>'
            )
        parts.append("</div>")
        parts.append("""
        <script>
        (function() {
            const chat = document.getElementById('chatMessages');
            const dots = document.querySelectorAll('.timeline-dot');
            const rows = chat.querySelectorAll('.chat-bubble-row');
            dots.forEach(dot => {
                dot.addEventListener('click', function() {
                    const idx = parseInt(this.dataset.index, 10);
                    if (rows[idx]) rows[idx].scrollIntoView({ behavior:'smooth', block:'start' });
                    dots.forEach(d => d.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        })();
        </script>""")

    parts.append("</div></body></html>")
    return "".join(parts)

# ==============================
# 11. LOGIN PAGE
# ==============================
def show_login_page() -> None:
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Intelligent credit evaluation for smarter lending</div>',
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
                    padding:32px;border-radius:20px;border:1px solid #1f2a36;">
        """, unsafe_allow_html=True)

        st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="small">Sign in to access your account</div>',
            unsafe_allow_html=True,
        )

        email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input(
            "Password", type="password", placeholder="••••••••", key="login_password"
        )

        if st.button("Sign In", use_container_width=True, key="signin_btn"):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Signing in..."):
                    user = authenticate(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    # ✅ Role comes from the database — never from UI input
                    st.session_state.role = user["role"]
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        st.markdown(
            '<p class="login-footer">Don\'t have an account? '
            '<a href="#">Sign up</a></p>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# 12. LOAN ANALYSIS PAGE
# ==============================
def show_loan_analysis() -> None:
    # 🔒 Only regular users may access this page
    require_role(["user"])

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Input Details")

    col1, col2 = st.columns(2)
    with col1:
        age          = st.number_input("Age", min_value=18, max_value=100, value=30)
        income       = st.number_input("Monthly Income (KES)", min_value=0, max_value=1_000_000, value=50_000, step=1_000)
        loan_amount  = st.number_input("Loan Amount (KES)", min_value=1, max_value=1_000_000, value=200_000, step=1_000)
        interest_rate= st.number_input("Interest Rate (%)", min_value=0.1, max_value=100.0, value=12.5, step=0.1)
        loan_term    = st.selectbox("Loan Term (months)", [12, 24, 36, 48, 60])
    with col2:
        car_value    = st.number_input("Car Value (KES)", min_value=1, max_value=1_000_000, value=400_000, step=1_000)
        car_age      = st.slider("Car Age (years)", 0, 50, 5)
        mileage      = st.number_input("Mileage (km)", 0, 500_000, 80_000, step=1_000)
        previous_loans    = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Key Financial Metrics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan",   f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate",   f"{interest_rate}%")
    st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("💰 Calculate Repayment"):
            r = interest_rate / 100 / 12
            monthly = (
                loan_amount / loan_term
                if r == 0
                else loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)
            )
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💳 Repayment Breakdown")
            st.write(f"**Monthly:** KES {monthly:,.2f}")
            st.write(f"**Weekly:**  KES {monthly / WEEKS_PER_MONTH:,.2f}")
            st.write(f"**Daily:**   KES {monthly / DAYS_PER_MONTH:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        if st.button("🤖 Check Loan Risk"):
            emp_map = {"salaried": 0, "self-employed": 1, "informal": 2}
            df = pd.DataFrame({
                "age":               [age],
                "monthly_income":    [income],
                "loan_amount":       [loan_amount],
                "interest_rate":     [interest_rate],
                "loan_term":         [loan_term],
                "car_value":         [car_value],
                "car_age":           [car_age],
                "mileage":           [mileage],
                "previous_loans":    [previous_loans],
                "previous_defaults": [previous_defaults],
                "employment_type":   [emp_map[employment_type]],
            })
            df["loan_to_value_ratio"]  = loan_amount / car_value
            df["income_to_loan_ratio"] = income / loan_amount

            X    = df[model.feature_names_in_]
            pred = model.predict(X)[0]
            prob: float = model.predict_proba(X)[0][1] * 100

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🧠 AI Risk Decision")
            st.write(f"**Risk Score:** {prob:.2f}%")
            st.progress(int(prob))
            if pred == 1:
                st.error("❌ High Risk — this application is likely to default.")
            else:
                st.success("✅ Low Risk — this application meets credit criteria.")

            st.subheader("📌 Risk Factors")
            reasons, citations = explain_risk_with_citations(df)
            for reason, cite in zip(reasons, citations):
                st.write(f"• {reason}  `[Source: {cite['source']}]`  🔵 Confidence: {cite['confidence']}")

            improvements = suggest_improvements(df)
            if improvements:
                st.subheader("💡 Recommendations")
                for suggestion in improvements:
                    st.info(suggestion)
            st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# 13. CONTACT PAGE (users only)
# ==============================
def show_contact_page() -> None:
    # 🔒 Only regular users may access this page
    require_role(["user"])

    st.subheader("💬 Customer Support Chat")
    user_id: str = st.session_state.user["id"]
    mark_messages_as_read(user_id)

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        st.session_state.auto_refresh = st.checkbox(
            "Auto-refresh (3s)", value=st.session_state.auto_refresh
        )

    try:
        msgs = (
            supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("id", desc=False)
            .execute()
            .data
        )
    except Exception as exc:
        logger.error("Contact page fetch: %s", exc)
        st.error("Failed to load messages. Please refresh.")
        msgs = []

    # Quick-action shortcuts
    st.markdown("**Quick Actions**")
    quick_actions = {
        "📊 Loan Status":   "What's my loan application status?",
        "💰 Payment Help":  "I need help with my payment",
        "📄 Upload Docs":   "I need to upload documents",
        "🔄 Reset Password":"I forgot my password",
    }
    for col, (label, draft) in zip(st.columns(len(quick_actions)), quick_actions.items()):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.draft_message = draft
                st.rerun()

    # Chat window
    chat_html = build_chat_html(msgs, height_px=CHAT_HEIGHT_PX, show_timeline=True)
    st.markdown('<div class="unified-chat">', unsafe_allow_html=True)
    components.html(chat_html, height=CHAT_HEIGHT_PX + 20, scrolling=False)

    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    with st.form(key="message_form", clear_on_submit=True):
        col_input, col_button = st.columns([5, 1])
        with col_input:
            msg_text = st.text_input(
                "Message",
                value=st.session_state.draft_message,
                placeholder="Type your message...",
                label_visibility="collapsed",
                key="chat_input",
            )
        with col_button:
            submitted = st.form_submit_button("📤 Send", use_container_width=True)

        if submitted:
            if msg_text.strip():
                try:
                    supabase.table("messages").insert({
                        "user_id":          user_id,
                        "name":             st.session_state.user["username"],
                        "email":            st.session_state.user["email"],
                        "message":          msg_text.strip(),
                        "status":           "sent",
                        "timestamp":        datetime.now(tz=timezone.utc).isoformat(),
                        "read_by_customer": False,
                        "delivered":        True,
                    }).execute()
                    st.session_state.draft_message = ""
                    st.success("Message sent!")
                    time.sleep(0.4)
                    st.rerun()
                except Exception as exc:
                    logger.error("Message insert: %s", exc)
                    st.error("Failed to send your message. Please try again.")
            else:
                st.session_state.draft_message = msg_text

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.auto_refresh:
        time.sleep(AUTO_REFRESH_SECONDS)
        st.rerun()

# ==============================
# 14. ADMIN DASHBOARD
# ==============================
def show_admin_dashboard() -> None:
    # 🔒 Only admins may access this page
    require_role(["admin"])

    st.subheader("📊 Admin Control Panel")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        st.session_state.auto_refresh = st.checkbox(
            "Auto-refresh (3s)", value=st.session_state.auto_refresh, key="admin_auto"
        )

    try:
        data: List[Dict[str, Any]] = (
            supabase.table("messages")
            .select("*")
            .order("timestamp", desc=False)
            .execute()
            .data
        )
    except Exception as exc:
        logger.error("Admin dashboard fetch: %s", exc)
        st.error("Failed to fetch messages.")
        data = []

    if not data:
        st.info("No messages yet.")
        return

    st.markdown("### 💬 Customer Conversations")
    users_df = pd.DataFrame(data)
    unique_users: List[Dict[str, Any]] = (
        users_df[["user_id", "name", "email"]]
        .drop_duplicates(subset=["user_id"])
        .to_dict("records")
    )

    col_users, col_chat = st.columns([1, 2])

    with col_users:
        st.markdown("**Conversations**")
        for usr in unique_users:
            if st.button(
                f"👤 {usr['name']} ({usr['email']})",
                key=f"user_{usr['user_id']}",
            ):
                st.session_state.selected_user_id = usr["user_id"]
                st.rerun()

    with col_chat:
        if st.session_state.selected_user_id is None and unique_users:
            st.session_state.selected_user_id = unique_users[0]["user_id"]

        if st.session_state.selected_user_id:
            user_msgs = [
                m for m in data
                if m["user_id"] == st.session_state.selected_user_id
            ]
            selected_name = next(
                (u["name"] for u in unique_users
                 if u["user_id"] == st.session_state.selected_user_id),
                "User",
            )
            st.markdown(f"#### Chat with {selected_name}")

            chat_html = build_chat_html(user_msgs, height_px=ADMIN_CHAT_HEIGHT_PX)
            components.html(chat_html, height=ADMIN_CHAT_HEIGHT_PX + 20, scrolling=True)

            unreplied = [m for m in user_msgs if not m.get("reply")]
            with st.form(
                key=f"reply_form_{st.session_state.selected_user_id}",
                clear_on_submit=True,
            ):
                col_input, col_btn = st.columns([5, 1])
                with col_input:
                    reply_text = st.text_input(
                        "", placeholder="Write a reply...", label_visibility="collapsed"
                    )
                with col_btn:
                    submitted = st.form_submit_button("📤 Send")

                if submitted:
                    if not reply_text.strip():
                        st.warning("Reply cannot be empty.")
                    elif not unreplied:
                        st.warning("All messages from this user have already been replied to.")
                    else:
                        try:
                            supabase.table("messages").update({
                                "reply":      reply_text.strip(),
                                "replied_at": datetime.now(tz=timezone.utc).isoformat(),
                                "status":     "replied",
                            }).eq("id", unreplied[-1]["id"]).execute()
                            st.success("Reply sent!")
                            st.rerun()
                        except Exception as exc:
                            logger.error("Reply update: %s", exc)
                            st.error("Failed to send reply. Please try again.")
        else:
            st.info("Select a user from the left to view their conversation.")

    st.markdown("---")
    st.metric("Total Messages", len(data))

    if not users_df.empty:
        users_df["timestamp"] = pd.to_datetime(users_df["timestamp"], errors="coerce", utc=True)
        daily = (
            users_df.groupby(users_df["timestamp"].dt.date)
            .size()
            .reset_index(name="count")
        )
        if not daily.empty:
            fig = px.line(
                daily,
                x="timestamp",
                y="count",
                title="Messages Over Time",
                labels={"timestamp": "Date", "count": "Messages"},
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e6edf3",
            )
            st.plotly_chart(fig, use_container_width=True)

    if st.session_state.auto_refresh:
        time.sleep(AUTO_REFRESH_SECONDS)
        st.rerun()

# ==============================
# 15. MAIN APP (post-login)
# ==============================
def show_main_app() -> None:
    role = st.session_state.get("role")

    # ✅ Navigation is built entirely from the DB role — never from URL or user input
    if role == "user":
        menu = ["📊 Loan Analysis", "💬 Contact"]
    elif role == "admin":
        menu = ["⚙️ Admin Dashboard"]
    else:
        # Unknown or missing role — force logout immediately
        st.error("⛔ Invalid session. Please log in again.")
        logout()
        return

    st.sidebar.markdown("## 🧭 Navigation")
    page = st.sidebar.radio("", menu, label_visibility="collapsed")
    st.sidebar.markdown("---")

    # User info + role badge in sidebar
    user     = st.session_state.user
    username = user.get("username", "User")

    if role == "user":
        unread = get_unread_reply_count(user["id"])
        badge  = f" 🔴 {unread}" if unread > 0 else ""
        st.sidebar.markdown(f"👤 **{username}**{badge}")
        st.sidebar.markdown(
            '<span class="role-badge user">User</span>', unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(f"👑 **{username}**")
        st.sidebar.markdown(
            '<span class="role-badge admin">Admin</span>', unsafe_allow_html=True
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    st.markdown(
        "<h1 style='text-align:center;color:#3b82f6'>AI Loan Risk Platform</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>Real-time credit risk evaluation powered by machine learning</div>",
        unsafe_allow_html=True,
    )

    # Page routing
    if "Loan Analysis" in page:
        show_loan_analysis()
    elif "Contact" in page:
        show_contact_page()
    elif "Admin Dashboard" in page:
        show_admin_dashboard()

# ==============================
# 16. ENTRY POINT
# ==============================
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
