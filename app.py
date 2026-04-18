# ==============================
# 1. IMPORTS
# ==============================
import pickle
import html
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

import bcrypt
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
# 3. CONFIG
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

section[data-testid="stSidebar"] .stRadio > div {
    gap: 10px;
}

section[data-testid="stSidebar"] label {
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    white-space: nowrap !important;
    width: 100% !important;
    box-sizing: border-box;
}

section[data-testid="stSidebar"] label:hover {
    background: #1a2330;
}

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

.login-card div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 12px;
    margin-bottom: 24px;
    justify-content: center;
}

.login-card div[role="radiogroup"] label {
    flex: 1;
    min-width: 120px;
    padding: 12px 16px;
    background: #1a222c;
    border: 1px solid #2a3748;
    border-radius: 12px;
    color: #8a94a3;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    margin: 0 !important;
    white-space: nowrap;
}

.login-card div[role="radiogroup"] label[data-selected="true"] {
    background: #1e3a5f;
    border-color: #3b82f6;
    color: white;
}

.login-card div[role="radiogroup"] input {
    display: none !important;
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

.login-footer a {
    color: #3b82f6;
    text-decoration: none;
}

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

.chat-input-container .stForm {
    margin-bottom: 0;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 6. SUPABASE CLIENT
# ==============================
@st.cache_resource
def get_supabase_client() -> Client:
    """Cached Supabase client — created once per server process."""
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = get_supabase_client()

# ==============================
# 7. SESSION STATE
# ==============================
_SESSION_DEFAULTS: Dict[str, Any] = {
    "authenticated": False,
    "user": None,
    "role": None,           # "user" | "admin"
    "seen_notified": set(),
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
# 9. HELPER FUNCTIONS
# ==============================

def _hash_encode(text: str) -> bytes:
    """Return UTF-8 encoded bytes for bcrypt operations."""
    return text.encode("utf-8")


def check_admin_password(plain: str) -> bool:
    stored_hash: str = st.secrets["ADMIN_PASSWORD_HASH"]
    return bcrypt.checkpw(_hash_encode(plain), _hash_encode(stored_hash))


def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        res = supabase.table("users").select("*").eq("email", email).single().execute()
        if res.data and bcrypt.checkpw(_hash_encode(password), _hash_encode(res.data["password"])):
            return res.data
    except Exception as exc:
        logger.error("login_user failed: %s", exc)
        st.error("Login failed. Please try again.")
    return None


def login_admin(username: str, password: str) -> bool:
    return username == st.secrets["ADMIN_USERNAME"] and check_admin_password(password)


def relative_time(ts: str) -> str:
    """Convert an ISO-8601 timestamp string to a human-readable relative time."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Ensure both datetimes share the same timezone awareness
        now = datetime.now(tz=dt.tzinfo or timezone.utc)
        diff = now - dt
        total_seconds = diff.total_seconds()
        if total_seconds < 60:
            return "just now"
        if total_seconds < 3600:
            mins = int(total_seconds // 60)
            return f"{mins} min ago"
        if total_seconds < 86400:
            hours = int(total_seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        if diff.days < 7:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        return dt.strftime("%b %d, %I:%M %p")
    except (ValueError, OverflowError) as exc:
        logger.warning("relative_time parse error for %r: %s", ts, exc)
        return ts


def get_unread_reply_count(user_id: int) -> int:
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


def mark_messages_as_read(user_id: int) -> None:
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
        reasons.append("📉 Low income vs loan amount")
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
    """Return actionable improvement suggestions for the applicant."""
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

    Eliminates the duplicated HTML-generation logic between the user
    Contact page and the Admin Dashboard.
    """
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

    timeline_styles = ""
    if show_timeline:
        timeline_styles = """
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
            background: #1e2630; color: #e4e8f0; padding: 2px 8px; border-radius: 12px;
            font-size: 10px; white-space: nowrap; opacity: 0; pointer-events: none;
            transition: opacity 0.2s; border: 1px solid #2a3748;
        }
        .timeline-dot:hover::after { opacity: 1; }
        """

    # Base styles shared between both views
    base_styles = f"""
        body {{ margin: 0; background: #0b1220; font-family: 'Inter', sans-serif; color: #e6edf3; }}
        .chat-messages {{
            flex: 1; overflow-y: auto; height: {height_px}px;
            padding: 20px 10px 20px 20px;
            scrollbar-width: thin; scrollbar-color: #3a4450 transparent;
        }}
        .chat-messages::-webkit-scrollbar {{ width: 6px; }}
        .chat-messages::-webkit-scrollbar-thumb {{ background: #3a4450; border-radius: 10px; }}
        .chat-bubble-row {{ display: flex; margin-bottom: 12px; }}
        .chat-bubble-row.user {{ justify-content: flex-end; }}
        .chat-bubble-row.admin {{ justify-content: flex-start; }}
        .chat-bubble {{
            max-width: 70%; padding: 12px 16px; border-radius: 18px;
            font-size: 14px; line-height: 1.5; word-break: break-word;
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }}
        .user .chat-bubble {{ background: #0084ff; color: white; border-bottom-right-radius: 4px; }}
        .admin .chat-bubble {{ background: #3a3b3c; color: #e4e6eb; border-bottom-left-radius: 4px; }}
        .chat-timestamp {{ font-size: 11px; color: #8a8d91; margin-top: 4px; text-align: right; }}
        .user .chat-timestamp {{ color: #b0d4ff; }}
        .reply-badge {{
            background: #1d4ed8; color: white; border-radius: 16px;
            padding: 4px 12px; font-size: 12px; margin-bottom: 8px; display: inline-block;
        }}
        .read-receipt {{ font-size: 11px; color: #8a8d91; margin-left: 8px; }}
        {timeline_styles}
    """

    html_parts = [
        f"<html><head><meta charset='UTF-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        f"<style>{base_styles}</style></head><body>"
        f"<div class='chat-wrapper'>"
        f"<div class='chat-messages' id='chatMessages'>"
    ]

    for msg in messages:
        timestamp = relative_time(msg.get("timestamp", ""))
        safe_message = html.escape(msg.get("message", ""))
        read_status = "✓✓ Read" if msg.get("read_by_customer") else "✓ Delivered"
        html_parts.append(f"""
        <div class="chat-bubble-row user" data-message-id="{msg.get('id','')}">
            <div style="display:flex;flex-direction:column;align-items:flex-end;max-width:70%">
                <div class="chat-bubble">{safe_message}</div>
                <div style="display:flex;align-items:center">
                    <div class="chat-timestamp">{timestamp}</div>
                    <div class="read-receipt">{read_status}</div>
                </div>
            </div>
        </div>""")

        if msg.get("reply"):
            reply_time = relative_time(msg.get("replied_at", ""))
            safe_reply = html.escape(msg["reply"])
            html_parts.append(f"""
        <div class="chat-bubble-row admin">
            <div style="display:flex;flex-direction:column;max-width:70%">
                <div class="reply-badge">Reply</div>
                <div class="chat-bubble">{safe_reply}</div>
                <div class="chat-timestamp">{reply_time}</div>
            </div>
        </div>""")

    html_parts.append("</div>")  # close #chatMessages

    # Optional timeline strip
    if show_timeline and timeline_data:
        html_parts.append('<div class="timeline" id="timeline">')
        for item in timeline_data:
            html_parts.append(
                f'<div class="timeline-dot" data-date="{item["display"]}" '
                f'data-index="{item["index"]}"></div>'
            )
        html_parts.append("</div>")
        html_parts.append("""
        <script>
        (function() {
            const chatMessages = document.getElementById('chatMessages');
            const dots = document.querySelectorAll('.timeline-dot');
            const rows = chatMessages.querySelectorAll('.chat-bubble-row');
            dots.forEach(dot => {
                dot.addEventListener('click', function() {
                    const idx = parseInt(this.dataset.index, 10);
                    if (rows[idx]) rows[idx].scrollIntoView({ behavior: 'smooth', block: 'start' });
                    dots.forEach(d => d.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        })();
        </script>""")

    html_parts.append("</div></body></html>")  # close .chat-wrapper + body
    return "".join(html_parts)


def logout() -> None:
    for key in _SESSION_DEFAULTS:
        st.session_state[key] = _SESSION_DEFAULTS[key]
    st.rerun()

# ==============================
# 10. LOGIN PAGE
# ==============================
def show_login_page() -> None:
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Intelligent credit evaluation for smarter lending</div>',
        unsafe_allow_html=True,
    )

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="small">Sign in to access your account</div>',
            unsafe_allow_html=True,
        )

        role = st.radio("", ["User", "Administrator"], horizontal=True, label_visibility="collapsed")

        if role == "User":
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            if st.button("Sign In", use_container_width=True, key="signin_user"):
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user_data = login_user(email, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user = user_data
                        st.session_state.role = "user"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            st.markdown(
                '<p class="login-footer">Don\'t have an account? <a href="#">Sign up</a></p>',
                unsafe_allow_html=True,
            )
        else:
            username = st.text_input("Admin Username", placeholder="admin", key="admin_user")
            password = st.text_input("Admin Password", type="password", placeholder="••••••••", key="admin_pass")
            if st.button("Sign In as Admin", use_container_width=True, key="signin_admin"):
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif login_admin(username, password):
                    st.session_state.authenticated = True
                    st.session_state.user = {"username": username, "role": "admin"}
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin credentials.")

        st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# 11. LOAN ANALYSIS PAGE
# ==============================
def show_loan_analysis() -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Input Details")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
        income = st.number_input("Monthly Income (KES)", min_value=0, max_value=1_000_000, value=50_000, step=1_000)
        loan_amount = st.number_input("Loan Amount (KES)", min_value=1, max_value=1_000_000, value=200_000, step=1_000)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.1, max_value=100.0, value=12.5, step=0.1)
        loan_term = st.selectbox("Loan Term (months)", [12, 24, 36, 48, 60])
    with col2:
        car_value = st.number_input("Car Value (KES)", min_value=1, max_value=1_000_000, value=400_000, step=1_000)
        car_age = st.slider("Car Age (years)", 0, 50, 5)
        mileage = st.number_input("Mileage (km)", 0, 500_000, 80_000, step=1_000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Key Financial Metrics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan", f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate", f"{interest_rate}%")
    st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("💰 Calculate Repayment"):
            r = interest_rate / 100 / 12
            if r == 0:
                monthly = loan_amount / loan_term
            else:
                monthly = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💳 Repayment Breakdown")
            st.write(f"**Monthly:** KES {monthly:,.2f}")
            st.write(f"**Weekly:** KES {monthly / WEEKS_PER_MONTH:,.2f}")
            st.write(f"**Daily:** KES {monthly / DAYS_PER_MONTH:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        if st.button("🤖 Check Loan Risk"):
            emp_map = {"salaried": 0, "self-employed": 1, "informal": 2}
            df = pd.DataFrame({
                "age": [age],
                "monthly_income": [income],
                "loan_amount": [loan_amount],
                "interest_rate": [interest_rate],
                "loan_term": [loan_term],
                "car_value": [car_value],
                "car_age": [car_age],
                "mileage": [mileage],
                "previous_loans": [previous_loans],
                "previous_defaults": [previous_defaults],
                "employment_type": [emp_map[employment_type]],
            })
            # Derived features — car_value and loan_amount validated > 0 above
            df["loan_to_value_ratio"] = loan_amount / car_value
            df["income_to_loan_ratio"] = income / loan_amount

            X = df[model.feature_names_in_]
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
# 12. CONTACT (USER) PAGE
# ==============================
def show_contact_page() -> None:
    st.subheader("💬 Customer Support Chat")
    user_id: int = st.session_state.user["id"]
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
        "📊 Loan Status": "What's my loan application status?",
        "💰 Payment Help": "I need help with my payment",
        "📄 Upload Docs": "I need to upload documents",
        "🔄 Reset Password": "I forgot my password",
    }
    action_cols = st.columns(len(quick_actions))
    for col, (label, draft) in zip(action_cols, quick_actions.items()):
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
                        "user_id": user_id,
                        "name": st.session_state.user["username"],
                        "email": st.session_state.user["email"],
                        "message": msg_text.strip(),
                        "status": "sent",
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        "read_by_customer": False,
                        "delivered": True,
                    }).execute()
                    st.session_state.draft_message = ""
                    st.success("Message sent!")
                    time.sleep(0.4)  # Brief pause so the success toast is visible
                    st.rerun()
                except Exception as exc:
                    logger.error("Message insert: %s", exc)
                    st.error("Failed to send your message. Please try again.")
            else:
                st.session_state.draft_message = msg_text  # preserve draft

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.auto_refresh:
        time.sleep(AUTO_REFRESH_SECONDS)
        st.rerun()

# ==============================
# 13. ADMIN DASHBOARD
# ==============================
def show_admin_dashboard() -> None:
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
        # Default to first user if none selected
        if st.session_state.selected_user_id is None and unique_users:
            st.session_state.selected_user_id = unique_users[0]["user_id"]

        if st.session_state.selected_user_id:
            user_msgs = [m for m in data if m["user_id"] == st.session_state.selected_user_id]
            selected_name = next(
                (u["name"] for u in unique_users if u["user_id"] == st.session_state.selected_user_id),
                "User",
            )
            st.markdown(f"#### Chat with {selected_name}")

            chat_html = build_chat_html(user_msgs, height_px=ADMIN_CHAT_HEIGHT_PX)
            components.html(chat_html, height=ADMIN_CHAT_HEIGHT_PX + 20, scrolling=True)

            # Reply form — targets the most-recent unreplied message
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
                        msg_to_reply = unreplied[-1]
                        try:
                            supabase.table("messages").update({
                                "reply": reply_text.strip(),
                                "replied_at": datetime.now(tz=timezone.utc).isoformat(),
                                "status": "replied",
                            }).eq("id", msg_to_reply["id"]).execute()
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
# 14. MAIN APP (post-login)
# ==============================
def show_main_app() -> None:
    st.sidebar.markdown("## 🧭 Navigation")

    if st.session_state.role == "user":
        menu = ["📊 Loan Analysis", "💬 Contact"]
    else:
        menu = ["⚙️ Admin Dashboard"]

    page = st.sidebar.radio("", menu, label_visibility="collapsed")
    st.sidebar.markdown("---")

    # User info in sidebar
    if st.session_state.role == "user":
        unread = get_unread_reply_count(st.session_state.user["id"])
        name = st.session_state.user.get("username", "User")
        badge = f" 🔴 {unread}" if unread > 0 else ""
        st.sidebar.markdown(f"👤 **{name}**{badge}")
    else:
        st.sidebar.markdown(f"👑 **Admin: {st.session_state.user['username']}**")

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

    # Route to the correct page
    if "Loan Analysis" in page:
        show_loan_analysis()
    elif "Contact" in page:
        show_contact_page()
    elif "Admin Dashboard" in page:
        show_admin_dashboard()

# ==============================
# 15. ENTRY POINT
# ==============================
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
