# ==============================
# 1. IMPORTS
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict, Any, List, Tuple
import html
import time

# ==============================
# 2. CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 3. CUSTOM CSS – FULL DARK BLUE THEME
# ==============================
st.markdown("""
<style>
/* … (your existing CSS – unchanged) … */
</style>
""", unsafe_allow_html=True)

# ==============================
# 4. SUPABASE (ONLY URL AND KEY)
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 5. SESSION STATE
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None   # "user" or "admin"
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "draft_message" not in st.session_state:
    st.session_state.draft_message = ""
if "risk_result" not in st.session_state:
    st.session_state.risk_result = None
if "repayment_result" not in st.session_state:
    st.session_state.repayment_result = None

# ==============================
# 6. MODEL
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ==============================
# HELPER FUNCTIONS
# ==============================
def login_user(email: str, password: str):
    """Authenticate user via Supabase Auth."""
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
            return {
                "id": res.user.id,
                "email": res.user.email
            }
    except Exception as e:
        st.error(f"Login error: {e}")
    return None

def explain_risk_with_citations(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, str]]]:
    reasons = []
    citations = []
    if df['income_to_loan_ratio'][0] < 0.3:
        reasons.append("📉 Low income vs loan")
        citations.append({"source": "Lending Policy §2.4", "confidence": "High"})
    if df['loan_to_value_ratio'][0] > 0.8:
        reasons.append("🚗 Loan too high vs car value")
        citations.append({"source": "Asset Valuation Guide", "confidence": "Medium"})
    if df['previous_defaults'][0] > 0:
        reasons.append("⚠️ Previous defaults")
        citations.append({"source": "Credit History", "confidence": "High"})
    if not reasons:
        reasons.append("✅ Strong profile")
        citations.append({"source": "All checks passed", "confidence": "High"})
    return reasons, citations

def suggest_improvements(df: pd.DataFrame) -> List[str]:
    suggestions = []
    if df['income_to_loan_ratio'][0] < 0.3:
        suggestions.append("Increase income or reduce loan amount")
    if df['loan_to_value_ratio'][0] > 0.8:
        suggestions.append("Provide additional collateral or reduce loan amount")
    return suggestions

def relative_time(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() // 60)
            return f"{mins} min ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours>1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days>1 else ''} ago"
        else:
            return dt.strftime("%b %d, %I:%M %p")
    except:
        return ts

def get_unread_reply_count(user_id: str) -> int:
    try:
        msgs = supabase.table("messages").select("id, reply, read_by_customer").eq("user_id", user_id).execute().data
        unseen = 0
        for m in msgs:
            if m.get("reply") and not m.get("read_by_customer", False):
                unseen += 1
        return unseen
    except:
        return 0

def mark_messages_as_read(user_id: str):
    try:
        supabase.table("messages").update({"read_by_customer": True})\
            .eq("user_id", user_id).eq("read_by_customer", False).execute()
    except:
        pass

# ==============================
# LOGOUT FUNCTION
# ==============================
def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

# ==============================
# LOGIN PAGE – FIXED ROLE FETCH
# ==============================
def show_login_page():
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="small">Sign in to access your account</div>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                user_data = login_user(email, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "id": user_data["id"],
                        "email": user_data["email"],
                        "username": email
                    }

                    # Fetch role from profiles table – safe, lowercase-converted
                    try:
                        profile = supabase.table("profiles") \
                            .select("role") \
                            .eq("id", st.session_state.user["id"]) \
                            .single() \
                            .execute()
                        # Force lowercase to avoid 'Admin' vs 'admin' mismatch
                        st.session_state.role = profile.data.get("role", "user").lower()
                    except Exception as e:
                        # If no row or error, fallback to "user"
                        st.session_state.role = "user"

                    st.rerun()
                else:
                    st.error("Invalid email or password")

        st.markdown('<p class="login-footer">Don\'t have an account? <a href="#">Sign up</a></p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ABOUT PAGE (unchanged)
# ==============================
def show_about_page():
    # … same as before …
    pass

# ==============================
# MAIN APP
# ==============================
def show_main_app():
    # … same as before, with Admin Dashboard protection …
    pass

# ==============================
# MAIN ENTRY POINT
# ==============================
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
