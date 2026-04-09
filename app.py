import streamlit as st
import pickle
import pandas as pd

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# DARK BLUE PREMIUM THEME
# ==============================
st.markdown("""
<style>

.main {
    background-color: #0b1426;
}

h1, h2, h3 {
    color: #e6edf3;
}

/* Cards */
.card {
    background: linear-gradient(145deg, #111c36, #0d162b);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.6);
    border: 1px solid rgba(0, 194, 255, 0.1);
}

/* KPI Cards */
.kpi {
    background: #0f1c35;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid rgba(0, 194, 255, 0.15);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #00c2ff, #007bff);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: 600;
    border: none;
}

/* Progress bar */
.stProgress > div > div {
    background-color: #00c2ff;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0a1222;
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
        reasons.append("Loan amount is high relative to car value")

    if data['previous_defaults'].values[0] > 0:
        reasons.append("History of previous loan defaults")

    if data['previous_loans'].values[0] > 3:
        reasons.append("Too many previous loans")

    if data['age'].values[0] < 25:
        reasons.append("Young borrower risk profile")

    if len(reasons) == 0:
        reasons.append("Strong financial profile")

    return reasons


def suggest_improvements(data):
    suggestions = []

    if data['income_to_loan_ratio'].values[0] < 0.3:
        suggestions.append("Increase income or reduce loan amount")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        suggestions.append("Reduce loan or increase collateral")

    if data['previous_defaults'].values[0] > 0:
        suggestions.append("Improve credit history")

    if data['previous_loans'].values[0] > 3:
        suggestions.append("Reduce existing loans")

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
<h1 style='text-align:center; color:#00c2ff;'>
AI Loan Risk Assessment System
</h1>
<p style='text-align:center; color:#8b9bb4;'>
Machine Learning • Financial Risk Intelligence
</p>
""", unsafe_allow_html=True)

st.divider()

# ==============================
# MAIN PAGE
# ==============================
if page == "Loan Analysis":

    # INPUT CARD
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Enter Loan Details")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Monthly Income (KES)", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount (KES)", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value (KES)", 0, 1000000, 400000)
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
    k1.markdown(f"<div class='kpi'><h3>Income</h3><p>KES {income:,}</p></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><h3>Loan</h3><p>KES {loan_amount:,}</p></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><h3>Interest</h3><p>{interest_rate}%</p></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    btn1, btn2 = st.columns(2)

    # ==============================
    # REPAYMENT
    # ==============================
    with btn1:
        if st.button("Calculate Repayment"):

            st.markdown('<div class="card">', unsafe_allow_html=True)

            monthly_rate = interest_rate / 100 / 12

            monthly = (
                loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
            ) / ((1 + monthly_rate) ** loan_term - 1)

            weekly = monthly / 4.33
            daily = monthly / 30

            st.subheader("Repayment Breakdown")

            c1, c2, c3 = st.columns(3)
            c1.metric("Monthly", f"{monthly:,.2f}")
            c2.metric("Weekly", f"{weekly:,.2f}")
            c3.metric("Daily", f"{daily:,.2f}")

            st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # RISK ANALYSIS (UPDATED FLOW)
    # ==============================
    with btn2:
        if st.button("Analyze Risk"):

            st.markdown('<div class="card">', unsafe_allow_html=True)

            emp = 0 if employment_type == "salaried" else 1 if employment_type == "self-employed" else 2

            raw_data = pd.DataFrame({
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

            raw_data['loan_to_value_ratio'] = loan_amount / car_value if car_value > 0 else 0
            raw_data['income_to_loan_ratio'] = income / loan_amount if loan_amount > 0 else 0

            input_data = raw_data.copy()
            input_data = input_data[model.feature_names_in_]

            prediction = model.predict(input_data)[0]
            probability = model.predict_proba(input_data)[0]
            risk_score = probability[1] * 100

            # RESULT
            st.subheader("AI Decision")

            if prediction == 1:
                st.error("❌ High Risk of Default")
            else:
                st.success("✅ Low Risk of Default")

            # RISK SCORE
            st.subheader("Risk Score")
            st.progress(int(risk_score))
            st.write(f"Risk Probability: {risk_score:.2f}%")

            if risk_score > 70:
                st.error("🔴 Very High Risk")
            elif risk_score > 40:
                st.warning("🟠 Moderate Risk")
            else:
                st.success("🟢 Low Risk")

            # EXPLANATION
            st.subheader("Risk Explanation")
            for r in explain_risk(raw_data):
                st.write(f"• {r}")

            # RECOMMENDATIONS
            st.subheader("Recommendations")
            suggestions = suggest_improvements(raw_data)

            if suggestions:
                for s in suggestions:
                    st.info(f"👉 {s}")
            else:
                st.success("✅ Your profile is financially healthy")

            st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ABOUT PAGE
# ==============================
elif page == "About":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("About This Project")

    st.write("""
AI-powered system for assessing loan risk using borrower financial data.

Designed for:
- Financial institutions
- Credit analysts
- Loan officers
""")

    st.markdown('</div>', unsafe_allow_html=True)
