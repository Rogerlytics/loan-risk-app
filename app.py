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
        # 📈 CHART 1: Loan vs Income
        # ==============================
        st.subheader("📊 Loan vs Income Analysis")

        fig1, ax1 = plt.subplots()
        ax1.bar(['Income', 'Loan Amount'], [income, loan_amount])
        ax1.set_title("Income vs Loan Amount")

        st.pyplot(fig1)

        # ==============================
        # 📉 CHART 2: Risk Gauge
        # ==============================
        st.subheader("📉 Risk Visualization")

        fig2, ax2 = plt.subplots()
        ax2.barh(['Risk Level'], [risk_score])
        ax2.set_xlim(0, 100)
        ax2.set_title("Risk Score (%)")

        st.pyplot(fig2)

        # ==============================
        # 🧠 EXPLANATION
        # ==============================
        st.subheader("📊 Risk Explanation")
        for r in explain_risk(raw_data):
            st.write(f"• {r}")

        # ==============================
        # 💡 RECOMMENDATIONS
        # ==============================
        st.subheader("💡 Recommendations")

        suggestions = suggest_improvements(raw_data)

        if suggestions:
            for s in suggestions:
                st.info(f"👉 {s}")
        else:
            st.success("✅ Your profile is financially healthy")
