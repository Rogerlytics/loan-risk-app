# ==============================
# views/loan_analysis.py
# ==============================
import streamlit as st
import pandas as pd
from utils.helpers import (
    explain_risk_with_citations,
    suggest_improvements,
    sanitise_number
)
from services.supabase_service import log_action


def show_loan_analysis(model, supabase):
    st.markdown(
        '<div class="section-heading">Loan Input Details</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 0, 100, 30, key="age")
        income = st.number_input(
            "Monthly Income (KES)", 0, 1_000_000, 50_000,
            step=1_000, key="income"
        )
        loan_amount = st.number_input(
            "Loan Amount (KES)", 0, 1_000_000, 200_000,
            step=1_000, key="loan_amount"
        )
        interest_rate = st.number_input(
            "Interest Rate (%)", 0.0, 100.0, 12.5,
            step=0.1, key="interest_rate"
        )
        loan_term = st.selectbox(
            "Loan Term (months)", [12, 24, 36, 48, 60],
            key="loan_term"
        )
    with col2:
        car_value = st.number_input(
            "Car Value (KES)", 0, 1_000_000, 400_000,
            step=1_000, key="car_value"
        )
        car_age = st.slider(
            "Car Age (years)", 0, 50, 5, key="car_age"
        )
        mileage = st.number_input(
            "Mileage (km)", 0, 500_000, 80_000,
            step=1_000, key="mileage"
        )
        previous_loans = st.number_input(
            "Previous Loans", 0, 10, 1, key="previous_loans"
        )
        previous_defaults = st.number_input(
            "Previous Defaults", 0, 10, 0, key="previous_defaults"
        )
    employment_type = st.selectbox(
        "Employment Type",
        ["salaried", "self-employed", "informal"],
        key="employment_type"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-heading">Key Financial Metrics</div>',
        unsafe_allow_html=True
    )
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan",   f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate",   f"{interest_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("Calculate Repayment", use_container_width=True):
            try:
                sanitise_number(loan_amount,   1,   1_000_000, "Loan Amount")
                sanitise_number(interest_rate, 0.1, 100.0,     "Interest Rate")
                sanitise_number(loan_term,     1,   60,        "Loan Term")
                with st.spinner("Calculating repayment..."):
                    r = interest_rate / 100 / 12
                    monthly = (
                        loan_amount / loan_term if r == 0
                        else loan_amount * r * (1 + r) ** loan_term
                             / ((1 + r) ** loan_term - 1)
                    )
                    st.session_state.repayment_result = {
                        "monthly": monthly,
                        "weekly":  monthly / 4.33,
                        "daily":   monthly / 30
                    }
                user = st.session_state.user
                log_action(
                    supabase, user["id"], user["email"],
                    "repayment_calculated",
                    f"Loan: KES {loan_amount:,} | "
                    f"Rate: {interest_rate}% | "
                    f"Term: {loan_term} months"
                )
            except ValueError as e:
                st.error(str(e))
                st.session_state.repayment_result = None

    with col_btn2:
        if st.button("Check Loan Risk", use_container_width=True):
            try:
                sanitise_number(age,        18, 100,       "Age")
                sanitise_number(income,      1, 1_000_000, "Monthly Income")
                sanitise_number(loan_amount, 1, 1_000_000, "Loan Amount")
                sanitise_number(car_value,   1, 1_000_000, "Car Value")
                with st.spinner("Running AI risk assessment..."):
                    emp = {
                        "salaried": 0, "self-employed": 1, "informal": 2
                    }[employment_type]
                    df = pd.DataFrame({
                        'age':               [age],
                        'monthly_income':    [income],
                        'loan_amount':       [loan_amount],
                        'interest_rate':     [interest_rate],
                        'loan_term':         [loan_term],
                        'car_value':         [car_value],
                        'car_age':           [car_age],
                        'mileage':           [mileage],
                        'previous_loans':    [previous_loans],
                        'previous_defaults': [previous_defaults],
                        'employment_type':   [emp]
                    })
                    df['loan_to_value_ratio']  = loan_amount / car_value
                    df['income_to_loan_ratio'] = income / loan_amount
                    try:
                        X    = df[model.feature_names_in_]
                        pred = model.predict(X)[0]
                        prob = model.predict_proba(X)[0][1] * 100
                        reasons, citations = explain_risk_with_citations(df)
                        suggestions = suggest_improvements(df)
                        st.session_state.risk_result = {
                            "prob":        prob,
                            "pred":        pred,
                            "reasons":     reasons,
                            "citations":   citations,
                            "suggestions": suggestions
                        }
                        risk_label = "High Risk" if pred == 1 else "Low Risk"
                        user = st.session_state.user
                        log_action(
                            supabase, user["id"], user["email"],
                            "risk_check",
                            f"Score: {prob:.1f}% | Result: {risk_label} | "
                            f"Loan: KES {loan_amount:,}"
                        )
                    except Exception:
                        st.error("Model features mismatch. Check your inputs.")
                        st.session_state.risk_result = None
            except ValueError as e:
                st.error(str(e))
                st.session_state.risk_result = None

    col_left, col_right = st.columns(2)

    with col_left:
        if st.session_state.repayment_result:
            res = st.session_state.repayment_result
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-heading">Repayment Breakdown</div>',
                unsafe_allow_html=True
            )
            st.write(f"**Monthly:** KES {res['monthly']:,.2f}")
            st.write(f"**Weekly:**  KES {res['weekly']:,.2f}")
            st.write(f"**Daily:**   KES {res['daily']:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                background:linear-gradient(145deg,#111827,#0b1220);
                border:1px dashed #1f2a36; border-radius:16px;
                padding:40px 20px; text-align:center; margin-top:8px;">
                <div style="font-size:32px; margin-bottom:10px;">💰</div>
                <div style="color:#F0F4F8; font-weight:600;
                            margin-bottom:6px;">No Repayment Calculated</div>
                <div style="color:#94A3B8; font-size:13px;">Fill in the
                    loan details and click
                    <b style="color:#60A5FA;">Calculate Repayment</b>.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        if st.session_state.risk_result:
            res = st.session_state.risk_result
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-heading">AI Risk Decision</div>',
                unsafe_allow_html=True
            )
            st.write(f"**Risk Score:** {res['prob']:.2f}%")
            st.progress(int(res['prob']))
            if res['pred'] == 1:
                st.error(
                    "High Risk — this application is likely to default."
                )
            else:
                st.success(
                    "Low Risk — this application meets credit criteria."
                )
            st.markdown(
                '<div class="section-heading">Risk Factors</div>',
                unsafe_allow_html=True
            )
            for i, r in enumerate(res['reasons']):
                src = res['citations'][i]
                st.write(
                    f"• {r}  `[{src['source']}]`  "
                    f"Confidence: {src['confidence']}"
                )
            if res['suggestions']:
                st.markdown(
                    '<div class="section-heading">Recommendations</div>',
                    unsafe_allow_html=True
                )
                for s in res['suggestions']:
                    st.info(s)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                background:linear-gradient(145deg,#111827,#0b1220);
                border:1px dashed #1f2a36; border-radius:16px;
                padding:40px 20px; text-align:center; margin-top:8px;">
                <div style="font-size:32px; margin-bottom:10px;">🤖</div>
                <div style="color:#F0F4F8; font-weight:600;
                            margin-bottom:6px;">No Risk Assessment Yet</div>
                <div style="color:#94A3B8; font-size:13px;">Fill in the
                    loan details and click
                    <b style="color:#60A5FA;">Check Loan Risk</b>.
                </div>
            </div>
            """, unsafe_allow_html=True)
