import streamlit as st
import pickle
import pandas as pd
import bcrypt
from datetime import datetime
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# THEME
# ==============================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0a0f1c;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}

.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 10px;
    height: 3em;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SECRETS (SECURE)
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# SESSION STATE
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# MODEL (CACHED)
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ==============================
# AUTH FUNCTION
# ==============================
def check_password(password: str) -> bool:
    return bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())

# ==============================
# ML HELPERS
# ==============================
def explain_risk(data):
    reasons = []
    if data['income_to_loan_ratio'].values[0] < 0.3:
        reasons.append("Low income vs loan")
    if data['loan_to_value_ratio'].values[0] > 0.8:
        reasons.append("High loan-to-value")
    if data['previous_defaults'].values[0] > 0:
        reasons.append("Previous defaults")
    if data['previous_loans'].values[0] > 3:
        reasons.append("Too many loans")
    if not reasons:
        reasons.append("Strong profile")
    return reasons

def suggest_improvements(data):
    suggestions = []
    if data['income_to_loan_ratio'].values[0] < 0.3:
        suggestions.append("Increase income or reduce loan")
    if data['loan_to_value_ratio'].values[0] > 0.8:
        suggestions.append("Improve collateral ratio")
    return suggestions

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact", "Admin Dashboard"])

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align:center;
font-size:42px;
background: linear-gradient(90deg, #3b82f6, #60a5fa);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;'>
AI Loan Risk Intelligence Platform
</h1>
<p style='text-align:center; color:#94a3b8;'>
Real-time ML-powered credit evaluation
</p>
""", unsafe_allow_html=True)

# ==============================
# LOAN ANALYSIS
# ==============================
if page == "Loan Analysis":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Loan Input")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Income", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000)
        car_age = st.slider("Car Age", 0, 50, 5)
        mileage = st.number_input("Mileage", 0, 500000, 80000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type",
                                   ["salaried", "self-employed", "informal"])

    st.markdown('</div>', unsafe_allow_html=True)

    # REPAYMENT
    if st.button("Calculate Repayment"):

        r = interest_rate / 100 / 12
        m = loan_amount * r * (1+r)**loan_term / ((1+r)**loan_term - 1)

        st.success(f"Monthly: KES {m:,.2f}")
        st.info(f"Weekly: KES {m/4.33:,.2f}")
        st.info(f"Daily: KES {m/30:,.2f}")

    # RISK CHECK
    if st.button("Check Loan Risk"):

        emp = {"salaried":0,"self-employed":1,"informal":2}[employment_type]

        df = pd.DataFrame({
            'age':[age],
            'monthly_income':[income],
            'loan_amount':[loan_amount],
            'interest_rate':[interest_rate],
            'loan_term':[loan_term],
            'car_value':[car_value],
            'car_age':[car_age],
            'mileage':[mileage],
            'previous_loans':[previous_loans],
            'previous_defaults':[previous_defaults],
            'employment_type':[emp]
        })

        df['loan_to_value_ratio'] = loan_amount / car_value if car_value else 0
        df['income_to_loan_ratio'] = income / loan_amount if loan_amount else 0

        X = df[model.feature_names_in_]

        pred = model.predict(X)[0]
        prob = model.predict_proba(X)[0][1] * 100

        st.progress(int(prob))

        st.subheader("AI Decision")
        st.write(f"Risk Score: {prob:.2f}%")

        if pred == 1:
            st.error("High Risk")
        else:
            st.success("Low Risk")

        st.subheader("Explanation")
        st.write(explain_risk(df))

# ==============================
# CONTACT
# ==============================
elif page == "Contact":

    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")

    if st.button("Send"):
        supabase.table("messages").insert({
            "name": name,
            "email": email,
            "message": message,
            "timestamp": str(datetime.now())
        }).execute()

        st.success("Sent")

# ==============================
# ADMIN DASHBOARD
# ==============================
elif page == "Admin Dashboard":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    if not st.session_state.logged_in:

        st.subheader("Admin Login")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if u == ADMIN_USERNAME and check_password(p):
                st.session_state.logged_in = True
                st.success("Welcome Admin")
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:

        st.subheader("Analytics Dashboard")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        data = supabase.table("messages").select("*").execute().data

        df = pd.DataFrame(data)

        st.metric("Total Messages", len(df))

        if "timestamp" in df.columns:
            st.write("Recent Messages")
            st.dataframe(df.tail(10))
