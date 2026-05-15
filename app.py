# ==============================
# app.py – Main Entry Point
# ==============================
import streamlit as st
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY, validate_secrets
from services.supabase_service import (
    sign_in, sign_up, sign_out, get_current_user,
    log_action
)
from views.loan_analysis import show_loan_analysis
from views.contact import show_contact
from views.about import show_about
from views.cars import show_cars
from views.admin_dashboard import show_admin_dashboard
from utils.helpers import apply_custom_css

# ---------- Validate secrets before anything else ----------
validate_secrets()

# ---------- Page configuration ----------
st.set_page_config(
    page_title="LendAssist Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Apply global CSS ----------
apply_custom_css()

# ---------- Initialize Supabase client ----------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Session state defaults ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "draft_message" not in st.session_state:
    st.session_state.draft_message = ""

# ---------- Helper: logout ----------
def do_logout():
    if st.session_state.authenticated:
        user = st.session_state.user
        log_action(supabase, user["id"], user["email"], "logout", "User logged out")
        sign_out()
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.page = "Login"
        st.rerun()

# ---------- Authentication UI (sidebar when logged out) ----------
def auth_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Logo", use_container_width=True)
        st.markdown("### Welcome 👋")
        
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
        
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True):
                if email and password:
                    user = sign_in(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.role = user.get("role", "user")
                        log_action(supabase, user["id"], user["email"], "login", "User logged in")
                        st.success(f"Welcome back, {user.get('email')}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.warning("Please enter email and password.")
        
        with tab_signup:
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            if st.button("Create Account", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_email and new_password:
                    user = sign_up(new_email, new_password)
                    if user:
                        st.success("Account created! Please log in.")
                    else:
                        st.error("Signup failed. Email may already exist.")
                else:
                    st.warning("Please fill all fields.")

# ---------- Main app logic ----------
def main():
    # Show authentication sidebar if not logged in
    if not st.session_state.authenticated:
        auth_sidebar()
        # Optional: show a hero message in main area
        st.markdown("""
        <div style="text-align:center; padding:80px 20px;">
            <h1 style="color:#60A5FA;">LendAssist Pro</h1>
            <p style="color:#94A3B8; font-size:18px;">Smart loan analysis · Customer support · Car marketplace</p>
            <p style="color:#64748B;">👈 Please log in or sign up using the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ---------- Logged-in user: sidebar navigation ----------
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Logo", use_container_width=True)
        st.markdown(f"**Logged in as:**  \n{st.session_state.user.get('email')}")
        if st.session_state.role == "admin":
            st.markdown("**Role:** `Admin` 🔧")
        else:
            st.markdown("**Role:** `Customer` 👤")
        
        st.markdown("---")
        
        # Navigation choices
        nav_options = ["Loan Analysis", "Contact", "About", "Car Marketplace"]
        if st.session_state.role == "admin":
            nav_options.append("Admin Dashboard")
        
        selected_page = st.radio(
            "Navigation",
            nav_options,
            index=nav_options.index(st.session_state.page) if st.session_state.page in nav_options else 0
        )
        st.session_state.page = selected_page
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            do_logout()
    
    # ---------- Route to selected page ----------
    if st.session_state.page == "Loan Analysis":
        show_loan_analysis(supabase)
    elif st.session_state.page == "Contact":
        show_contact(supabase)
    elif st.session_state.page == "About":
        show_about(supabase)
    elif st.session_state.page == "Car Marketplace":
        show_cars(supabase)
    elif st.session_state.page == "Admin Dashboard" and st.session_state.role == "admin":
        show_admin_dashboard(supabase)
    else:
        st.error("Page not found. Please select a valid option.")

if __name__ == "__main__":
    main()
