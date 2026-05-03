
import pickle
import os
import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# SUPABASE
# ==============================
@st.cache_resource
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials")
        st.stop()
    return create_client(url, key)

supabase = get_supabase_client()

# ==============================
# MODEL
# ==============================
@st.cache_resource
def load_model():
    if not os.path.exists("loan_model.pkl"):
        st.error("Model file missing")
        st.stop()
    with open("loan_model.pkl", "rb") as f:
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

if "auth" not in st.session_state:
    st.session_state.auth = False

# ==============================
# LOGIN / SIGNUP
# ==============================
if not st.session_state.auth:
    st.title("AI Loan Risk Platform")

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate(email, password)
            if user:
                st.session_state.auth = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                res = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                if res.user:
                    st.success("Account created")
                else:
                    st.error("Signup failed")
            except Exception as e:
                st.error(str(e))

# ==============================
# MAIN APP
# ==============================
else:

    # Sidebar Navigation
    page = st.sidebar.radio("Navigation", ["Loan Analysis", "Contact", "About", "Admin"])

    if page == "Loan Analysis":

        st.title("Loan Analysis")

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", 18, 100, 30)
            income = st.number_input("Monthly Income", 0)
            employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])

        with col2:
            loan_amount = st.number_input("Loan Amount", 1)
            interest_rate = st.number_input("Interest Rate (%)", 0.1, 100.0, 12.5)
            loan_term = st.selectbox("Loan Term (months)", [12, 24, 36, 48, 60])

        car_value = st.number_input("Car Value", 1)
        car_age = st.slider("Car Age", 0, 20, 5)

        emp_map = {"salaried": 0, "self-employed": 1, "informal": 2}

        # Repayment Calculation
        if st.button("Calculate Repayment"):
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -loan_term)
            st.subheader("Repayment Breakdown")
            st.write(f"Monthly: {monthly_payment:.2f}")
            st.write(f"Weekly: {monthly_payment / 4:.2f}")
            st.write(f"Daily: {monthly_payment / 30:.2f}")

        if st.button("Check Loan Risk"):

            if loan_amount == 0 or car_value == 0:
                st.error("Invalid values")
                st.stop()

            df = pd.DataFrame({
                "age": [age],
                "monthly_income": [income],
                "loan_amount": [loan_amount],
                "interest_rate": [interest_rate],
                "loan_term": [loan_term],
                "car_value": [car_value],
                "car_age": [car_age],
                "employment_type": [emp_map[employment_type]]
            })

            df["loan_to_value_ratio"] = loan_amount / car_value
            df["income_to_loan_ratio"] = income / loan_amount

            try:
                X = df[model.feature_names_in_]
                pred = model.predict(X)[0]
                prob = model.predict_proba(X)[0][1] * 100

                st.subheader(f"Risk Score: {prob:.2f}%")

                if pred == 1:
                    st.error("High Risk")
                else:
                    st.success("Low Risk")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif page == "Contact":
        st.title("Contact Support")
        message = st.text_area("Your Message")
        if st.button("Send"):
            st.success("Message sent (placeholder)")

    elif page == "About":
        st.title("About")
        st.write("AI-powered loan risk analysis system.")

    elif page == "Admin":
        st.title("Admin Dashboard")
        st.write("Admin features coming soon...")

