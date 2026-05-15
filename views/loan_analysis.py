# ==============================
# views/loan_analysis.py
# ==============================
import streamlit as st
import pandas as pd
import numpy as np
from utils.helpers import (
    explain_risk_with_citations,
    suggest_improvements,
    sanitise_number,
    format_currency,
    calculate_risk_score
)


def show_loan_analysis(model, supabase):
    """Loan analysis page using ML model and supabase for logging."""
    st.markdown(
        '<div class="section-heading">📊 Loan Risk Analysis</div>',
        unsafe_allow_html=True
    )
    
    st.markdown("""
    <div style="background:#0f1e30; border-radius:16px; padding:20px; margin-bottom:24px;">
        <p style="color:#94A3B8; font-size:14px;">
            Enter the applicant's details to get a risk assessment, improvement suggestions,
            and a repayment plan powered by machine learning.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        income = st.number_input("Monthly Income (KSh)", min_value=0, value=50000, step=10000)
        loan_amount = st.number_input("Loan Amount (KSh)", min_value=0, value=200000, step=50000)
        credit_score = st.slider("Credit Score", 300, 850, 650)
    
    with col2:
        existing_debt = st.number_input("Existing Monthly Debt (KSh)", min_value=0, value=20000, step=5000)
        loan_term = st.selectbox("Loan Term (months)", [6, 12, 18, 24, 36, 48, 60], index=3)
        purpose = st.selectbox("Loan Purpose", ["Business", "Education", "Medical", "Home Improvement", "Debt Consolidation", "Other"])
    
    if st.button("Analyze Risk", use_container_width=True):
        # Prepare features for ML model (adjust based on your model's expected inputs)
        # Example: model expects [income, loan_amount, credit_score, existing_debt, term, purpose_encoded]
        # For now, we use a fallback risk score calculation if model fails
        try:
            # If model is a scikit-learn pipeline or classifier
            # You need to adjust feature names/encoding based on your trained model
            # Here's a generic attempt:
            features = np.array([[income, loan_amount, credit_score, existing_debt, loan_term, 0]])  # placeholder
            prediction = model.predict(features)[0]  # assume binary 0/1 or risk score
            risk_score = prediction * 100 if isinstance(prediction, (int, float)) else 50
        except Exception as e:
            # Fallback to rule-based risk score
            risk_score = calculate_risk_score(income, loan_amount, credit_score, existing_debt)
            st.warning(f"Using rule-based risk calculation (ML model error: {str(e)})")
        
        # Display results
        st.markdown("---")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Risk Score", f"{risk_score:.1f}/100")
        with col_r2:
            monthly_payment = (loan_amount / loan_term) * (1 + (0.15 if risk_score < 50 else 0.08))
            st.metric("Estimated Monthly Payment", format_currency(monthly_payment))
        
        # Explanation
        st.markdown("### 📝 Risk Explanation")
        explanation = explain_risk_with_citations(risk_score, income, loan_amount, credit_score, existing_debt)
        st.markdown(explanation, unsafe_allow_html=True)
        
        # Suggestions
        st.markdown("### 💡 Improvement Suggestions")
        suggestions = suggest_improvements(risk_score, income, loan_amount, credit_score, existing_debt)
        st.info(suggestions)
        
        # Repayment table
        st.markdown("### 📅 Repayment Schedule")
        balance = loan_amount
        schedule = []
        rate = 0.15 if risk_score < 50 else 0.08
        monthly_rate = rate / 12
        payment = (loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term) / ((1 + monthly_rate) ** loan_term - 1)
        
        for month in range(1, loan_term + 1):
            interest = balance * monthly_rate
            principal = payment - interest
            balance -= principal
            schedule.append({
                "Month": month,
                "Payment": format_currency(payment),
                "Principal": format_currency(principal),
                "Interest": format_currency(interest),
                "Remaining Balance": format_currency(max(0, balance))
            })
        
        df_schedule = pd.DataFrame(schedule)
        st.dataframe(df_schedule, use_container_width=True, hide_index=True)
        
        # Log action to supabase
        user = st.session_state.get("user")
        if user:
            from services.supabase_service import log_action
            log_action(
                supabase,
                user["id"],
                user["email"],
                "risk_check",
                f"Risk score: {risk_score:.1f}, Loan amount: {loan_amount}, Term: {loan_term}"
            )
    
    # Footer note
    st.markdown("---")
    st.caption("Risk assessment uses machine learning combined with financial rules. Always consult a professional.")
