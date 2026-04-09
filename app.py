import streamlit as st
import pickle
import pandas as pd

# ==============================
# LOAD MODEL
# ==============================
model = pickle.load(open("loan_model.pkl", "rb"))

# ==============================
# 🧠 RISK EXPLANATION FUNCTION
# ==============================
def explain_risk(data):
    reasons = []

    if data['income_to_loan_ratio'].values[0] < 0.3:
        reasons.append("Low income compared to loan amount")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        reasons.append("Loan amount is high relative to car value")

    if data['previous_defaults'].values[0] > 0:
        reasons.append("History of previous loan defaults")

    if data['previous_loans'].values[0] > 3:
        reasons.append("Too many previous loans")

    if data['age'].values[0] < 25:
        reasons.append("Very young borrower (higher risk group)")

    if len(reasons) == 0:
        reasons.append("Strong financial profile")

    return reasons

# ==============================
# 💡 RECOMMENDATION FUNCTION
# ==============================
def suggest_improvements(data):
    suggestions = []

    if data['income_to_loan_ratio'].values[0] < 0.3:
        suggestions.append("Consider increasing income or reducing loan amount")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        suggestions.append("Reduce loan amount or increase collateral value")

    if data['previous_defaults'].values[0] > 0:
        suggestions.append("Improve credit history before applying")

    if data['previous_loans'].values[0] > 3:
        suggestions.append("Reduce existing loan obligations")

    return suggestions

# ==============================
# UI HEADER
# ==============================
st.title("💰 AI Loan Risk Assessment System")
st.markdown("Built with Machine Learning • Real-time Risk Prediction")
st.markdown("---")

# ==============================
# INPUT SECTION
# ==============================
st.subheader("📥 Enter Loan Details")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Borrower Age", min_value=0, value=30)
    income = st.number_input("Monthly Income (KES)", min_value=0, value=50000)
    loan_amount = st.number_input("Loan Amount (KES)", min_value=0, value=200000)
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=12.5)
    loan_term = st.selectbox("Loan Term (Months)", [12, 18, 24, 36, 48, 60])

with col2:
    car_value = st.number_input("Car Value (KES)", min_value=0, value=400000)
    car_age = st.slider("Car Age (Years)", 0, 50, 5)
    mileage = st.number_input("Car Mileage (km)", min_value=0, value=80000)
    previous_loans = st.number_input("Previous Loans", min_value=0, value=1)
    previous_defaults = st.number_input("Previous Defaults", min_value=0, value=0)

employment_type = st.selectbox(
    "Employment Type",
    ["salaried", "self-employed", "informal"]
)

st.markdown("---")

# ==============================
# SUMMARY
# ==============================
st.subheader("📊 Input Summary")

col3, col4 = st.columns(2)

with col3:
    st.write(f"💼 Income: KES {income:,}")
    st.write(f"💳 Loan: KES {loan_amount:,}")
    st.write(f"🚗 Car Value: KES {car_value:,}")
    st.write(f"📆 Loan Term: {loan_term} months")

with col4:
    st.write(f"👤 Age: {age}")
    st.write(f"🚘 Car Age: {car_age} years")
    st.write(f"📍 Mileage: {mileage:,} km")
    st.write(f"📉 Defaults: {previous_defaults}")

st.markdown("---")

# ==============================
# BUTTONS
# ==============================
btn1, btn2 = st.columns(2)

# ==============================
# 💵 REPAYMENT CALCULATOR (UPGRADED)
# ==============================
with btn1:
    if st.button("💵 Calculate Repayment"):
        if loan_amount > 0 and interest_rate > 0 and loan_term > 0:
            monthly_rate = interest_rate / 100 / 12

            monthly_payment = (
                loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
            ) / ((1 + monthly_rate) ** loan_term - 1)

            total_payment = monthly_payment * loan_term

            # ✅ NEW CALCULATIONS
            weekly_payment = monthly_payment / 4.33
            daily_payment = monthly_payment / 30

            st.success("📊 Repayment Results")

            st.write(f"💳 Monthly Payment: KES {monthly_payment:,.2f}")
            st.write(f"📅 Weekly Payment: KES {weekly_payment:,.2f}")   # ✅ ADDED
            st.write(f"🗓️ Daily Payment: KES {daily_payment:,.2f}")     # ✅ ADDED
            st.write(f"💰 Total Repayment: KES {total_payment:,.2f}")

        else:
            st.warning("Please enter valid loan details")

# ==============================
# 🤖 LOAN RISK PREDICTION
# ==============================
with btn2:
    if st.button("🤖 Check Loan Risk"):

        if employment_type == "salaried":
            emp_type = 0
        elif employment_type == "self-employed":
            emp_type = 1
        else:
            emp_type = 2

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

        raw_data['loan_to_value_ratio'] = (
            raw_data['loan_amount'] / raw_data['car_value']
            if car_value > 0 else 0
        )

        raw_data['income_to_loan_ratio'] = (
            raw_data['monthly_income'] / raw_data['loan_amount']
            if loan_amount > 0 else 0
        )

        input_data = raw_data.copy()
        input_data = input_data[model.feature_names_in_]

        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0]
        risk_score = probability[1] * 100

        st.subheader("🤖 AI Decision")

        if prediction == 1:
            st.error("❌ High Risk of Default")
        else:
            st.success("✅ Low Risk of Default")

        st.subheader("📊 Risk Score")
        st.progress(int(risk_score))
        st.write(f"Risk Probability: {risk_score:.2f}%")

        if risk_score > 70:
            st.error("🔴 Very High Risk")
        elif risk_score > 40:
            st.warning("🟠 Moderate Risk")
        else:
            st.success("🟢 Low Risk")

        st.subheader("📊 Risk Explanation")
        for r in explain_risk(raw_data):
            st.write(f"• {r}")

        st.subheader("💡 Recommendations")
        suggestions = suggest_improvements(raw_data)

        if suggestions:
            for s in suggestions:
                st.info(f"👉 {s}")
        else:
            st.success("✅ Your profile is financially healthy")
