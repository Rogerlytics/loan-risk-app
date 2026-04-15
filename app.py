# ==============================
# LOAN ANALYSIS (FIXED LAYOUT)
# ==============================
if page == "Loan Analysis":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Input")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Monthly Income", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000)
        car_age = st.slider("Car Age", 0, 50, 5)
        mileage = st.number_input("Mileage", 0, 500000, 80000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])
    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # KPI
    # ==============================
    st.markdown('<div class="card">', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan", f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate", f"{interest_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # BUTTON COLUMNS (FIXED)
    # ==============================
    b1, b2 = st.columns(2)

    # 💰 REPAYMENT (STAYS LEFT)
    with b1:
        if st.button("💰 Calculate Repayment"):

            r = interest_rate / 100 / 12
            m = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💳 Repayment Summary")

            st.write(f"📅 Monthly: KES {m:,.2f}")
            st.write(f"🗓 Weekly: KES {m/4.33:,.2f}")
            st.write(f"⏱ Daily: KES {m/30:,.2f}")

            st.markdown('</div>', unsafe_allow_html=True)

    # 🤖 RISK (STAYS RIGHT — FIXED)
    with b2:
        if st.button("🤖 Check Loan Risk"):

            emp = {"salaried": 0, "self-employed": 1, "informal": 2}[employment_type]

            df = pd.DataFrame({
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

            df['loan_to_value_ratio'] = loan_amount / car_value if car_value else 0
            df['income_to_loan_ratio'] = income / loan_amount if loan_amount else 0

            X = df[model.feature_names_in_]
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1] * 100

            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader("🧠 AI Decision")
            st.write(f"Risk Score: {prob:.2f}%")

            st.progress(int(prob))

            if pred == 1:
                st.error("❌ High Risk")
            else:
                st.success("✅ Low Risk")

            st.subheader("📌 Risk Explanation")
            for r in explain_risk(df):
                st.write(f"• {r}")

            st.subheader("💡 Recommendations")
            for s in suggest_improvements(df):
                st.info(s)

            st.markdown('</div>', unsafe_allow_html=True)
