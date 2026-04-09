import streamlit as st
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# PREMIUM UI STYLING
# ==============================
st.markdown("""
<style>
.main {
    background-color: #0e1117;
}

h1, h2, h3, h4 {
    color: #ffffff;
}

.card {
    background-color: #1c1f26;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    margin-bottom: 15px;
}

.stButton>button {
    background-color: #00c2ff;
    color: black;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: bold;
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
        suggestions.append("Reduce loan or increase collateral value")

    if data['previous_defaults'].values[0] > 0:
        suggestions.append("Improve credit history before applying")

    if data['previous_loans'].values[0] > 3:
        suggestions.append("Reduce number of existing loans")

    return suggestions

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align: center;'>AI Loan Risk Assessment System</h1>
<p style='text-align: center; color: gray;'>
Machine Learning • Risk Scoring • Financial Insights
</p>
""", unsafe_allow_html=True)

st.divider()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to",
    ["Loan Analysis", "About"]
)

# ==============================
# MAIN SECTION
# ==============================
if section == "Loan Analysis":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Enter Loan Details")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", min_value=0, value=30)
        income = st.number_input("Monthly Income", min_value=0, value=50000)
        loan_amount = st.number_input("Loan Amount", min_value=0, value=200000)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=12.5)
        loan_term = st.selectbox("Loan Term (Months)", [12, 18, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value", min_value=0, value=400000)
        car_age = st.slider("Car Age", 0, 50, 5)
        mileage = st.number_input("Mileage", min_value=0, value=80000)
        previous_loans = st.number_input("Previous Loans", min_value=0, value=1)
        previous_defaults = st.number_input("Previous Defaults", min_value=0, value=0)

    employment_type = st.selectbox(
        "Employment Type",
        ["salaried", "self-employed", "informal"]
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    btn1, btn2 = st.columns(2)

    # ==============================
    # REPAYMENT
    # ==============================
    with btn1:
        if st.button("Calculate Repayment"):
            monthly_rate = interest_rate / 100 / 12

            monthly_payment = (
                loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
            ) / ((1 + monthly_rate) ** loan_term - 1)

            weekly_payment = monthly_payment / 4.33
            daily_payment = monthly_payment / 30

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Repayment Breakdown")

            colA, colB, colC = st.columns(3)
            colA.metric("Monthly", f"{monthly_payment:,.2f}")
            colB.metric("Weekly", f"{weekly_payment:,.2f}")
            colC.metric("Daily", f"{daily_payment:,.2f}")

            st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # RISK ANALYSIS
    # ==============================
    with btn2:
        if st.button("Analyze Risk"):

            emp_type = 0 if employment_type == "salaried" else 1 if employment_type == "self-employed" else 2

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

            raw_data['loan_to_value_ratio'] = loan_amount / car_value if car_value > 0 else 0
            raw_data['income_to_loan_ratio'] = income / loan_amount if loan_amount > 0 else 0

            input_data = raw_data.copy()
            input_data = input_data[model.feature_names_in_]

            prediction = model.predict(input_data)[0]
            probability = model.predict_proba(input_data)[0]
            risk_score = probability[1] * 100

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Risk Analysis")

            colX, colY = st.columns(2)

            with colX:
                st.metric("Risk Score (%)", f"{risk_score:.2f}")

            with colY:
                st.metric("Decision", "High Risk" if prediction == 1 else "Low Risk")

            st.markdown('</div>', unsafe_allow_html=True)

            # ==============================
            # CHARTS
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Data Visualization")

            fig1, ax1 = plt.subplots()
            ax1.bar(['Income', 'Loan'], [income, loan_amount])
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots()
            ax2.barh(['Risk'], [risk_score])
            ax2.set_xlim(0, 100)
            st.pyplot(fig2)

            st.markdown('</div>', unsafe_allow_html=True)

            # ==============================
            # EXPLANATION
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Risk Explanation")

            for r in explain_risk(raw_data):
                st.write("- " + r)

            st.markdown('</div>', unsafe_allow_html=True)

            # ==============================
            # RECOMMENDATIONS
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Recommendations")

            suggestions = suggest_improvements(raw_data)

            if suggestions:
                for s in suggestions:
                    st.write("- " + s)
            else:
                st.write("Profile is financially strong")

            st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ABOUT SECTION
# ==============================
elif section == "About":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("About This Project")

    st.write("""
This application uses machine learning to evaluate loan risk based on borrower and asset data.

Features include:
- Risk prediction
- Financial analysis
- Repayment calculation
- Decision support insights
""")

    st.markdown('</div>', unsafe_allow_html=True)
