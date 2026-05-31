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


def _get_google_oauth_url(supabase) -> dict:
    """
    Generate Google OAuth URL and return full diagnostic info.
    """
    result = {
        "url":       "",
        "error":     "",
        "app_url":   "",
        "provider":  "",
        "raw_resp":  ""
    }
    try:
        app_url = st.secrets.get("APP_URL", "")
        result["app_url"] = app_url

        if not app_url:
            result["error"] = "APP_URL is not set in Streamlit secrets"
            return result

        resp = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to":           app_url,
                "skip_browser_redirect": True
            }
        })

        result["raw_resp"] = str(type(resp)) + " | " + str(
            [a for a in dir(resp) if not a.startswith("_")]
        )
        result["url"]      = getattr(resp, "url", "") or ""
        result["provider"] = getattr(resp, "provider", "") or ""

        if not result["url"]:
            result["error"] = (
                "Supabase returned empty URL. "
                "Google provider may not be enabled in Supabase."
            )

    except Exception as e:
        result["error"] = str(e)

    return result


def handle_google_callback(supabase) -> bool:
    params = st.query_params

    # ── PKCE ──
    code = params.get("code", "")
    if code:
        try:
            result = supabase.auth.exchange_code_for_session(
                {"auth_code": code}
            )
            if result and getattr(result, "session", None):
                _complete_google_login(
                    supabase,
                    result.user,
                    result.session.access_token,
                    result.session.refresh_token
                )
                st.query_params.clear()
                return True
        except Exception:
            pass
        st.query_params.clear()

    # ── Implicit / hash relay ──
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


def _render_diagnostic(oauth_info: dict, supabase_url: str):
    """Full diagnostic panel — remove once working."""

    st.markdown("""
    <div style="background:#0f1e30;border:1px solid #2563eb;
        border-radius:12px;padding:20px;margin-bottom:16px;">
        <div style="color:#60A5FA;font-size:14px;font-weight:700;
            margin-bottom:12px;">🔍 Google OAuth Diagnostics</div>
    """, unsafe_allow_html=True)

    # ── Check 1: APP_URL ──
    app_url = oauth_info.get("app_url", "")
    if app_url:
        st.success(f"✅ APP_URL is set: `{app_url}`")
    else:
        st.error("❌ APP_URL is NOT set in Streamlit secrets")
        st.code("""
# Add to Streamlit Cloud → Settings → Secrets:
APP_URL = "https://loan-risk-app-pfjcxqbqzrdqkz9q7kx7ux.streamlit.app"
        """)

    # ── Check 2: OAuth URL generated ──
    url = oauth_info.get("url", "")
    if url:
        st.success("✅ Supabase generated OAuth URL successfully")
        st.markdown("**Full OAuth URL** — copy this and open in browser:")
        st.code(url, language=None)

        # Parse the URL to show what redirect_uri Supabase is sending
        if "redirect_uri" in url:
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                redir  = params.get("redirect_uri", [""])[0]
                if redir:
                    st.warning(
                        f"⚠️ Supabase is sending redirect_uri: `{redir}`\n\n"
                        f"This MUST exactly match an **Authorized redirect URI** "
                        f"in your Google Cloud Console."
                    )
            except Exception:
                pass
    else:
        err = oauth_info.get("error", "Unknown error")
        st.error(f"❌ OAuth URL generation failed: {err}")

    # ── Check 3: Expected redirect URI ──
    st.markdown("---")
    st.markdown("**Expected redirect URI in Google Cloud Console:**")
    st.code(
        f"{supabase_url}/auth/v1/callback",
        language=None
    )
    st.caption(
        "Go to Google Cloud Console → APIs & Services → Credentials "
        "→ your OAuth 2.0 Client ID → Edit → "
        "Authorized redirect URIs — it must contain exactly the above."
    )

    # ── Check 4: Consent screen ──
    st.markdown("---")
    st.markdown("**OAuth Consent Screen checklist:**")
    st.markdown("""
    Go to Google Cloud Console → APIs & Services → OAuth consent screen:

    - **Publishing status** should be `In production` (not `Testing`)
    - If still `Testing` → click **Publish App** → Confirm
    - If you see `Needs verification` that is fine — you can still test
    """)

    # ── Check 5: Manual test ──
    st.markdown("---")
    st.markdown("**Manual URL test:**")
    st.markdown(
        "Copy the full OAuth URL above, open a **new incognito window**, "
        "paste it in the address bar and press Enter. "
        "When you get the 403, **copy the full URL from the address bar** "
        "and paste it below — the error code in the URL tells us exactly "
        "what is wrong."
    )

    st.text_input(
        "Paste the 403 error page URL here:",
        key="debug_403_url",
        placeholder="https://accounts.google.com/...?error=..."
    )

    if st.session_state.get("debug_403_url"):
        error_url = st.session_state.debug_403_url
        if "redirect_uri_mismatch" in error_url:
            st.error(
                "🔴 CAUSE: redirect_uri_mismatch\n\n"
                "The redirect URI Supabase sends does NOT match "
                "what is registered in Google Cloud Console.\n\n"
                "Fix: Copy the exact URI shown above into Google Cloud "
                "Console → Authorized redirect URIs."
            )
        elif "access_denied" in error_url:
            st.error(
                "🔴 CAUSE: access_denied\n\n"
                "Your OAuth app is in Testing mode and your Google "
                "account is not listed as a test user.\n\n"
                "Fix: Go to OAuth consent screen → Test users → "
                "Add your email. OR click Publish App."
            )
        elif "invalid_client" in error_url:
            st.error(
                "🔴 CAUSE: invalid_client\n\n"
                "The Client ID or Client Secret in Supabase does not "
                "match your Google Cloud Console credentials.\n\n"
                "Fix: Go to Supabase → Auth → Providers → Google → "
                "re-paste Client ID and Client Secret from Google "
                "Cloud Console."
            )
        elif "unauthorized_client" in error_url:
            st.error(
                "🔴 CAUSE: unauthorized_client\n\n"
                "The OAuth client type is wrong — it must be "
                "'Web application' not 'Desktop app' or 'iOS'.\n\n"
                "Fix: Create a new OAuth 2.0 Client ID with type "
                "'Web application' in Google Cloud Console."
            )
        elif "disabled_client" in error_url:
            st.error(
                "🔴 CAUSE: disabled_client\n\n"
                "Your OAuth client has been disabled.\n\n"
                "Fix: Google Cloud Console → Credentials → "
                "find your client and re-enable it."
            )
        else:
            st.warning(
                f"Unknown error in URL. "
                f"Look for `error=` parameter: {error_url}"
            )

    st.markdown("</div>", unsafe_allow_html=True)


def _google_button(oauth_url: str, label: str = "Sign in with Google"):
    if not oauth_url:
        return

    safe_url = (oauth_url
                .replace("&", "&amp;")
                .replace('"', "&quot;"))

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

    st.markdown(f"""
    <style>
    .google-btn {{
        display:flex; align-items:center; justify-content:center;
        gap:12px; width:100%; height:50px; background:#ffffff;
        border:1px solid #dadce0; border-radius:8px; cursor:pointer;
        font-family:'Google Sans',Roboto,Arial,sans-serif;
        font-size:15px; font-weight:500; color:#3c4043;
        text-decoration:none;
        box-shadow:0 1px 3px rgba(0,0,0,0.15),0 1px 2px rgba(0,0,0,0.10);
        transition:background 0.15s ease,box-shadow 0.15s ease;
        margin:0 0 12px 0; box-sizing:border-box;
    }}
    .google-btn:hover {{
        background:#f8f9fa;
        box-shadow:0 2px 8px rgba(0,0,0,0.18);
        color:#3c4043; text-decoration:none;
    }}
    .google-btn:active {{ background:#f1f3f4; }}
    </style>
    <a class="google-btn" href="{safe_url}" target="_self">
        {google_svg}
        <span>{label}</span>
    </a>
    """, unsafe_allow_html=True)


def _or_divider(label="or continue with email"):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;
                margin:0 0 12px 0;">
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
            Check your inbox and spam folder, then click the link.
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
                st.success("Sent!")
            else:
                st.error("Failed. Please try again.")
    with c2:
        if st.button("Back to Login",
                     use_container_width=True, key="back_confirm"):
            st.session_state.pending_confirmation_email = None
            st.rerun()


def show_login_page(supabase):
    st.markdown("""
    <style>
    [data-testid="stSidebar"]        { display:none !important; }
    [data-testid="collapsedControl"] { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

    for k, v in [
        ("show_signup", False),
        ("pending_confirmation_email", None),
        ("google_oauth_info", None),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # Generate OAuth info once per session
    if not st.session_state.google_oauth_info:
        st.session_state.google_oauth_info = _get_google_oauth_url(supabase)

    oauth_info    = st.session_state.google_oauth_info
    oauth_url     = oauth_info.get("url", "") if oauth_info else ""
    supabase_url  = st.secrets.get("SUPABASE_URL", "")

    # ── 3D Title ──
    st.markdown("""
    <div style="text-align:center;font-size:52px;font-weight:800;
        background:linear-gradient(
            180deg,#93C5FD 0%,#3B82F6 45%,#1D4ED8 100%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        background-clip:text;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.6));
        letter-spacing:-1px;line-height:1.1;
        margin-top:40px;margin-bottom:10px;">
        AI Loan Risk Platform</div>
    <div style="text-align:center;color:#94A3B8;font-size:16px;
        margin-bottom:32px;">
        Intelligent credit evaluation for smarter lending</div>
    """, unsafe_allow_html=True)

    # ── Diagnostics panel — shown above login card ──
    _render_diagnostic(oauth_info or {}, supabase_url)

    _, col, _ = st.columns([1, 2, 1])
    with col:

        if st.session_state.pending_confirmation_email:
            _confirmation_banner(
                supabase, st.session_state.pending_confirmation_email
            )

        elif not st.session_state.show_signup:
            st.markdown("""
            <div style="text-align:center;font-size:22px;font-weight:700;
                color:#F0F4F8;margin-bottom:2px;">Welcome back</div>
            <div style="text-align:center;color:#94A3B8;font-size:14px;
                margin-bottom:20px;">Sign in to access your account</div>
            """, unsafe_allow_html=True)

            _google_button(oauth_url, "Sign in with Google")
            _or_divider("or continue with email")

            with st.form("login_form", clear_on_submit=False):
                email    = st.text_input(
                    "Email", placeholder="you@example.com"
                )
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                sub = st.form_submit_button(
                    "Login", use_container_width=True
                )
                if sub:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        try:
                            clean = sanitise_email(email)
                            sanitise_password(password)
                            with st.spinner("Signing in..."):
                                r = login_user(supabase, clean, password)
                            if r is None:
                                st.error("Something went wrong.")
                            elif r.get("error") == "email_not_confirmed":
                                st.session_state\
                                    .pending_confirmation_email = clean
                                st.rerun()
                            elif r.get("error") == "invalid_credentials":
                                st.error("Invalid email or password.")
                            elif r.get("id"):
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id":       r["id"],
                                    "email":    r["email"],
                                    "username": r["email"]
                                }
                                st.session_state.access_token  = r.get(
                                    "access_token"
                                )
                                st.session_state.refresh_token = r.get(
                                    "refresh_token"
                                )
                                st.session_state.role = get_user_role(
                                    supabase, r["id"]
                                )
                                log_action(
                                    supabase, r["id"], r["email"],
                                    "login",
                                    f"Logged in as {st.session_state.role}"
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

        else:
            st.markdown("""
            <div style="text-align:center;font-size:22px;font-weight:700;
                color:#F0F4F8;margin-bottom:2px;">Create Account</div>
            <div style="text-align:center;color:#94A3B8;font-size:14px;
                margin-bottom:20px;">Sign up for a new account</div>
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
                                r = signup_user(supabase, clean, new_pw)
                            if r is None:
                                st.error("Signup failed.")
                            elif r.get("error") == "already_registered":
                                st.warning(
                                    "Email already registered. "
                                    "Please log in."
                                )
                            elif r.get("id"):
                                log_action(
                                    supabase, r["id"], clean,
                                    "signup", "New account created"
                                )
                                if r.get("confirmed"):
                                    st.success("Account created!")
                                    st.session_state.show_signup = False
                                    st.rerun()
                                else:
                                    st.session_state\
                                        .pending_confirmation_email = clean
                                    st.session_state.show_signup = False
                                    st.rerun()
                        except ValueError as e:
                            st.error(str(e))

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()
