import streamlit as st
import pickle
import pandas as pd
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 🎨 PREMIUM DARK BLUE THEME (YOUR CODE)
# ==============================
st.markdown("""
<style>

/* ===== BACKGROUND ===== */
html, body, [class*="css"] {
    background-color: #0a0f1c;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

/* ===== MAIN CONTAINER ===== */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* ===== HEADINGS ===== */
h1, h2, h3 {
    color: #e6edf3;
    font-weight: 600;
}

/* ===== CARD STYLE ===== */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.05);
}

/* ===== BUTTONS ===== */
.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    border-radius: 10px;
    height: 3em;
    font-weight: 500;
    transition: 0.3s;
}

.stButton>button:hover {
    background: linear-gradient(90deg, #1d4ed8, #1e40af);
    transform: scale(1.02);
}

/* ===== INPUT FIELDS ===== */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
textarea {
    background-color: #111827;
    color: white;
    border-radius: 8px;
    border: 1px solid #1f2937;
}

/* ===== SELECT BOX ===== */
.stSelectbox>div>div {
    background-color: #111827;
    color: white;
    border-radius: 8px;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}

/* ===== METRICS ===== */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, #111827, #0b1220);
    border-radius: 12px;
    padding: 10px;
}

/* ===== DIVIDER ===== */
hr {
    border: 1px solid rgba(255,255,255,0.05);
}

/* ===== SUCCESS / WARNING / ERROR ===== */
.stAlert {
    border-radius: 10px;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div > div {
    background-color: #2563eb;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# SUPABASE CONFIG (REPLACE)
# ==============================
SUPABASE_URL = "https://yerqsfaseucvluljaicx.supabase.co"
SUPABASE_KEY = "sb_publishable_Mve8q2zXADlFzVlCVYgdZQ_D5cu3vrD"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        reasons.append("Low income compared to loan")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        reasons.append("Loan too high vs car value")

    if data['previous_defaults'].values[0] > 0:
        reasons.append("Previous defaults")

    if data['previous_loans'].values[0] > 3:
        reasons.append("Too many loans")

    if not reasons:
        reasons.append("Strong financial profile")

    return reasons


def suggest_improvements(data):
    suggestions = []

    if data['income_to_loan_ratio'].values[0] < 0.3:
        suggestions.append("Increase income or reduce loan")

    if data['loan_to_value_ratio'].values[0] > 0.8:
        suggestions.append("Reduce loan or increase collateral")

    return suggestions

# ==============================
# SIDEBAR NAVIGATION
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact", "Admin Inbox"])

# ==============================
# SIDEBAR CONTACT
# ==============================
st.sidebar.markdown("---")
st.sidebar.subheader("Quick Contact")

s_name = st.sidebar.text_input("Name", key="s_name")
s_email = st.sidebar.text_input("Email", key="s_email")
s_message = st.sidebar.text_area("Message", key="s_message")

if st.sidebar.button("Send"):
    if s_name and s_email and s_message:
        supabase.table("messages").insert({
            "name": s_name,
            "email": s_email,
            "message": s_message
        }).execute()
        st.sidebar.success("Message sent")
    else:
        st.sidebar.warning("Fill all fields")

# ==============================
# HEADER
# ==============================
st.title("AI Loan Risk Assessment System")
st.caption("Machine Learning powered financial decision engine")
st.divider()

# ==============================
# LOAN ANALYSIS
# ==============================
if page == "Loan Analysis":

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Monthly Income", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term (Months)", [12, 24, 36, 48, 60])

    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000)
        car_age = st.slider("Car Age", 0, 50, 5)
        mileage = st.number_input("Mileage", 0, 500000, 80000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

    employment_type = st.selectbox("Employment Type", ["salaried", "self-employed", "informal"])

    st.divider()

    btn1, btn2 = st.columns(2)

    # ==============================
    # REPAYMENT CALCULATOR
    # ==============================
    with btn1:
        if st.button("Calculate Repayment"):

            if loan_amount > 0 and interest_rate > 0:

                monthly_rate = interest_rate / 100 / 12

                monthly_payment = (
                    loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term
                ) / ((1 + monthly_rate) ** loan_term - 1)

                total_payment = monthly_payment * loan_term

                weekly_payment = monthly_payment / 4.33
                daily_payment = monthly_payment / 30

                st.subheader("Repayment Results")
                st.write(f"Monthly: KES {monthly_payment:,.2f}")
                st.write(f"Weekly: KES {weekly_payment:,.2f}")
                st.write(f"Daily: KES {daily_payment:,.2f}")
                st.write(f"Total: KES {total_payment:,.2f}")

            else:
                st.warning("Enter valid values")

    # ==============================
    # RISK ANALYSIS
    # ==============================
    with btn2:
        if st.button("Check Loan Risk"):

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

            input_data = raw_data[model.feature_names_in_]

            prediction = model.predict(input_data)[0]
            probability = model.predict_proba(input_data)[0][1] * 100

            st.subheader("AI Decision")

            if prediction == 1:
                st.error("❌ High Risk of Default")
            else:
                st.success("✅ Low Risk of Default")

            st.subheader("Risk Score")
            st.progress(int(probability))
            st.write(f"Risk Probability: {probability:.2f}%")

            st.subheader("Risk Explanation")
            for r in explain_risk(raw_data):
                st.write(f"• {r}")

            st.subheader("Recommendations")
            for s in suggest_improvements(raw_data):
                st.info(f"👉 {s}")

# ==============================
# CONTACT PAGE
# ==============================
elif page == "Contact":

    st.subheader("Contact Me")

    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")

    if st.button("Send Message"):
        if name and email and message:
            supabase.table("messages").insert({
                "name": name,
                "email": email,
                "message": message
            }).execute()
            st.success("Message sent successfully")
        else:
            st.warning("Fill all fields")

# ==============================
# ADMIN INBOX (FIXED)
# ==============================
elif page == "Admin Inbox":

    st.subheader("Admin Inbox")

    try:
        response = supabase.table("messages").select("*").execute()
        messages = response.data

        st.metric("Total Messages", len(messages))

        messages = sorted(messages, key=lambda x: x['created_at'], reverse=True)

        for msg in messages:
            st.write(f"Name: {msg['name']}")
            st.write(f"Email: {msg['email']}")
            st.write(f"Message: {msg['message']}")
            st.write(f"Date: {msg['created_at']}")
            st.markdown("---")

    except Exception as e:
        st.error(f"Database error: {e}")
