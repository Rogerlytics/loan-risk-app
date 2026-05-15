# ==============================
# views/loan_analysis.py (original)
# ==============================
import streamlit as st
import pandas as pd
import numpy as np
from utils.helpers import format_currency, sanitise_number
from services.supabase_service import log_action


def show_loan_analysis(model, supabase):
    """Original loan analysis page – uses ML model and clean design."""
    st.markdown(
        '<div class="section-heading">📊 Loan Risk Assessment</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        income = st.number_input("💰 Monthly Income (KSh)", min_value=0, value=50000, step=10000)
        loan_amount = st.number_input("🏦 Loan Amount (KSh)", min_value=0, value=200000, step=50000)
        credit_score = st.slider("📈 Credit Score", 300, 850, 650, help="Higher is better")

    with col2:
        existing_debt = st.number_input("💳 Existing Monthly Debt (KSh)", min_value=0, value=20000, step=5000)
        loan_term = st.selectbox("⏱️ Loan Term (months)", [6, 12, 18, 24, 36, 48, 60], index=3)
        purpose = st.selectbox("🎯 Loan Purpose", ["Business", "Education", "Medical", "Home Improvement", "Debt Consolidation"])

    if st.button("🔍 Analyze Risk", use_container_width=True):
        # Prepare features for ML model (adjust to your model's expectations)
        try:
            # Example: model expects [income, loan_amount, credit_score, existing_debt, loan_term]
            features = np.array([[income, loan_amount, credit_score, existing_debt, loan_term]])
            risk_score = model.predict(features)[0] * 100  # assume model outputs 0-1
        except:
            # Fallback simple rule
            risk_score = 100 - min(100, (loan_amount / income) * 50 + (existing_debt / income) * 30)
            st.info("Using rule‑based calculation (model not compatible)")

        # Risk level
        if risk_score >= 70:
            level = "🟢 Low Risk"
            color = "green"
        elif risk_score >= 40:
            level = "🟠 Medium Risk"
            color = "orange"
        else:
            level = "🔴 High Risk"
            color = "red"

        st.markdown(f"### Risk Score: **{risk_score:.1f}** / 100")
        st.markdown(f"<h3 style='color:{color}'>{level}</h3>", unsafe_allow_html=True)

        # Monthly payment calculation
        annual_rate = 0.12  # 12% interest for medium/low risk, 18% for high
        if risk_score < 40:
            annual_rate = 0.18
        monthly_rate = annual_rate / 12
        payment = (loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term) / ((1 + monthly_rate) ** loan_term - 1)

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Estimated Monthly Payment", format_currency(payment))
        col_m2.metric("Total Interest", format_currency(payment * loan_term - loan_amount))

        # Repayment schedule
        st.markdown("### 📅 Repayment Schedule")
        balance = loan_amount
        schedule = []
        for month in range(1, loan_term + 1):
            interest = balance * monthly_rate
            principal = payment - interest
            balance -= principal
            schedule.append({
                "Month": month,
                "Payment": format_currency(payment),
                "Principal": format_currency(principal),
                "Interest": format_currency(interest),
                "Balance": format_currency(max(0, balance))
            })
        st.dataframe(pd.DataFrame(schedule), use_container_width=True, hide_index=True)

        # Log action
        user = st.session_state.user
        log_action(supabase, user["id"], user["email"], "loan_analysis",
                   f"Amount: {loan_amount}, Term: {loan_term}, Risk: {risk_score:.1f}")

    st.caption("Powered by machine learning. Estimates are for guidance only.")
