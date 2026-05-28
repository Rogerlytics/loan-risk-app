# ==============================
# auth/login.py
# ==============================
import streamlit as st
import streamlit.components.v1 as components
from services.supabase_service import (
    login_user,
    signup_user,
    get_user_role,
    resend_confirmation_email,
    log_action
)
from utils.helpers import sanitise_email, sanitise_password


def logout(supabase):
    try:
        user = st.session_state.get("user")
        if user:
            log_action(
                supabase, user["id"], user["email"],
                "logout", "User logged out"
            )
    except Exception:
        pass
    for k in [
        "authenticated", "user", "role",
        "access_token", "refresh_token", "google_oauth_url"
    ]:
        st.session_state[k] = None if k != "authenticated" else False
    st.rerun()


def _get_google_oauth_url(supabase) -> str:
    """Generate Google OAuth redirect URL via Supabase."""
    try:
        app_url = st.secrets.get("APP_URL", "http://localhost:8501")
        resp = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": app_url,
                "scopes": "email profile"
            }
        })
        url = getattr(resp, "url", "") or ""
        return url
    except Exception:
        return ""


def handle_google_callback(supabase) -> bool:
    """
    Reads OAuth tokens from URL query params or hash via JS relay.
    Returns True if user was successfully authenticated.
    """
    params = st.query_params

    # PKCE code flow (if enabled in Supabase)
    code = params.get("code", "")
    if code:
        try:
            result = supabase.auth.exchange_code_for_session(
                {"auth_code": code}
            )
            if result and result.session:
                u  = result.user
                at = result.session.access_token
                rt = result.session.refresh_token
                _complete_google_login(supabase, u, at, rt)
                st.query_params.clear()
                return True
        except Exception:
            pass

    # Implicit flow — tokens sent as query params by our JS relay
    at = params.get("google_at", "")
    rt = params.get("google_rt", "")
    if at:
        try:
            supabase.auth.set_session(at, rt)
            user_resp = supabase.auth.get_user(at)
            if user_resp and user_resp.user:
                _complete_google_login(
                    supabase, user_resp.user, at, rt
                )
                st.query_params.clear()
                return True
        except Exception:
            pass
        st.query_params.clear()

    return False


def _complete_google_login(supabase, user, access_token, refresh_token):
    """Set session state after successful Google auth."""
    role = get_user_role(supabase, user.id)
    st.session_state.authenticated  = True
    st.session_state.user           = {
        "id":       user.id,
        "email":    user.email,
        "username": user.email
    }
    st.session_state.access_token  = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.role          = role
    log_action(
        supabase, user.id, user.email,
        "login", f"Signed in via Google as {role}"
    )


def _inject_hash_relay():
    """
    Injects a JS snippet that reads access_token from the URL hash
    (placed there by Supabase after Google OAuth) and re-navigates
    to the same URL with tokens as query params so Python can read them.
    Uses window.location (same frame) — no parent access needed.
    """
    components.html("""
    <!DOCTYPE html><html><body>
    <script>
    (function() {
        function relay() {
            try {
                // Try current window first
                var h = window.location.hash || '';
                // Also try parent (may work in same-origin context)
                try { h = window.parent.location.hash || h; } catch(e) {}

                if (h && h.indexOf('access_token') !== -1) {
                    var p  = new URLSearchParams(h.replace(/^#/, ''));
                    var at = p.get('access_token') || '';
                    var rt = p.get('refresh_token') || '';
                    if (at) {
                        var base = window.location.href.split('#')[0];
                        try { base = window.parent.location.href.split('#')[0]; }
                        catch(e) {}
                        // Remove any existing query
                        base = base.split('?')[0];
                        var dest = base
                            + '?google_at=' + encodeURIComponent(at)
                            + '&google_rt=' + encodeURIComponent(rt);
                        try {
                            window.parent.location.replace(dest);
                        } catch(e) {
                            window.location.replace(dest);
                        }
                        return true;
                    }
                }
            } catch(e) {}
            return false;
        }
        if (!relay()) { setTimeout(relay, 400); setTimeout(relay, 1200); }
    })();
    </script>
    </body></html>
    """, height=0)


def _google_button(oauth_url: str, label: str = "Sign in with Google"):
    """
    Renders official-style Google Sign-In button using a plain <a> tag
    in st.markdown so it navigates the main browser window directly —
    no JS, no iframe sandbox issues.
    """
    if not oauth_url:
        st.markdown("""
        <div style="background:#1f2a36;border:1px dashed #334155;
            border-radius:8px;padding:12px;text-align:center;
            color:#64748B;font-size:13px;margin:4px 0;">
            Google Sign-In is not configured yet.
        </div>
        """, unsafe_allow_html=True)
        return

    google_svg = """
    <svg width="20" height="20" viewBox="0 0 24 24"
         xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92
               c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57
               c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77
               c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93
               -6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43
               .35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45
               1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15
               C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18
               7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            fill="#EA4335"/>
    </svg>"""

    # Escape for safe embedding in HTML attribute
    safe_url = (oauth_url
                .replace("&", "&amp;")
                .replace('"', "&quot;"))

    st.markdown(f"""
    <style>
    .google-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        height: 50px;
        background: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        cursor: pointer;
        font-family: 'Google Sans', Roboto, Arial, sans-serif;
        font-size: 15px;
        font-weight: 500;
        color: #3c4043;
        text-decoration: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15),
                    0 1px 2px rgba(0,0,0,0.10);
        transition: background 0.15s ease, box-shadow 0.15s ease;
        margin: 4px 0;
        box-sizing: border-box;
    }}
    .google-btn:hover {{
        background: #f8f9fa;
        box-shadow: 0 2px 8px rgba(0,0,0,0.18);
        color: #3c4043;
        text-decoration: none;
    }}
    .google-btn:active {{ background: #f1f3f4; }}
    </style>
    <a class="google-btn" href="{safe_url}" target="_self">
        {google_svg}
        <span>{label}</span>
    </a>
    """, unsafe_allow_html=True)


def _or_divider(label="or continue with email"):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;
                margin:14px 0 10px 0;">
        <div style="flex:1;height:1px;background:#1f2a36;"></div>
        <div style="color:#475569;font-size:12px;white-space:nowrap;">
            {label}
        </div>
        <div style="flex:1;height:1px;background:#1f2a36;"></div>
    </div>
    """, unsafe_allow_html=True)


def _confirmation_banner(supabase, email: str):
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#1c1a05,#2a2005);
        border:1px solid #ca8a04;border-radius:16px;
        padding:20px 24px;margin-bottom:16px;">
        <div style="color:#fde68a;font-size:16px;font-weight:700;
                    margin-bottom:6px;">Email Not Confirmed</div>
        <div style="color:#fef3c7;font-size:13px;line-height:1.6;">
            We sent a confirmation link to
            <b style="color:#fde68a;">{email}</b>.<br>
            Check your inbox and spam folder, then click the link
            before logging in.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Resend Confirmation Email",
                     use_container_width=True, key="resend_btn"):
            with st.spinner("Sending..."):
                ok = resend_confirmation_email(supabase, email)
            if ok:
                st.success("Confirmation email resent!")
            else:
                st.error("Failed. Please try again.")
    with c2:
        if st.button("Back to Login",
                     use_container_width=True, key="back_confirm"):
            st.session_state.pending_confirmation_email = None
            st.rerun()


def show_login_page(supabase):

    # Hide sidebar
    st.markdown("""
    <style>
    [data-testid="stSidebar"]    { display:none !important; }
    [data-testid="collapsedControl"] { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Session state defaults
    for k, v in [
        ("show_signup", False),
        ("pending_confirmation_email", None),
        ("google_oauth_url", None)
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # Always inject hash relay (detects OAuth return with #access_token)
    _inject_hash_relay()

    # Generate OAuth URL once per session
    if not st.session_state.google_oauth_url:
        st.session_state.google_oauth_url = _get_google_oauth_url(supabase)
    oauth_url = st.session_state.google_oauth_url

    # ── 3D Gradient Title ──
    st.markdown("""
    <div style="
        text-align:center;
        font-size:52px;
        font-weight:800;
        background:linear-gradient(180deg,#93C5FD 0%,#3B82F6 45%,#1D4ED8 100%);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        background-clip:text;
        filter:drop-shadow(0 4px 8px rgba(0,0,0,0.6));
        letter-spacing:-1px;
        line-height:1.1;
        margin-top:40px;
        margin-bottom:10px;">AI Loan Risk Platform</div>
    <div style="
        text-align:center;
        color:#94A3B8;
        font-size:16px;
        margin-bottom:40px;">
        Intelligent credit evaluation for smarter lending</div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:

        # ── Card ──
        with st.container():
            st.markdown("""
            <div style="
                background:linear-gradient(145deg,#111827,#0b1220);
                border:1px solid #1f2a36;
                border-radius:20px;
                padding:32px 28px 24px 28px;
                box-shadow:0 20px 40px rgba(0,0,0,0.5);">
            """, unsafe_allow_html=True)

            # ── Email confirmation pending ──
            if st.session_state.pending_confirmation_email:
                _confirmation_banner(
                    supabase,
                    st.session_state.pending_confirmation_email
                )

            # ── LOGIN ──
            elif not st.session_state.show_signup:
                st.markdown("""
                <div style="text-align:center;font-size:22px;
                    font-weight:700;color:#F0F4F8;margin-bottom:2px;">
                    Welcome back</div>
                <div style="text-align:center;color:#94A3B8;
                    font-size:14px;margin-bottom:18px;">
                    Sign in to access your account</div>
                """, unsafe_allow_html=True)

                _google_button(oauth_url, "Sign in with Google")
                _or_divider("or continue with email")

                with st.form("login_form", clear_on_submit=False):
                    email    = st.text_input(
                        "Email", placeholder="you@example.com"
                    )
                    password = st.text_input(
                        "Password", type="password",
                        placeholder="••••••••"
                    )
                    sub = st.form_submit_button(
                        "Login", use_container_width=True
                    )
                    if sub:
                        if not email or not password:
                            st.error(
                                "Please enter both email and password."
                            )
                        else:
                            try:
                                clean = sanitise_email(email)
                                sanitise_password(password)
                                with st.spinner("Signing in..."):
                                    r = login_user(
                                        supabase, clean, password
                                    )
                                if r is None:
                                    st.error(
                                        "Something went wrong. Try again."
                                    )
                                elif r.get("error") == \
                                        "email_not_confirmed":
                                    st.session_state\
                                        .pending_confirmation_email \
                                        = clean
                                    st.rerun()
                                elif r.get("error") == \
                                        "invalid_credentials":
                                    st.error(
                                        "Invalid email or password."
                                    )
                                elif r.get("id"):
                                    st.session_state.authenticated = True
                                    st.session_state.user = {
                                        "id":       r["id"],
                                        "email":    r["email"],
                                        "username": r["email"]
                                    }
                                    st.session_state.access_token  = \
                                        r.get("access_token")
                                    st.session_state.refresh_token = \
                                        r.get("refresh_token")
                                    st.session_state.role = get_user_role(
                                        supabase, r["id"]
                                    )
                                    log_action(
                                        supabase, r["id"], r["email"],
                                        "login",
                                        f"Logged in as "
                                        f"{st.session_state.role}"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Invalid email or password.")
                            except ValueError as e:
                                st.error(str(e))

                if st.button(
                    "Don't have an account? Sign up →",
                    use_container_width=True
                ):
                    st.session_state.show_signup = True
                    st.session_state.pending_confirmation_email = None
                    st.rerun()

            # ── SIGN UP ──
            else:
                st.markdown("""
                <div style="text-align:center;font-size:22px;
                    font-weight:700;color:#F0F4F8;margin-bottom:2px;">
                    Create Account</div>
                <div style="text-align:center;color:#94A3B8;
                    font-size:14px;margin-bottom:18px;">
                    Sign up for a new account</div>
                """, unsafe_allow_html=True)

                _google_button(oauth_url, "Sign up with Google")
                _or_divider("or sign up with email")

                with st.form("signup_form", clear_on_submit=False):
                    new_email = st.text_input(
                        "Email", placeholder="you@example.com"
                    )
                    new_pw    = st.text_input(
                        "Password", type="password",
                        placeholder="Min 6 characters"
                    )
                    conf_pw   = st.text_input(
                        "Confirm Password", type="password",
                        placeholder="Repeat password"
                    )
                    sub = st.form_submit_button(
                        "Create Account", use_container_width=True
                    )
                    if sub:
                        if not new_email or not new_pw or not conf_pw:
                            st.error("Please fill in all fields.")
                        elif new_pw != conf_pw:
                            st.error("Passwords do not match.")
                        else:
                            try:
                                clean = sanitise_email(new_email)
                                sanitise_password(new_pw)
                                with st.spinner("Creating account..."):
                                    r = signup_user(
                                        supabase, clean, new_pw
                                    )
                                if r is None:
                                    st.error(
                                        "Signup failed. Please try again."
                                    )
                                elif r.get("error") == "already_registered":
                                    st.warning(
                                        "That email is already registered."
                                        " Please log in instead."
                                    )
                                elif r.get("id"):
                                    log_action(
                                        supabase, r["id"], clean,
                                        "signup", "New account created"
                                    )
                                    if r.get("confirmed"):
                                        st.success(
                                            "Account created! "
                                            "You can now log in."
                                        )
                                        st.session_state.show_signup = False
                                        st.rerun()
                                    else:
                                        st.session_state\
                                            .pending_confirmation_email \
                                            = clean
                                        st.session_state.show_signup = False
                                        st.rerun()
                            except ValueError as e:
                                st.error(str(e))

                if st.button(
                    "← Back to Login", use_container_width=True
                ):
                    st.session_state.show_signup = False
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
