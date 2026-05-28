```python
# ==============================
# auth/login.py
# COMPLETE WORKING FILE
# ==============================

import streamlit as st

from services.supabase_service import (
    login_user,
    signup_user,
    get_user_role,
    resend_confirmation_email,
    log_action
)

from utils.helpers import (
    sanitise_email,
    sanitise_password
)


# ─────────────────────────────
# LOGOUT
# ─────────────────────────────
def logout(supabase):

    try:

        user = st.session_state.get("user")

        if user:

            log_action(
                supabase,
                user["id"],
                user["email"],
                "logout",
                "User logged out"
            )

    except Exception:
        pass

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# ─────────────────────────────
# GOOGLE OAUTH URL
# ─────────────────────────────
def get_google_oauth_url():

    supabase_url = st.secrets["SUPABASE_URL"]

    app_url = st.secrets["APP_URL"]

    return (
        f"{supabase_url}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={app_url}"
    )


# ─────────────────────────────
# GOOGLE BUTTON
# ─────────────────────────────
def render_google_button():

    oauth_url = get_google_oauth_url()

    st.markdown(
        f"""
        <a href="{oauth_url}" target="_self"
           style="text-decoration:none;">

            <div style="
                width:100%;
                height:52px;
                border-radius:10px;
                background:white;
                color:#111827;
                font-size:15px;
                font-weight:600;
                cursor:pointer;
                box-shadow:0 1px 3px rgba(0,0,0,0.15);

                display:flex;
                align-items:center;
                justify-content:center;

                margin-bottom:10px;
            ">

                Continue with Google

            </div>

        </a>
        """,
        unsafe_allow_html=True
    )


# ─────────────────────────────
# DIVIDER
# ─────────────────────────────
def _or_divider(label="or continue with email"):

    st.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            gap:12px;
            margin:18px 0;
        ">

            <div style="
                flex:1;
                height:1px;
                background:#1f2a36;
            "></div>

            <div style="
                color:#64748B;
                font-size:12px;
                white-space:nowrap;
            ">
                {label}
            </div>

            <div style="
                flex:1;
                height:1px;
                background:#1f2a36;
            "></div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ─────────────────────────────
# EMAIL CONFIRMATION
# ─────────────────────────────
def _confirmation_banner(supabase, email):

    st.warning(
        f"""
        Email confirmation required.

        Please check your inbox for:

        {email}
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Resend Email",
            use_container_width=True
        ):

            ok = resend_confirmation_email(
                supabase,
                email
            )

            if ok:
                st.success("Confirmation email sent.")
            else:
                st.error("Failed to send email.")

    with col2:

        if st.button(
            "Back to Login",
            use_container_width=True
        ):

            st.session_state.pending_confirmation_email = None

            st.rerun()


# ─────────────────────────────
# MAIN LOGIN PAGE
# ─────────────────────────────
def show_login_page(supabase):

    # Hide sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display:none !important;
        }

        [data-testid="collapsedControl"] {
            display:none !important;
        }

        .stApp {
            background:#020617;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Session defaults
    defaults = {
        "show_signup": False,
        "pending_confirmation_email": None
    }

    for k, v in defaults.items():

        if k not in st.session_state:
            st.session_state[k] = v

    # ─────────────────────────
    # TITLE
    # ─────────────────────────
    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:50px;
            margin-bottom:40px;
        ">

            <div style="
                font-size:48px;
                font-weight:800;
                color:#60A5FA;
            ">
                AI Loan Risk Platform
            </div>

            <div style="
                color:#94A3B8;
                font-size:16px;
                margin-top:8px;
            ">
                Intelligent credit evaluation for smarter lending
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    _, col, _ = st.columns([1, 2, 1])

    with col:

        st.markdown(
            """
            <div style="
                background:#0F172A;
                border:1px solid #1E293B;
                border-radius:20px;
                padding:35px;
                box-shadow:0 10px 30px rgba(0,0,0,0.35);
            ">
            """,
            unsafe_allow_html=True
        )

        # ─────────────────────
        # CONFIRMATION
        # ─────────────────────
        if st.session_state.pending_confirmation_email:

            _confirmation_banner(
                supabase,
                st.session_state.pending_confirmation_email
            )

        # ─────────────────────
        # LOGIN
        # ─────────────────────
        elif not st.session_state.show_signup:

            st.markdown(
                """
                <h2 style="
                    text-align:center;
                    color:white;
                    margin-bottom:20px;
                ">
                    Welcome Back
                </h2>
                """,
                unsafe_allow_html=True
            )

            render_google_button()

            _or_divider()

            with st.form("login_form"):

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••"
                )

                submit = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )

                if submit:

                    try:

                        clean = sanitise_email(email)

                        sanitise_password(password)

                        r = login_user(
                            supabase,
                            clean,
                            password
                        )

                        if r.get("id"):

                            st.session_state.authenticated = True

                            st.session_state.user = {
                                "id": r["id"],
                                "email": r["email"],
                                "username": r["email"]
                            }

                            st.session_state.role = get_user_role(
                                supabase,
                                r["id"]
                            )

                            st.rerun()

                        elif r.get("error") == "email_not_confirmed":

                            st.session_state.pending_confirmation_email = clean

                            st.rerun()

                        else:

                            st.error(
                                "Invalid email or password."
                            )

                    except Exception as e:

                        st.error(str(e))

            if st.button(
                "Create Account",
                use_container_width=True
            ):

                st.session_state.show_signup = True

                st.rerun()

        # ─────────────────────
        # SIGNUP
        # ─────────────────────
        else:

            st.markdown(
                """
                <h2 style="
                    text-align:center;
                    color:white;
                    margin-bottom:20px;
                ">
                    Create Account
                </h2>
                """,
                unsafe_allow_html=True
            )

            render_google_button()

            _or_divider("or sign up with email")

            with st.form("signup_form"):

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 6 characters"
                )

                confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat password"
                )

                submit = st.form_submit_button(
                    "Create Account",
                    use_container_width=True
                )

                if submit:

                    if password != confirm:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        try:

                            clean = sanitise_email(email)

                            sanitise_password(password)

                            r = signup_user(
                                supabase,
                                clean,
                                password
                            )

                            if r.get("id"):

                                st.success(
                                    "Account created successfully."
                                )

                                st.session_state.show_signup = False

                                st.rerun()

                            else:

                                st.error(
                                    "Signup failed."
                                )

                        except Exception as e:

                            st.error(str(e))

            if st.button(
                "Back to Login",
                use_container_width=True
            ):

                st.session_state.show_signup = False

                st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )
```
