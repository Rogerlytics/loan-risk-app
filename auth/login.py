# ==============================
# auth/login.py
# ==============================
import streamlit as st
from services.supabase_service import (
    login_user,
    signup_user,
    get_user_role,
    resend_confirmation_email,
    log_action
)
from utils.helpers import sanitise_email, sanitise_password


def logout(supabase):
    """Clear session and log out user."""
    try:
        user = st.session_state.get("user")
        if user:
            log_action(
                supabase, user["id"], user["email"],
                "logout", "User logged out"
            )
    except Exception:
        pass
    
    # Clear all auth-related session state
    for k in [
        "authenticated", "user", "role",
        "access_token", "refresh_token", "google_oauth_url"
    ]:
        st.session_state[k] = None if k != "authenticated" else False
    st.rerun()


def _get_google_oauth_url(supabase) -> str:
    """
    Generate Google OAuth URL via Supabase.
    Uses PKCE flow — tokens returned as ?code= query param.
    """
    try:
        # Get app URL from secrets or fallback to Streamlit default
        app_url = st.secrets.get("APP_URL", "https://loan-risk-app-pfjcxqbqzrdqkz9q7kx7ux.streamlit.app")
        
        resp = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": app_url,
                "scopes": "email profile",
                "query_params": {
                    "access_type": "offline",
                    "prompt": "select_account"
                }
            }
        })
        
        url = getattr(resp, "url", "")
        return url if url else ""
        
    except Exception as e:
        st.error(f"OAuth configuration error: {str(e)}")
        return ""


def handle_google_callback(supabase) -> bool:
    """
    Handle OAuth callback - call this EARLY in app.py before rendering.
    Returns True when user is successfully authenticated.
    
    Note: supabase-py v2+ expects exchange_code_for_session(code: str)
    """
    params = st.query_params
    
    # Check for OAuth error first
    error = params.get("error", "")
    if error:
        error_desc = params.get("error_description", "Authentication failed")
        st.error(f"Google Sign-In error: {error_desc}")
        st.query_params.clear()
        return False
    
    # PKCE flow: Supabase returns ?code=
    code = params.get("code", "")
    if code:
        try:
            # IMPORTANT: Pass code as string, not dict (supabase-py v2+)
            result = supabase.auth.exchange_code_for_session(code)
            
            if result and hasattr(result, 'user') and result.user:
                access_token = ""
                refresh_token = ""
                
                if hasattr(result, 'session') and result.session:
                    access_token = getattr(result.session, 'access_token', '')
                    refresh_token = getattr(result.session, 'refresh_token', '')
                
                _complete_google_login(supabase, result.user, access_token, refresh_token)
                st.query_params.clear()
                return True
                
        except Exception as e:
            st.error(f"Failed to complete Google authentication: {str(e)}")
            st.query_params.clear()
            return False
    
    return False


def _complete_google_login(supabase, user, access_token: str, refresh_token: str):
    """Set all session state after successful Google auth."""
    role = get_user_role(supabase, user.id)
    
    st.session_state.authenticated = True
    st.session_state.user = {
        "id": user.id,
        "email": user.email,
        "username": user.email
    }
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.role = role
    
    log_action(
        supabase, user.id, user.email,
        "login", f"Signed in via Google as {role}"
    )


def _google_button(oauth_url: str, label: str = "Sign in with Google"):
    """
    Google Sign-In button - only renders if URL is valid.
    Uses plain <a> tag to avoid iframe/sandbox issues.
    """
    # Don't render anything if URL is empty/invalid
    if not oauth_url or not oauth_url.strip():
        return  # Silent return - no white box
    
    # Safe URL encoding for HTML
    safe_url = (oauth_url
                .replace("&", "&amp;")
                .replace('"', "&quot;"))

    google_svg = """
    <svg width="18" height="18" viewBox="0 0 24 24" 
         xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>"""

    st.markdown(f"""
    <style>
    .google-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        width: 100%;
        height: 46px;
        background: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        cursor: pointer;
        font-family: 'Google Sans', Roboto, Arial, sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #3c4043;
        text-decoration: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
        margin: 8px 0;
        box-sizing: border-box;
    }}
    .google-btn:hover {{
        background: #f8f9fa;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }}
    .google-btn:active {{
        background: #f1f3f4;
        transform: translateY(0);
    }}
    </style>
    <a class="google-btn" href="{safe_url}" target="_self" rel="noopener noreferrer">
        {google_svg}
        <span>{label}</span>
    </a>
    """, unsafe_allow_html=True)


def _or_divider(label: str = "or continue with email"):
    """Render a styled divider between auth options."""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:16px 0;">
        <div style="flex:1;height:1px;background:#1e293b;"></div>
        <div style="color:#64748b;font-size:12px;white-space:nowrap;">
            {label}
        </div>
        <div style="flex:1;height:1px;background:#1e293b;"></div>
    </div>
    """, unsafe_allow_html=True)


def _confirmation_banner(supabase, email: str):
    """Show email confirmation pending message."""
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#1c1a05,#2a2005);
        border:1px solid #ca8a04;border-radius:12px;
        padding:16px 20px;margin-bottom:16px;">
        <div style="color:#fde68a;font-size:15px;font-weight:600;
                    margin-bottom:8px;">📧 Email Not Confirmed</div>
        <div style="color:#fef3c7;font-size:13px;line-height:1.5;">
            We sent a confirmation link to
            <b style="color:#fde68a;">{email}</b>.<br>
            Check your inbox and click the link to activate your account.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Resend Email", use_container_width=True, key="resend_btn"):
            with st.spinner("Sending..."):
                ok = resend_confirmation_email(supabase, email)
            if ok:
                st.success("Confirmation email resent!")
            else:
                st.error("Failed to resend.")
    with c2:
        if st.button("Back to Login", use_container_width=True, key="back_confirm"):
            st.session_state.pending_confirmation_email = None
            st.rerun()


def show_login_page(supabase):
    """Render the complete login/signup page."""
    
    # Hide sidebar on auth pages
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display:none !important; }
    [data-testid="collapsedControl"] { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state defaults
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False
    if "pending_confirmation_email" not in st.session_state:
        st.session_state.pending_confirmation_email = None
    if "google_oauth_url" not in st.session_state:
        st.session_state.google_oauth_url = _get_google_oauth_url(supabase)

    oauth_url = st.session_state.google_oauth_url

    # Header
    st.markdown("""
    <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:42px;font-weight:800;
            background:linear-gradient(180deg,#93C5FD 0%,#3B82F6 45%,#1D4ED8 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            margin-bottom:8px;">AI Loan Risk Platform</div>
        <div style="color:#64748b;font-size:14px;">
            Intelligent credit evaluation for smarter lending
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        # Card container
        st.markdown("""
        <div style="background:linear-gradient(145deg,#0f172a,#1e293b);
            border:1px solid #334155;border-radius:16px;
            padding:28px 24px;box-shadow:0 20px 40px rgba(0,0,0,0.4);">
        """, unsafe_allow_html=True)

        # ── Email confirmation pending ──
        if st.session_state.pending_confirmation_email:
            _confirmation_banner(
                supabase, 
                st.session_state.pending_confirmation_email
            )

        # ── Login View ──
        elif not st.session_state.show_signup:
            st.markdown("""
            <div style="text-align:center;margin-bottom:20px;">
                <div style="font-size:20px;font-weight:700;color:#f1f5f9;margin-bottom:4px;">
                    Welcome back
                </div>
                <div style="color:#64748b;font-size:13px;">
                    Sign in to access your account
                </div>
            </div>
            """, unsafe_allow_html=True)

            _google_button(oauth_url, "Sign in with Google")
            _or_divider("or continue with email")

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                sub = st.form_submit_button("Login", use_container_width=True)
                
                if sub:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        try:
                            clean_email = sanitise_email(email)
                            sanitise_password(password)
                            with st.spinner("Signing in..."):
                                r = login_user(supabase, clean_email, password)
                            
                            if r is None:
                                st.error("Something went wrong. Try again.")
                            elif r.get("error") == "email_not_confirmed":
                                st.session_state.pending_confirmation_email = clean_email
                                st.rerun()
                            elif r.get("error") == "invalid_credentials":
                                st.error("Invalid email or password.")
                            elif r.get("id"):
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id": r["id"],
                                    "email": r["email"],
                                    "username": r["email"]
                                }
                                st.session_state.access_token = r.get("access_token")
                                st.session_state.refresh_token = r.get("refresh_token")
                                st.session_state.role = get_user_role(supabase, r["id"])
                                log_action(
                                    supabase, r["id"], r["email"], 
                                    "login", f"Logged in as {st.session_state.role}"
                                )
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")
                        except ValueError as e:
                            st.error(str(e))

            if st.button("Don't have an account? Sign up →", use_container_width=True):
                st.session_state.show_signup = True
                st.session_state.pending_confirmation_email = None
                st.rerun()

        # ── Sign Up View ──
        else:
            st.markdown("""
            <div style="text-align:center;margin-bottom:20px;">
                <div style="font-size:20px;font-weight:700;color:#f1f5f9;margin-bottom:4px;">
                    Create Account
                </div>
                <div style="color:#64748b;font-size:13px;">
                    Sign up for a new account
                </div>
            </div>
            """, unsafe_allow_html=True)

            _google_button(oauth_url, "Sign up with Google")
            _or_divider("or sign up with email")

            with st.form("signup_form", clear_on_submit=False):
                new_email = st.text_input("Email", placeholder="you@example.com")
                new_pw = st.text_input("Password", type="password", placeholder="Min 6 characters")
                conf_pw = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                sub = st.form_submit_button("Create Account", use_container_width=True)
                
                if sub:
                    if not new_email or not new_pw or not conf_pw:
                        st.error("Please fill in all fields.")
                    elif new_pw != conf_pw:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            clean_email = sanitise_email(new_email)
                            sanitise_password(new_pw)
                            with st.spinner("Creating account..."):
                                r = signup_user(supabase, clean_email, new_pw)
                            
                            if r is None:
                                st.error("Signup failed. Please try again.")
                            elif r.get("error") == "already_registered":
                                st.warning("That email is already registered. Please log in instead.")
                            elif r.get("id"):
                                log_action(supabase, r["id"], clean_email, "signup", "New account created")
                                if r.get("confirmed"):
                                    st.success("Account created! You can log in.")
                                    st.session_state.show_signup = False
                                    st.rerun()
                                else:
                                    st.session_state.pending_confirmation_email = clean_email
                                    st.session_state.show_signup = False
                                    st.rerun()
                        except ValueError as e:
                            st.error(str(e))

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()

        # Close card container
        st.markdown("</div>", unsafe_allow_html=True)
