
import pickle
import html
import time
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any

import pandas as pd
import streamlit as st
from supabase import create_client, Client

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# SUPABASE CLIENT
# ==============================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        st.error("❌ Supabase credentials missing")
        st.stop()

    return create_client(url, key)

supabase = get_supabase_client()

# ==============================
# MODEL LOADING
# ==============================
@st.cache_resource
def load_model():
    path = "loan_model.pkl"
    if not os.path.exists(path):
        st.error("❌ Model not found")
        st.stop()
    with open(path, "rb") as f:
        return pickle.load(f)

model = load_model()

# ==============================
# AUTH
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
# SESSION
# ==============================
if "auth" not in st.session_state:
    st.session_state.auth = False

# ==============================
# LOGIN + SIGNUP UI
# ==============================
if not st.session_state.auth:

    st.title("AI Loan Risk Platform")

    tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            user = authenticate(email, password)
            if user:
                st.session_state.auth = True
                st.session_state.user = user
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab_signup:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Create Account"):
            try:
                res = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                if res.user:
                    st.success("✅ Account created! You can now log in.")
                else:
                    st.error("Signup failed")
            except Exception as e:
                st.error(f"Signup error: {str(e)}")

# ==============================
# LOAN ANALYSIS
# ==============================
else:
    st.title("Loan Analysis")

    age = st.number_input("Age", 18, 100, 30)
    income = st.number_input("Income", 0)
    loan_amount = st.number_input("Loan Amount", 1)
    car_value = st.number_input("Car Value", 1)

    if st.button("Check Loan Risk"):

        if loan_amount == 0 or car_value == 0:
            st.error("❌ Loan amount and car value must be greater than zero.")
            st.stop()

        df = pd.DataFrame({
            "age": [age],
            "monthly_income": [income],
            "loan_amount": [loan_amount],
            "car_value": [car_value],
        })

        df["loan_to_value_ratio"] = loan_amount / car_value
        df["income_to_loan_ratio"] = income / loan_amount

        try:
            if hasattr(model, "feature_names_in_"):
                X = df[model.feature_names_in_]
            else:
                X = df
        except Exception as e:
            st.error(f"❌ Feature mismatch: {str(e)}")
            st.stop()

        try:
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1] * 100
            st.success(f"Risk Score: {prob:.2f}%")
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")
