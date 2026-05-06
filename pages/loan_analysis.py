# ==============================
# pages/loan_analysis.py
# ==============================
import streamlit as st
import pandas as pd
from utils.helpers import explain_risk_with_citations, suggest_improvements


def show_loan_analysis(model):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Input Details")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 0, 100, 30, key="age")
        income = st.number_input("Monthly Income", 0, 1000000, 50000, key="income")
        loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000, key="loan_amount")
        interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5, key="interest_rate")
        loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60], key="loan_term")
    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000, key="car_value")
        car_age = st.slider("Car Age", 0, 50, 5, key="car_age")
        mileage = st.number_input("Mileage", 0, 500000, 80000, key="mileage")
        previous_loans = st.number_input("Previous Loans", 0, 10, 1, key="previous_loans")
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0, key="previous_defaults")
    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"], key="employment_type")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Key Financial Metrics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan", f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate", f"{interest_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💰 Calculate Repayment", use_container_width=True):
            if interest_rate > 0 and loan_term > 0 and loan_amount > 0:
                r = interest_rate / 100 / 12
                m = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)
                st.session_state.repayment_result = {
                    "monthly": m,
                    "weekly": m / 4.33,
                    "daily": m / 30
                }
            else:
                st.warning("Please ensure loan amount, interest rate, and loan term are valid.")
                st.session_state.repayment_result = None

    with col_btn2:
        if st.button("🤖 Check Loan Risk", use_container_width=True):
            emp = {"salaried": 0, "self-employed": 1, "informal": 2}[employment_type]
            df = pd.DataFrame({
                'age': [age], 'monthly_income': [income], 'loan_amount': [loan_amount],
                'interest_rate': [interest_rate], 'loan_term': [loan_term],
                'car_value': [car_value], 'car_age': [car_age], 'mileage': [mileage],
                'previous_loans': [previous_loans], 'previous_defaults': [previous_defaults],
                'employment_type': [emp]
            })
            df['loan_to_value_ratio'] = loan_amount / car_value if car_value else 0
            df['income_to_loan_ratio'] = income / loan_amount if loan_amount else 0

            try:
                X = df[model.feature_names_in_]
                pred = model.predict(X)[0]
                prob = model.predict_proba(X)[0][1] * 100
                reasons, citations = explain_risk_with_citations(df)
                suggestions = suggest_improvements(df)
                st.session_state.risk_result = {
                    "prob": prob, "pred": pred,
                    "reasons": reasons, "citations": citations,
                    "suggestions": suggestions
                }
            except Exception:
                st.error("Model features mismatch. Please check inputs.")
                st.session_state.risk_result = None

    col_left_result, col_right_result = st.columns(2)
    with col_left_result:
        if st.session_state.repayment_result:
            res = st.session_state.repayment_result
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💳 Repayment Breakdown")
            st.write(f"Monthly: KES {res['monthly']:,.2f}")
            st.write(f"Weekly: KES {res['weekly']:,.2f}")
            st.write(f"Daily: KES {res['daily']:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right_result:
        if st.session_state.risk_result:
            res = st.session_state.risk_result
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🧠 AI Risk Decision")
            st.write(f"Risk Score: {res['prob']:.2f}%")
            st.progress(int(res['prob']))
            if res['pred'] == 1:
                st.error("❌ High Risk")
            else:
                st.success("✅ Low Risk")
            st.subheader("📌 Risk Factors")
            for i, r in enumerate(res['reasons']):
                src = res['citations'][i]
                st.write(f"• {r}  `[Source: {src['source']}]`  🔵 Confidence: {src['confidence']}")
            st.subheader("💡 Recommendations")
            for s in res['suggestions']:
                st.info(s)
            st.markdown('</div>', unsafe_allow_html=True)
