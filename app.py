import streamlit as st
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# PREMIUM UI
# ==============================
st.markdown("""
<style>
.main { background-color: #0e1117; }
h1, h2, h3 { color: white; }

.card {
    background-color: #1c1f26;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
}

.stButton>button {
    background-color: #00c2ff;
    color: black;
    border-radius: 10px;
    height: 3em;
    width: 100%;
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
        reasons.append("Low income compared to loan amount")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        reasons.append("Loan too high vs car value")

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
        suggestions.append("Reduce loan or increase collateral")

    if data['previous_defaults'].values[0] > 0:
        suggestions.append("Improve credit history")

    return suggestions

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align:center;'>AI Loan Risk Assessment System</h1>
<p style='text-align:center;color:gray;'>Machine Learning • Financial Insights</p>
""", unsafe_allow_html=True)

st.divider()

# ==============================
# SIDEBAR
# ==============================
section = st.sidebar.radio("Navigation", ["Loan Analysis", "About"])

# ==============================
# MAIN
# ==============================
if section == "Loan Analysis":

    # INPUT CARD
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

    st.divider()

    btn1, btn2 = st.columns(2)

    # ==============================
    # REPAYMENT
    # ==============================
    with btn1:
        if st.button("Calculate Repayment"):
            monthly_rate = interest_rate / 100 / 12

            monthly = (
                loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
            ) / ((1 + monthly_rate) ** loan_term - 1)

            weekly = monthly / 4.33
            daily = monthly / 30

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Repayment")

            c1, c2, c3 = st.columns(3)
            c1.metric("Monthly", f"{monthly:,.2f}")
            c2.metric("Weekly", f"{weekly:,.2f}")
            c3.metric("Daily", f"{daily:,.2f}")

            st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# LOAN RISK PREDICTION
# ==============================
with btn2:
    if st.button("🤖 Check Loan Risk"):

        # ==============================
        # Encode employment
        # ==============================
        if employment_type == "salaried":
            emp_type = 0
        elif employment_type == "self-employed":
            emp_type = 1
        else:
            emp_type = 2

        # ==============================
        # CREATE RAW DATA (for explanation)
        # ==============================
        raw_data = pd.DataFrame({
            'age': [age],
            'monthly_income': [income],
            'loan_amount': [loan_amount],
            'interest_rate': [interest_rate],
            'loan_term': [loan_term],
            'car_value': [car_value],
            'car_age': [car_age],
            'mileage': [mileage],
            'previous_loans': [previous_loans],
            'previous_defaults': [previous_defaults],
            'employment_type': [emp_type]
        })

        # Derived features
        raw_data['loan_to_value_ratio'] = (
            raw_data['loan_amount'] / raw_data['car_value']
            if car_value > 0 else 0
        )

        raw_data['income_to_loan_ratio'] = (
            raw_data['monthly_income'] / raw_data['loan_amount']
            if loan_amount > 0 else 0
        )

        # ==============================
        # MODEL INPUT (strict)
        # ==============================
        input_data = raw_data.copy()
        input_data = input_data[model.feature_names_in_]

        # ==============================
        # PREDICTION
        # ==============================
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0]
        risk_score = probability[1] * 100

        # ==============================
        # RESULT
        # ==============================
        st.subheader("🤖 AI Decision")

        if prediction == 1:
            st.error("❌ High Risk of Default")
        else:
            st.success("✅ Low Risk of Default")

        # ==============================
        # 📊 RISK SCORE
        # ==============================
        st.subheader("📊 Risk Score")
        st.progress(int(risk_score))
        st.write(f"Risk Probability: {risk_score:.2f}%")

        if risk_score > 70:
            st.error("🔴 Very High Risk")
        elif risk_score > 40:
            st.warning("🟠 Moderate Risk")
        else:
            st.success("🟢 Low Risk")

        # ==============================
        # 🧠 EXPLANATION (uses raw_data)
        # ==============================
        st.subheader("📊 Risk Explanation")
        reasons = explain_risk(raw_data)

        for r in reasons:
            st.write(f"• {r}")
