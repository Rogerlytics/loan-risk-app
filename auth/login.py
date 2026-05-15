# ==============================
# auth/login.py
# ==============================
import streamlit as st
from services.supabase_service import (
    login_user,
    signup_user,
    get_user_role,
    log_action
)


def show_login_page(supabase):
    """Render the login/signup screen."""
    st.markdown("""
    <div style="text-align:center; padding:20px;">
        <h1 style="color:#60A5FA;">Welcome to AI Loan Risk Platform</h1>
        <p style="color:#94A3B8;">Please log in or sign up to continue</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Login")
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
                st.success(f"Welcome, {user['email']}!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        st.markdown("### Sign Up")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        if st.button("Create Account", use_container_width=True):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif new_email and new_password:
                user = signup_user(new_email, new_password)
                if user:
                    st.success("Account created! Please log in.")
                else:
                    st.error("Signup failed. Email may already exist.")
            else:
                st.warning("Please fill all fields")


def logout(supabase):
    """Clear session and sign out."""
    if st.session_state.get("authenticated"):
        user = st.session_state.user
        log_action(supabase, user["id"], user["email"], "logout", "User logged out")
    st.session_state.clear()
    st.rerun()
