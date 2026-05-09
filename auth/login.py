# ==============================
# auth/login.py
# ==============================
import streamlit as st
from services.supabase_service import login_user, signup_user, get_user_role


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.rerun()


def show_login_page(supabase):
    # Extra aggressive sidebar + collapse arrow hide on login
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # 3D Blue Title — centred, same style as all other pages
    st.markdown("""
    <div style="
        text-align: center;
        font-size: 48px;
        font-weight: 800;
        color: #60A5FA;
        text-shadow:
            0 1px 0 #2563eb,
            0 2px 0 #1d4ed8,
            0 3px 0 #1e40af,
            0 4px 0 #1e3a8a,
            0 5px 10px rgba(0,0,0,0.6);
        letter-spacing: -0.5px;
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
        # Single HTML block for the card — avoids the empty box bug
        st.markdown("""
        <div style="
            background: rgba(26,46,68,0.85);
            backdrop-filter: blur(12px);
            border: 1px solid #2563eb;
            border-radius: 24px;
            padding: 36px 32px 24px 32px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            margin-bottom: 0px;
        ">
        """, unsafe_allow_html=True)

        if not st.session_state.show_signup:
            st.markdown("""
            <div style="text-align:center; font-size:22px; font-weight:700;
                color:#F0F4F8; margin-bottom:4px;">Welcome back</div>
            <div style="text-align:center; color:#94A3B8; font-size:14px;
                margin-bottom:24px;">Sign in to access your account</div>
            """, unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
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
                            st.session_state.role = get_user_role(supabase, st.session_state.user["id"])
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

            if st.button("Don't have an account? Sign up →", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

        else:
            st.markdown("""
            <div style="text-align:center; font-size:22px; font-weight:700;
                color:#F0F4F8; margin-bottom:4px;">Create Account</div>
            <div style="text-align:center; color:#94A3B8; font-size:14px;
                margin-bottom:24px;">Sign up for a new account</div>
            """, unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                new_email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    if not new_email or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        user_data = signup_user(supabase, new_email, new_password)
                        if user_data:
                            st.success("Account created! Please check your email to confirm, then log in.")
                        else:
                            st.error("Signup failed. That email may already be registered.")

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
