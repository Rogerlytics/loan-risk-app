import streamlit as st
import pickle
import pandas as pd
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 🎨 PREMIUM DARK BLUE THEME
# ==============================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0a0f1c;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}

.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 10px;
    height: 3em;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SUPABASE
# ==============================
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-key"
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
# SIDEBAR
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact", "Admin Inbox"])

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align:center;
           font-size:42px;
           background: linear-gradient(90deg, #3b82f6, #60a5fa);
           -webkit-background-clip: text;
           -webkit-text-fill-color: transparent;'>
AI Loan Risk Intelligence Platform
</h1>
<p style='text-align:center; color:#94a3b8;'>
Real-time credit risk evaluation powered by machine learning
</p>
""", unsafe_allow_html=True)

# ==============================
# MAIN PAGE
# ==============================
if page == "Loan Analysis":

    # INPUT
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Loan Input")

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

    # KPI CARDS (CLEAN VERSION)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Key Metrics")

    k1, k2, k3 = st.columns(3)
    k1.metric("Loan Amount", f"KES {loan_amount:,}")
    k2.metric("Monthly Income", f"KES {income:,}")
    k3.metric("Interest Rate", f"{interest_rate}%")

    st.markdown('</div>', unsafe_allow_html=True)

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

            weekly = monthly_payment / 4.33
            daily = monthly_payment / 30

            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader("Repayment Summary")
            st.write(f"Monthly: KES {monthly_payment:,.2f}")
            st.write(f"Weekly: KES {weekly:,.2f}")
            st.write(f"Daily: KES {daily:,.2f}")

            st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # RISK
    # ==============================
    with btn2:
        if st.button("Check Loan Risk"):

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

            inp = raw[model.feature_names_in_]

            pred = model.predict(inp)[0]
            prob = model.predict_proba(inp)[0][1] * 100

            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader("AI Decision")
            st.write(f"Risk Score: {prob:.2f}%")

            st.progress(int(prob))

            if pred == 1:
                st.error("❌ High Risk")
            else:
                st.success("✅ Low Risk")

            st.subheader("Risk Explanation")
            for r in explain_risk(raw):
                st.write(f"• {r}")

            st.subheader("Recommendations")
            for s in suggest_improvements(raw):
                st.info(s)

            st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# CONTACT
# ==============================
elif page == "Contact":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")

    if st.button("Send Message"):
        supabase.table("messages").insert({
            "name": name,
            "email": email,
            "message": message
        }).execute()
        st.success("Message sent")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ADMIN
# ==============================
elif page == "Admin Inbox":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    try:
        res = supabase.table("messages").select("*").execute()
        msgs = res.data

        st.metric("Total Messages", len(msgs))

        for m in msgs:
            st.write(m)

    except Exception as e:
        st.error(f"Database error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
