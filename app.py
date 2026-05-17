# ==============================
# app.py — Entry point only
# ==============================
import streamlit as st
import pickle
from supabase import create_client, Client
from styles.theme import apply_theme
from auth.login import show_login_page, logout
from views.about import show_about_page
from views.loan_analysis import show_loan_analysis
from views.contact import show_contact
from views.admin_dashboard import show_admin_dashboard
from views.car_marketplace import show_car_marketplace
from views.car_upload import show_car_management
from services.supabase_service import get_unread_reply_count
from config.settings import validate_secrets

# ── Config ──
st.set_page_config(
    page_title="AI Loan Risk System",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_theme()
validate_secrets()

# ── Supabase ──
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Restore session on every rerun ──
if st.session_state.get("access_token") and \
        st.session_state.get("refresh_token"):
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
    except Exception:
        pass

# ── Session state defaults ──
defaults = {
    "authenticated":              False,
    "user":                       None,
    "role":                       None,
    "access_token":               None,
    "refresh_token":              None,
    "seen_notified":              set(),
    "selected_user_id":           None,
    "selected_car_id":            None,
    "editing_car_id":             None,
    "confirm_delete_id":          None,
    "auto_refresh":               False,
    "draft_message":              "",
    "risk_result":                None,
    "repayment_result":           None,
    "show_signup":                False,
    "pending_confirmation_email": None,
    "last_msg_count":             0,
    "admin_last_count":           0,
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
# NOT LOGGED IN
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
# LOGGED IN
# ══════════════════════════════
else:
    with st.sidebar:
        st.markdown(
            '<p style="font-size:20px; font-weight:800; color:#60A5FA; '
            'text-shadow:0 2px 4px rgba(0,0,0,0.5); margin-bottom:4px;">'
            'Navigation</p>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<hr style="border-color:#1f2a36; margin-top:0;">',
            unsafe_allow_html=True
        )

        if st.session_state.role == "admin":
            menu = [
                "Loan Analysis",
                "Car Marketplace",
                "Car Management",
                "Contact",
                "Admin Dashboard",
                "About"
            ]
        else:
            menu = [
                "Loan Analysis",
                "Car Marketplace",
                "Contact",
                "About"
            ]

        # REPLACED: Added a proper label "Navigation Menu"
        page = st.radio("Navigation Menu", menu, label_visibility="collapsed")

        st.markdown(
            '<hr style="border-color:#1f2a36;">',
            unsafe_allow_html=True
        )

        if st.session_state.role == "user":
            unread = get_unread_reply_count(
                supabase, st.session_state.user["id"]
            )
            display_name = st.session_state.user["email"]
            badge = (
                f' <span style="background:#ef4444; color:white; '
                f'border-radius:50%; padding:1px 7px; '
                f'font-size:11px;">{unread}</span>'
                if unread > 0 else ""
            )
            st.markdown(
                f'<p style="color:#F0F4F8;">👤 <b>{display_name}</b>'
                f'{badge}</p>',
                unsafe_allow_html=True
            )
        else:
            safe_name = st.session_state.user.get(
                "username", st.session_state.user.get("email")
            )
            st.markdown(
                f'<p style="color:#F0F4F8;">👑 <b>Admin:</b> '
                f'{safe_name}</p>',
                unsafe_allow_html=True
            )

        role_label = (st.session_state.role or "user").upper()
        st.markdown(
            f'<p style="color:#94A3B8; font-size:13px;">'
            f'Role: <b>{role_label}</b></p>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<hr style="border-color:#1f2a36;">',
            unsafe_allow_html=True
        )

        if st.button("Logout", use_container_width=True):
            logout(supabase)

    # ── Page routing ──
    if page == "About":
        show_about_page()

    elif page == "Car Marketplace":
        st.markdown(
            '<div class="page-title">Car Marketplace</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="page-subtitle">Browse verified vehicle listings '
            'with AI-powered valuations</div>',
            unsafe_allow_html=True
        )
        show_car_marketplace(supabase)

    elif page == "Car Management":
        st.markdown(
            '<div class="page-title">Car Management</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="page-subtitle">Add, edit and manage '
            'car listings</div>',
            unsafe_allow_html=True
        )
        show_car_management(supabase)

    else:
        st.markdown(
            '<div class="page-title">AI Loan Risk Platform</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="page-subtitle">Real-time credit risk evaluation '
            'powered by machine learning</div>',
            unsafe_allow_html=True
        )
        if page == "Loan Analysis":
            show_loan_analysis(model, supabase)
        elif page == "Contact":
            show_contact(supabase)
        elif page == "Admin Dashboard":
            show_admin_dashboard(supabase)
