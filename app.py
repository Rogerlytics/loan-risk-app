
# ==============================
# 1. IMPORTS
# ==============================
import pickle
import html
import time
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ==============================
# 2. LOGGING
# ==============================
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ==============================
# 3. PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 4. CONSTANTS
# ==============================
WEEKS_PER_MONTH: float = 4.333
DAYS_PER_MONTH: int = 30
CHAT_HEIGHT_PX: int = 450
ADMIN_CHAT_HEIGHT_PX: int = 450
AUTO_REFRESH_SECONDS: int = 3

# ==============================
# 5. SUPABASE CLIENT (FIXED)
# ==============================
@st.cache_resource
def get_supabase_client() -> Client:
    """Safe Supabase client initialization."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")

        if not url or not key:
            st.error("❌ Supabase credentials missing in secrets.toml")
            st.stop()

        return create_client(url, key)

    except Exception as e:
        st.error(f"❌ Supabase connection failed: {str(e)}")
        st.stop()

supabase: Client = get_supabase_client()

# ==============================
# 6. MODEL (FIXED)
# ==============================
@st.cache_resource
def load_model():
    """Load ML model safely with error handling."""
    model_path = "loan_model.pkl"

    if not os.path.exists(model_path):
        logger.error("Model file missing at %s", model_path)
        st.error("❌ Model file 'loan_model.pkl' not found.")
        st.stop()

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        logger.error("Model loading failed: %s", str(e))
        st.error(f"❌ Failed to load model.")
        st.stop()

model = load_model()

# ==============================
# 7. SESSION STATE
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ==============================
# 8. SIMPLE LOGIN (placeholder)
# ==============================
def show_login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.authenticated = True
            st.session_state.user = {"email": email}
            st.session_state.role = "user"
            st.rerun()
        else:
            st.error("Enter credentials")

# ==============================
# 9. LOAN ANALYSIS (FIXED)
# ==============================
def show_loan_analysis():
    st.title("Loan Analysis")

    income = st.number_input("Income", min_value=0)
    loan_amount = st.number_input("Loan Amount", min_value=1)
    car_value = st.number_input("Car Value", min_value=1)

    if st.button("Check Risk"):
        # FIX: prevent division crash
        if loan_amount == 0 or car_value == 0:
            st.error("❌ Loan amount and car value must be greater than zero.")
            return

        df = pd.DataFrame({
            "income": [income],
            "loan_amount": [loan_amount],
            "car_value": [car_value],
        })

        df["loan_to_value_ratio"] = loan_amount / car_value
        df["income_to_loan_ratio"] = income / loan_amount

        # FIX: feature mismatch
        if hasattr(model, "feature_names_in_"):
            X = df[model.feature_names_in_]
        else:
            X = df

        try:
            pred = model.predict(X)[0]
            st.success(f"Prediction: {pred}")
        except Exception as e:
            st.error(f"Model prediction failed: {str(e)}")

# ==============================
# 10. CHAT FETCH (FIXED ORDER)
# ==============================
def fetch_messages(user_id):
    try:
        data = (
            supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=False)  # FIXED
            .execute()
            .data
        )
        return data
    except Exception as e:
        st.error("Failed to load messages")
        return []

# ==============================
# 11. MAIN
# ==============================
if not st.session_state.authenticated:
    show_login()
else:
    show_loan_analysis()
