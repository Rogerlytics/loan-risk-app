import streamlit as st
import pickle
import pandas as pd
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# SUPABASE CONFIG (REPLACE THESE)
# ==============================
SUPABASE_URL = "https://yerqsfaseucvluljaicx.supabase.co"
SUPABASE_KEY = "sb_publishable_Mve8q2zXADlFzVlCVYgdZQ_D5cu3vrD"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# DARK BLUE PREMIUM THEME
# ==============================
st.markdown("""
<style>
.main {background-color: #0b1426;}
h1, h2, h3 {color: #e6edf3;}

.card {
    background: linear-gradient(145deg, #111c36, #0d162b);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.6);
}

.kpi {
    background: #0f1c35;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
}

.stButton>button {
    background: linear-gradient(90deg, #00c2ff, #007bff);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    border: none;
}

section[data-testid="stSidebar"] {
    background-color: #0a1222;
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
        reasons.append("Previous loan defaults")

    if data['previous_loans'].values[0] > 3:
        reasons.append("Too many previous loans")

    if not reasons:
        reasons.append("Strong financial profile")

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
# SIDEBAR NAVIGATION
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact", "Admin Inbox", "About"])

# ==============================
# SIDEBAR CONTACT FORM
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
        st.sidebar.success("Sent!")
    else:
        st.sidebar.warning("Fill all fields")

# ==============================
# HEADER
# ==============================
st.markdown("""
<h1 style='text-align:center; color:#00c2ff;'>AI Loan Risk Assessment System</h1>
<p style='text-align:center; color:#8b9bb4;'>Machine Learning • Financial Intelligence</p>
""", unsafe_allow_html=True)

st.divider()

# ==============================
# LOAN ANALYSIS PAGE
# ==============================
if page == "Loan Analysis":

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

    if st.button("Analyze Risk"):

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
# MAIN CONTACT PAGE
# ==============================
elif page == "Contact":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Contact Me")

    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    message = st.text_area("Your Message")

    if st.button("Send Message"):
        if name and email and message:
            supabase.table("messages").insert({
                "name": name,
                "email": email,
                "message": message
            }).execute()
            st.success("Message sent successfully!")
        else:
            st.warning("Please fill all fields")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ADMIN INBOX
# ==============================
elif page == "Admin Inbox":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Admin Inbox")

    response = supabase.table("messages").select("*").order("created_at", desc=True).execute()
    messages = response.data

    st.metric("Total Messages", len(messages))

    for msg in messages:
        st.write(f"Name: {msg['name']}")
        st.write(f"Email: {msg['email']}")
        st.write(f"Message: {msg['message']}")
        st.write(f"Date: {msg['created_at']}")
        st.markdown("---")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ABOUT
# ==============================
elif page == "About":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("About")

    st.write("AI-powered loan risk system with real-time prediction and backend integration.")

    st.markdown('</div>', unsafe_allow_html=True)
