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
from config.settings import validate_secrets          # ← NEW import

# ── Config ──
st.set_page_config(
    page_title="AI Loan Risk System",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_theme()
validate_secrets()                                   # ← NEW call

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

# ══════════════════════════════
# NOT LOGGED IN — hide sidebar completely
# ══════════════════════════════
if not st.session_state.authenticated:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    show_login_page(supabase)

# ══════════════════════════════
# LOGGED IN — show sidebar + pages
# ══════════════════════════════
else:
    # Auto-expand sidebar via JS after login
    st.markdown("""
    <script>
    const sidebar = window.parent.document.querySelector('[data-testid="collapsedControl"]');
    if (sidebar) sidebar.click();
    </script>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            '<p style="font-size:20px;font-weight:800;color:#60A5FA;'
            'text-shadow:0 2px 4px rgba(0,0,0,0.5);margin-bottom:4px;">Navigation</p>',
            unsafe_allow_html=True
        )
        st.markdown('<hr style="border-color:#2563eb;margin-top:0;">', unsafe_allow_html=True)

        if st.session_state.role == "admin":
            menu = ["Loan Analysis", "Contact", "Admin Dashboard", "About"]
        else:
            menu = ["Loan Analysis", "Contact", "About"]

        page = st.radio("", menu, label_visibility="collapsed")

        st.markdown('<hr style="border-color:#2563eb;">', unsafe_allow_html=True)

        if st.session_state.role == "user":
            unread = get_unread_reply_count(supabase, st.session_state.user["id"])
            display_name = st.session_state.user["email"]
            badge = f' <span style="background:#ef4444;color:white;border-radius:50%;padding:1px 7px;font-size:11px;">{unread}</span>' if unread > 0 else ""
            st.markdown(f'<p style="color:#F0F4F8;">👤 <b>{display_name}</b>{badge}</p>', unsafe_allow_html=True)
        else:
            safe_name = st.session_state.user.get("username", st.session_state.user.get("email"))
            st.markdown(f'<p style="color:#F0F4F8;">👑 <b>Admin:</b> {safe_name}</p>', unsafe_allow_html=True)

        role_label = (st.session_state.role or "user").upper()
        st.markdown(f'<p style="color:#94A3B8;font-size:13px;">Role: <b>{role_label}</b></p>', unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#2563eb;">', unsafe_allow_html=True)

        if st.button("Logout", use_container_width=True):
            logout()

    # ── Page routing ──
    if page == "About":
        show_about_page()
    else:
        st.markdown('<div class="page-title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Real-time credit risk evaluation powered by machine learning</div>', unsafe_allow_html=True)

        if page == "Loan Analysis":
            show_loan_analysis(model)
        elif page == "Contact":
            show_contact(supabase)
        elif page == "Admin Dashboard":
            show_admin_dashboard(supabase)
