# ==============================
# IMPORTS
# ==============================
import streamlit as st
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# THEME
# ==============================
st.markdown("""
<style>
body {background:#0a0f1c; color:#e6edf3;}
.card {
    background:#111827;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SUPABASE
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# SESSION
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()

# ==============================
# MODEL
# ==============================
model = pickle.load(open("loan_model.pkl", "rb"))

# ==============================
# FUNCTIONS
# ==============================
def check_password(p):
    return bcrypt.checkpw(p.encode(), ADMIN_PASSWORD_HASH.encode())

def login(email, password):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        u = res.data[0]
        if bcrypt.checkpw(password.encode(), u["password"].encode()):
            return u
    return None

def explain_risk(df):
    reasons = []
    if df['income_to_loan_ratio'][0] < 0.3:
        reasons.append("Low income")
    if df['loan_to_value_ratio'][0] > 0.8:
        reasons.append("High loan vs car value")
    return reasons or ["Strong profile"]

# ==============================
# SIDEBAR (MUST COME BEFORE PAGES)
# ==============================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Loan Analysis", "Contact", "Admin Dashboard"]
)

# ==============================
# HEADER
# ==============================
st.title("AI Loan Risk Platform")
st.caption("Real-time credit risk evaluation")

# ==============================
# PAGES (CORRECT STRUCTURE)
# ==============================

# ------------------------------
# LOAN ANALYSIS
# ------------------------------
if page == "Loan Analysis":

    col1, col2 = st.columns(2)

    with col1:
        income = st.number_input("Income", 0, 1000000, 50000)
        loan = st.number_input("Loan", 0, 1000000, 200000)

    with col2:
        car_value = st.number_input("Car Value", 0, 1000000, 400000)

    b1, b2 = st.columns(2)

    # REPAYMENT
    with b1:
        if st.button("💰 Calculate Repayment"):
            m = loan * 0.02
            st.success(f"Monthly: {m}")

    # RISK
    with b2:
        if st.button("🤖 Check Loan Risk"):

            df = pd.DataFrame({
                'monthly_income':[income],
                'loan_amount':[loan],
                'car_value':[car_value]
            })

            df['loan_to_value_ratio'] = loan / car_value if car_value else 0
            df['income_to_loan_ratio'] = income / loan if loan else 0

            st.write("Risk:", explain_risk(df))

# ------------------------------
# CONTACT
# ------------------------------
elif page == "Contact":

    st.subheader("💬 Chat")

    if st.session_state.user:
        msg = st.text_input("Message")

        if st.button("Send"):
            supabase.table("messages").insert({
                "user_id": st.session_state.user["id"],
                "name": st.session_state.user["username"],
                "email": st.session_state.user["email"],
                "message": msg,
                "status": "sent"
            }).execute()
            st.rerun()

        msgs = supabase.table("messages").select("*").eq(
            "user_id", st.session_state.user["id"]
        ).order("id").execute().data

        for m in msgs:
            st.write(m["message"])

# ------------------------------
# ADMIN
# ------------------------------
elif page == "Admin Dashboard":

    u = st.text_input("Admin Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == ADMIN_USERNAME and check_password(p):
            st.session_state.logged_in = True

    if st.session_state.logged_in:

        data = supabase.table("messages").select("*").execute().data

        st.write("Total Messages:", len(data))

        for m in data:
            st.write(m["message"])

            reply = st.text_input(f"Reply {m['id']}")

            if st.button(f"Send {m['id']}"):
                supabase.table("messages").update({
                    "reply": reply,
                    "replied_at": str(datetime.now())
                }).eq("id", m["id"]).execute()
