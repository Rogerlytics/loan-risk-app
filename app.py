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
from styles.theme import apply_theme
from services.supabase_service import (
    login_user,
    signup_user,
    get_user_role,
    get_user_messages,
    get_all_messages,
    send_message,
    send_reply,
    get_unread_reply_count,
    mark_messages_as_read
)

# ==============================
# 2. CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")
apply_theme()

# ==============================
# 3. SUPABASE CLIENT
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 4. SESSION STATE
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
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
# New session state for tokens
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

# ==============================
# 5. MODEL
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ==============================
# HELPER FUNCTIONS (non‑DB)
# ==============================
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

# ==============================
# LOGOUT FUNCTION
# ==============================
def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.rerun()

# ==============================
# LOGIN / SIGNUP PAGE
# ==============================
def show_login_page():
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        if not st.session_state.show_signup:
            st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
            st.markdown('<div class="small">Sign in to access your account</div>', unsafe_allow_html=True)

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
                            # Save tokens for session management
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
            st.markdown('<div class="section">Create Account</div>', unsafe_allow_html=True)
            st.markdown('<div class="small">Sign up for a new account</div>', unsafe_allow_html=True)

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
                            st.success("✅ Account created! Please check your email to confirm, then log in.")
                        else:
                            st.error("Signup failed. That email may already be registered.")

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# (The rest of the file – about page, main app, loan analysis, contact, admin dashboard – remains unchanged)
# ... (include the rest of the code exactly as previously given, no other modifications)
