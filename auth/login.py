# ==============================
# auth/login.py
# ==============================
import streamlit as st
from services.supabase_service import login_user, signup_user, get_user_role
from utils.helpers import sanitise_email, sanitise_password


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.rerun()


def show_login_page(supabase):
    # Hide sidebar completely on login page
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Gradient 3D Blue Title
    st.markdown("""
    <div style="
        text-align: center;
        font-size: 52px;
        font-weight: 800;
        background: linear-gradient(180deg, #93C5FD 0%, #3B82F6 45%, #1D4ED8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.6));
        letter-spacing: -1px;
        line-height: 1.1;
        margin-top: 40px;
        margin-bottom: 10px;
    ">AI Loan Risk Platform</div>
    <div style="
        text-align: center;
        color: #94A3B8;
        font-size: 16px;
        margin-bottom: 40px;
    ">Intelligent credit evaluation for smarter lending</div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #111827, #0b1220);
            border: 1px solid #1f2a36;
            border-radius: 20px;
            padding: 36px 32px 24px 32px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        ">
        """, unsafe_allow_html=True)

        # ── LOGIN FORM ──
        if not st.session_state.show_signup:
            st.markdown("""
            <div style="text-align:center; font-size:22px; font-weight:700;
                color:#F0F4F8; margin-bottom:4px;">Welcome back</div>
            <div style="text-align:center; color:#94A3B8; font-size:14px;
                margin-bottom:24px;">Sign in to access your account</div>
            """, unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                submitted = st.form_submit_button(
                    "Login", use_container_width=True
                )
                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        try:
                            email = sanitise_email(email)
                            sanitise_password(password)
                            user_data = login_user(supabase, email, password)
                            if user_data:
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id": user_data["id"],
                                    "email": user_data["email"],
                                    "username": email
                                }
                                st.session_state.access_token = user_data.get("access_token")
                                st.session_state.refresh_token = user_data.get("refresh_token")
                                st.session_state.role = get_user_role(
                                    supabase, st.session_state.user["id"]
                                )
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")
                        except ValueError as e:
                            st.error(str(e))

            if st.button("Don't have an account? Sign up →", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

        # ── SIGNUP FORM ──
        else:
            st.markdown("""
            <div style="text-align:center; font-size:22px; font-weight:700;
                color:#F0F4F8; margin-bottom:4px;">Create Account</div>
            <div style="text-align:center; color:#94A3B8; font-size:14px;
                margin-bottom:24px;">Sign up for a new account</div>
            """, unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                new_email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input(
                    "Password", type="password", placeholder="Min 6 characters"
                )
                confirm_password = st.text_input(
                    "Confirm Password", type="password", placeholder="Repeat password"
                )
                submitted = st.form_submit_button(
                    "Create Account", use_container_width=True
                )
                if submitted:
                    if not new_email or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            new_email = sanitise_email(new_email)
                            sanitise_password(new_password)
                            user_data = signup_user(supabase, new_email, new_password)
                            if user_data:
                                st.success(
                                    "Account created! Please check your email "
                                    "to confirm, then log in."
                                )
                            else:
                                st.error(
                                    "Signup failed. That email may already be registered."
                                )
                        except ValueError as e:
                            st.error(str(e))

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
