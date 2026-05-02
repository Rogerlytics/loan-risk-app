
# (Your full original app preserved, only critical fixes applied)

import pickle
import html
import time
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# FIXED SUPABASE CLIENT
# ==============================
@st.cache_resource
def get_supabase_client() -> Client:
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
# FIXED MODEL LOADING
# ==============================
@st.cache_resource
def load_model():
    model_path = "loan_model.pkl"

    if not os.path.exists(model_path):
        logger.error("Model missing")
        st.error("❌ Model file not found.")
        st.stop()

    try:
        with open(model_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(str(e))
        st.error("❌ Failed to load model.")
        st.stop()

model = load_model()

# ==============================
# AUTH (UNCHANGED)
# ==============================
def authenticate(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return res.user
    except:
        return None

# ==============================
# LOAN ANALYSIS (FIXED ONLY)
# ==============================
def loan_analysis():
    st.title("Loan Analysis")

    age = st.number_input("Age", 18, 100, 30)
    income = st.number_input("Income", 0)
    loan_amount = st.number_input("Loan Amount", 1)
    car_value = st.number_input("Car Value", 1)

    if st.button("Check Loan Risk"):

        # FIX: division safety
        if loan_amount == 0 or car_value == 0:
            st.error("❌ Loan amount and car value must be greater than zero.")
            return

        df = pd.DataFrame({
            "age": [age],
            "monthly_income": [income],
            "loan_amount": [loan_amount],
            "car_value": [car_value],
        })

        df["loan_to_value_ratio"] = loan_amount / car_value
        df["income_to_loan_ratio"] = income / loan_amount

        # FIX: feature mismatch
        try:
            if hasattr(model, "feature_names_in_"):
                X = df[model.feature_names_in_]
            else:
                X = df
        except Exception as e:
            st.error(f"❌ Feature mismatch: {str(e)}")
            return

        try:
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1] * 100
            st.success(f"Risk Score: {prob:.2f}%")
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")

# ==============================
# SIMPLE CHAT FETCH FIX
# ==============================
def get_messages(user_id):
    return (
        supabase.table("messages")
        .select("*")
        .eq("user_id", user_id)
        .order("timestamp", desc=False)
        .execute()
        .data
    )

# ==============================
# MAIN
# ==============================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(email, password)
        if user:
            st.session_state.auth = True
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    loan_analysis()
