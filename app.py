# ==============================
# app.py — Entry point only
# ==============================
import streamlit as st
import pickle
from supabase import create_client, Client
from styles.theme import apply_theme
from auth.login import show_login_page, logout
from pages.about import show_about_page
from pages.loan_analysis import show_loan_analysis
from pages.contact import show_contact
from pages.admin_dashboard import show_admin_dashboard
from services.supabase_service import get_unread_reply_count

# ── Config ──
st.set_page_config(page_title="AI Loan Risk System", layout="wide")
apply_theme()

# ── Supabase ──
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Restore session on every rerun ──
if st.session_state.get("access_token") and st.session_state.get("refresh_token"):
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
    except Exception:
        pass

# ── Session state defaults ──
defaults = {
    "authenticated": False, "user": None, "role": None,
    "access_token": None, "refresh_token": None,
    "seen_notified": set(), "selected_user_id": None,
    "auto_refresh": False, "draft_message": "",
    "risk_result": None, "repayment_result": None,
    "show_signup": False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ── ML Model ──
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ── Routing ──
if not st.session_state.authenticated:
    show_login_page(supabase)
else:
    # Sidebar
    st.sidebar.markdown("## 🧭 Navigation")
    menu = ["📊 Loan Analysis", "💬 Contact", "⚙️ Admin Dashboard", "ℹ️ About"] \
        if st.session_state.role == "admin" \
        else ["📊 Loan Analysis", "💬 Contact", "ℹ️ About"]

    page = st.sidebar.radio("", menu)
    st.sidebar.markdown("---")

    if st.session_state.role == "user":
        unread = get_unread_reply_count(supabase, st.session_state.user["id"])
        display_name = st.session_state.user["email"]
        st.sidebar.markdown(f"👤 **{display_name}**" + (f" 🔴 {unread}" if unread > 0 else ""))
    else:
        safe_name = st.session_state.user.get("username", st.session_state.user.get("email"))
        st.sidebar.markdown(f"👑 **Admin: {safe_name}**")

    st.sidebar.markdown(f"Role: **{(st.session_state.role or 'user').upper()}**")
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    # Page routing
    if "About" in page:
        show_about_page()
    else:
        st.markdown("<h1 style='text-align:center;color:#F0F4F8'>AI Loan Risk Platform</h1>", unsafe_allow_html=True)
        st.markdown("<div class='app-subtitle'>Real-time credit risk evaluation powered by machine learning</div>", unsafe_allow_html=True)

        if "Loan Analysis" in page:
            show_loan_analysis(model)
        elif "Contact" in page:
            show_contact(supabase)
        elif "Admin Dashboard" in page:
            show_admin_dashboard(supabase)
