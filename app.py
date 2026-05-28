# ==============================
# app.py
# ==============================

import streamlit as st
import pickle

from supabase import create_client, Client

from styles.theme import apply_theme

from auth.login import (
    show_login_page,
    logout
)

from views.about import show_about_page
from views.loan_analysis import show_loan_analysis
from views.contact import show_contact
from views.admin_dashboard import show_admin_dashboard
from views.car_marketplace import show_car_marketplace
from views.car_upload import show_car_management

from services.supabase_service import (
    get_unread_reply_count,
    get_user_role
)

from config.settings import validate_secrets


# ─────────────────────────────
# PAGE CONFIG
# ─────────────────────────────
st.set_page_config(
    page_title="AI Loan Risk Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()

validate_secrets()


# ─────────────────────────────
# SUPABASE
# ─────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ─────────────────────────────
# SESSION DEFAULTS
# ─────────────────────────────
defaults = {
    "authenticated": False,
    "user": None,
    "role": None,
    "seen_notified": set(),
    "selected_user_id": None,
    "selected_car_id": None,
    "editing_car_id": None,
    "confirm_delete_id": None,
    "auto_refresh": False,
    "draft_message": "",
    "risk_result": None,
    "repayment_result": None,
    "show_signup": False,
    "pending_confirmation_email": None,
    "last_msg_count": 0,
    "admin_last_count": 0,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ─────────────────────────────
# LOAD MODEL
# ─────────────────────────────
@st.cache_resource
def load_model():

    return pickle.load(
        open("loan_model.pkl", "rb")
    )


model = load_model()


# ─────────────────────────────
# RESTORE GOOGLE SESSION
# ─────────────────────────────
try:

    session = supabase.auth.get_session()

    if session and session.session:

        user_response = supabase.auth.get_user()

        if user_response and user_response.user:

            u = user_response.user

            st.session_state.authenticated = True

            st.session_state.user = {
                "id": u.id,
                "email": u.email,
                "username": u.email
            }

            st.session_state.role = get_user_role(
                supabase,
                u.id
            )

except Exception:
    pass


# ─────────────────────────────
# NOT LOGGED IN
# ─────────────────────────────
if not st.session_state.authenticated:

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display:none !important;
        }

        [data-testid="collapsedControl"] {
            display:none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    show_login_page(supabase)


# ─────────────────────────────
# LOGGED IN
# ─────────────────────────────
else:

    with st.sidebar:

        st.markdown(
            """
            <p style="
                font-size:20px;
                font-weight:800;
                color:#60A5FA;
                margin-bottom:4px;
            ">
                Navigation
            </p>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

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

        page = st.radio(
            "Navigation",
            menu,
            label_visibility="collapsed"
        )

        st.markdown("---")

        if st.session_state.role == "user":

            unread = get_unread_reply_count(
                supabase,
                st.session_state.user["id"]
            )

            badge = (
                f" ({unread})"
                if unread > 0 else ""
            )

            st.markdown(
                f"""
                👤 **{
                    st.session_state.user["email"]
                }**{badge}
                """
            )

        else:

            st.markdown(
                f"""
                👑 **Admin:** {
                    st.session_state.user["email"]
                }
                """
            )

        st.markdown(
            f"""
            Role: **{
                (st.session_state.role or "user").upper()
            }**
            """
        )

        st.markdown("---")

        if st.button(
            "Logout",
            use_container_width=True
        ):

            logout(supabase)

    # ─────────────────────────
    # ROUTING
    # ─────────────────────────
    if page == "About":

        show_about_page()

    elif page == "Car Marketplace":

        st.markdown(
            """
            <div class="page-title">
                Car Marketplace
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="page-subtitle">
                Browse verified vehicle listings
            </div>
            """,
            unsafe_allow_html=True
        )

        show_car_marketplace(supabase)

    elif page == "Car Management":

        st.markdown(
            """
            <div class="page-title">
                Car Management
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="page-subtitle">
                Add and manage car listings
            </div>
            """,
            unsafe_allow_html=True
        )

        show_car_management(supabase)

    else:

        st.markdown(
            """
            <div class="page-title">
                AI Loan Risk Platform
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="page-subtitle">
                AI-powered credit risk evaluation
            </div>
            """,
            unsafe_allow_html=True
        )

        if page == "Loan Analysis":

            show_loan_analysis(
                model,
                supabase
            )

        elif page == "Contact":

            show_contact(supabase)

        elif page == "Admin Dashboard":

            show_admin_dashboard(supabase)
