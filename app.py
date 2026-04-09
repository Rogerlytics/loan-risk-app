import streamlit as st
import pickle
import pandas as pd

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# NEON BLUE AI THEME
# ==============================
st.markdown("""
<style>

/* Background */
.main {
    background-color: #050a18;
}

/* Headings */
h1, h2, h3 {
    color: #00eaff;
}

/* Cards with glow */
.card {
    background: #0b1229;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0px 0px 20px rgba(0, 234, 255, 0.15);
    border: 1px solid rgba(0, 234, 255, 0.2);
}

/* KPI Cards */
.kpi {
    background: #081022;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid rgba(0, 234, 255, 0.25);
    box-shadow: 0px 0px 10px rgba(0, 234, 255, 0.1);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #00eaff, #007bff);
    color: black;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: bold;
    border: none;
    box-shadow: 0px 0px 12px rgba(0,234,255,0.5);
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #00eaff, #007bff);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #040814;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# LOAD MODEL
# ==============================
model = pickle.load(open("loan_model.pkl", "rb"))

# ==============================
# FUNCTIONS
# ==============================
def explain_risk(data):
    reasons = []

    if data['income_to_loan_ratio'].values[0] < 0.3:
        reasons.append("Low income compared to loan")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        reasons.append("Loan too high vs asset")

    if data['previous_defaults'].values[0] > 0:
        reasons.append("Past defaults")

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
        suggestions.append("Reduce loan or increase collateral")

    if data['previous_defaults'].values[0] > 0:
        suggestions.append("Improve credit history")

    return suggestions

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis", "About"])

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align:center; color:#00eaff;'>
AI Loan Risk Assessment System
</h1>
<p style='text-align:center; color:#7dd3fc;'>
AI Powered • Risk Intelligence • Smart Lending
</p>
""", unsafe_allow_html=True)

st.divider()

# ==============================
# MAIN PAGE
# ==============================
if page == "Loan Analysis":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Enter Loan Details")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Monthly Income", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000)
        car_age = st.slider("Car Age", 0, 50, 5)
        mileage = st.number_input("Mileage", 0, 500000, 80000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])

    st.markdown('</div>', unsafe_allow_html=True)

    # KPI
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Key Metrics")

    k1, k2, k3 = st.columns(3)
    k1.markdown(f"<div class='kpi'><h3>Income</h3><p>{income:,}</p></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><h3>Loan</h3><p>{loan_amount:,}</p></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><h3>Interest</h3><p>{interest_rate}%</p></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    btn1, btn2 = st.columns(2)

    # REPAYMENT
    with btn1:
        if st.button("Calculate Repayment"):
            monthly_rate = interest_rate / 100 / 12
            monthly = (loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term) / ((1 + monthly_rate) ** loan_term - 1)

            st.success(f"Monthly Payment: {monthly:,.2f}")

    # RISK
    with btn2:
        if st.button("Analyze Risk"):

            emp = 0 if employment_type == "salaried" else 1 if employment_type == "self-employed" else 2

            raw = pd.DataFrame({
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

            raw['loan_to_value_ratio'] = loan_amount / car_value if car_value > 0 else 0
            raw['income_to_loan_ratio'] = income / loan_amount if loan_amount > 0 else 0

            inp = raw.copy()
            inp = inp[model.feature_names_in_]

            pred = model.predict(inp)[0]
            prob = model.predict_proba(inp)[0][1] * 100

            st.metric("Risk Score", f"{prob:.2f}%")
            st.progress(int(prob))

            if pred == 1:
                st.error("High Risk")
            else:
                st.success("Low Risk")
