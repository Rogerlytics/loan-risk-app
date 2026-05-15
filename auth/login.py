# ==============================
# auth/login.py
# ==============================
import streamlit as st
from services.supabase_service import login_user, signup_user, log_action


def show_login_page(supabase):
    """Original login/signup screen with proper styling."""
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 40px 20px;
        background: linear-gradient(145deg, #111827, #0b1220);
        border-radius: 20px;
        border: 1px solid #1f2a36;
        text-align: center;
    }
    .login-title {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 20px;
    }
    .login-subtitle {
        color: #94A3B8;
        font-size: 14px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">LendAssist Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Smart loan analysis · Customer support · Car marketplace</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            user = login_user(email, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.role = user.get("role", "user")
                st.session_state.access_token = user.get("access_token")
                st.session_state.refresh_token = user.get("refresh_token")
                log_action(supabase, user["id"], user["email"], "login", "User logged in")
                st.success(f"Welcome back, {user['email']}!")
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
        if st.button("Create Account", use_container_width=True):
            if new_password != confirm:
                st.error("Passwords do not match")
            elif new_email and new_password:
                user = signup_user(new_email, new_password)
                if user:
                    st.success("Account created! Please log in.")
                else:
                    st.error("Signup failed. Email may already exist.")
            else:
                st.warning("Please fill all fields")

    st.markdown('</div>', unsafe_allow_html=True)


def logout(supabase):
    if st.session_state.get("authenticated"):
        user = st.session_state.user
        log_action(supabase, user["id"], user["email"], "logout", "User logged out")
    st.session_state.clear()
    st.rerun()
