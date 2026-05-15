# ==============================
# config/settings.py
# ==============================
import streamlit as st

# ── Required secrets ────────────────────────────
REQUIRED_SECRETS = ["SUPABASE_URL", "SUPABASE_KEY"]


def validate_secrets():
    """
    Check all required secrets are present before the app starts.
    Shows a clear error and stops the app if anything is missing.
    """
    missing = []
    for secret in REQUIRED_SECRETS:
        try:
            val = st.secrets[secret]
            if not val or str(val).strip() == "":
                missing.append(secret)
        except (KeyError, FileNotFoundError):
            missing.append(secret)

    if missing:
        st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }
        </style>
        """, unsafe_allow_html=True)

        st.error("⛔ App configuration error — cannot start.")
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #111827, #0b1220);
            border: 1px solid #ef4444;
            border-radius: 16px;
            padding: 24px 28px;
            margin-top: 16px;
        ">
            <div style="color:#F87171; font-size:18px; font-weight:700;
                        margin-bottom:12px;">
                Missing Required Secrets
            </div>
            <div style="color:#94A3B8; font-size:14px; margin-bottom:16px;">
                The following environment variables are not set:
            </div>
        """, unsafe_allow_html=True)

        for s in missing:
            st.markdown(f"""
            <div style="
                background:#1f2a36; border-radius:8px;
                padding:10px 16px; margin-bottom:8px;
                font-family:monospace; color:#F87171;
                border-left: 3px solid #ef4444;
            ">{s}</div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div style="color:#94A3B8; font-size:13px; margin-top:16px;">
                <b style="color:#F0F4F8;">How to fix this:</b><br><br>
                1. Go to your app on
                   <a href="https://streamlit.io/cloud" target="_blank"
                      style="color:#60A5FA;">Streamlit Cloud</a><br>
                2. Click <b style="color:#F0F4F8;">Settings</b> →
                   <b style="color:#F0F4F8;">Secrets</b><br>
                3. Add the missing keys in this format:<br><br>
                <div style="background:#0e1117; border-radius:8px;
                            padding:12px 16px; font-family:monospace;
                            color:#86efac; border:1px solid #1f2a36;">
                    SUPABASE_URL = "https://your-project.supabase.co"<br>
                    SUPABASE_KEY = "your-anon-key-here"
                </div>
            </div>
            </div>
        """, unsafe_allow_html=True)

        st.stop()


def require_role(allowed_roles: list):
    """
    Hard route protection — call at the top of any page function.
    Immediately stops the page if the user's role is not in allowed_roles.
    """
    role = st.session_state.get("role")
    authenticated = st.session_state.get("authenticated", False)

    if not authenticated or not role:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #111827, #0b1220);
            border: 1px solid #ef4444;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            margin-top: 40px;
        ">
            <div style="font-size:48px; margin-bottom:16px;">🔒</div>
            <div style="color:#F87171; font-size:20px; font-weight:700;
                        margin-bottom:8px;">Session Expired</div>
            <div style="color:#94A3B8; font-size:14px;">
                Please log in to access this page.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    if role not in allowed_roles:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, #111827, #0b1220);
            border: 1px solid #ef4444;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            margin-top: 40px;
        ">
            <div style="font-size:48px; margin-bottom:16px;">⛔</div>
            <div style="color:#F87171; font-size:20px; font-weight:700;
                        margin-bottom:8px;">Access Denied</div>
            <div style="color:#94A3B8; font-size:14px;">
                You don't have permission to view this page.<br>
                Your current role is
                <b style="color:#60A5FA;">{role.upper()}</b> —
                this page requires
                <b style="color:#60A5FA;">
                    {" or ".join(r.upper() for r in allowed_roles)}
                </b>.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()


# ── Exported constants (read from st.secrets) ─────────────────────────
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except (KeyError, FileNotFoundError):
    SUPABASE_URL = None
    SUPABASE_KEY = None
