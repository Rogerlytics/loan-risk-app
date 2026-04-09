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
    # RISK ANALYSIS (ALL VISUALS HERE)
    # ==============================
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

            # ==============================
            # RISK CARD
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Risk Analysis")

            colA, colB = st.columns(2)

            with colA:
                st.metric("Risk Score (%)", f"{prob:.2f}")
                st.progress(int(prob))  # ✅ PROGRESS BAR HERE

            with colB:
                if pred == 1:
                    st.error("❌ High Risk")
                else:
                    st.success("✅ Low Risk")

            # ==============================
            # HORIZONTAL BAR (VISUAL)
            # ==============================
            fig, ax = plt.subplots()
            ax.barh(['Risk Level'], [prob])
            ax.set_xlim(0, 100)
            ax.set_title("Risk Percentage")
            st.pyplot(fig)

            st.markdown('</div>', unsafe_allow_html=True)

            # ==============================
            # EXPLANATION
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Explanation")

            for r in explain_risk(raw):
                st.write("- " + r)

            st.markdown('</div>', unsafe_allow_html=True)

            # ==============================
            # RECOMMENDATIONS
            # ==============================
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Recommendations")

            for s in suggest_improvements(raw):
                st.write("- " + s)

            st.markdown('</div>', unsafe_allow_html=True)

elif section == "About":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("About")

    st.write("Machine learning system for loan risk evaluation and financial analysis.")

    st.markdown('</div>', unsafe_allow_html=True)
