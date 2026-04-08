# ==============================
# PROFESSIONAL HEADER
# ==============================
st.title("💰 AI Loan Risk Assessment System")
st.markdown("Built with Machine Learning • Real-time Risk Prediction")
st.markdown("---")

# ==============================
# INPUT SECTION (COLUMNS)
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
# SUMMARY SECTION
# ==============================
st.subheader("📊 Input Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.write(f"💼 Income: KES {income:,}")
    st.write(f"💳 Loan: KES {loan_amount:,}")
    st.write(f"🚗 Car Value: KES {car_value:,}")
    st.write(f"📆 Loan Term: {loan_term} months")

with summary_col2:
    st.write(f"👤 Age: {age}")
    st.write(f"🚘 Car Age: {car_age} years")
    st.write(f"📍 Mileage: {mileage:,} km")
    st.write(f"📉 Defaults: {previous_defaults}")

st.markdown("---")

# ==============================
# ACTION BUTTONS (SIDE BY SIDE)
# ==============================
btn1, btn2 = st.columns(2)

# ==============================
# REPAYMENT CALCULATOR
# ==============================
with btn1:
    if st.button("💵 Calculate Repayment"):
        if loan_amount > 0 and interest_rate > 0 and loan_term > 0:
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = (
                loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
            ) / ((1 + monthly_rate) ** loan_term - 1)

            total_payment = monthly_payment * loan_term

            st.success("📊 Repayment Results")
            st.write(f"Monthly Payment: KES {monthly_payment:,.2f}")
            st.write(f"Total Repayment: KES {total_payment:,.2f}")
        else:
            st.warning("Please enter valid loan details")

# ==============================
# LOAN RISK PREDICTION
# ==============================
with btn2:
    if st.button("🤖 Check Loan Risk"):

        # Encode employment type
        if employment_type == "salaried":
            emp_type = 0
        elif employment_type == "self-employed":
            emp_type = 1
        else:
            emp_type = 2

        # Create DataFrame
        input_data = pd.DataFrame({
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

        # Derived features
        input_data['loan_to_value_ratio'] = (
            input_data['loan_amount'] / input_data['car_value']
            if car_value > 0 else 0
        )

        input_data['income_to_loan_ratio'] = (
            input_data['monthly_income'] / input_data['loan_amount']
            if loan_amount > 0 else 0
        )

        # Match model columns
        input_data = input_data[model.feature_names_in_]

        prediction = model.predict(input_data)[0]

        st.subheader("🤖 AI Decision")

        if prediction == 1:
            st.error("❌ High Risk of Default")
        else:
            st.success("✅ Low Risk of Default")
