import streamlit as st
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 🎨 THEME
# ==============================
st.markdown("""
<style>
html, body {
    background-color: #0a0f1c;
    color: #e6edf3;
}

.card {
    background: #111827;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.stButton>button {
    background: linear-gradient(90deg,#2563eb,#1d4ed8);
    color: white;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# SAFE START
# ==============================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
    ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None

    model = pickle.load(open("loan_model.pkl", "rb"))

    # ==============================
    # AUTH
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

    # ==============================
    # SIDEBAR
    # ==============================
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Loan Analysis","Contact","Admin Dashboard"])

    st.sidebar.title("User")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        user = login(email,password)
        if user:
            st.session_state.user = user

    # ==============================
    # HEADER
    # ==============================
    st.title("AI Loan Risk Intelligence Platform")

    # ==============================
    # LOAN ANALYSIS
    # ==============================
    if page == "Loan Analysis":

        age = st.number_input("Age",0,100,30)
        income = st.number_input("Income",0,1000000,50000)
        loan_amount = st.number_input("Loan",0,1000000,200000)
        interest_rate = st.number_input("Interest",0.0,100.0,12.5)
        loan_term = st.selectbox("Term",[12,24,36,48,60])
        car_value = st.number_input("Car Value",0,1000000,400000)

        # KPI
        c1,c2,c3 = st.columns(3)
        c1.metric("Loan",loan_amount)
        c2.metric("Income",income)
        c3.metric("Rate",interest_rate)

        b1,b2 = st.columns(2)

        # ==============================
        # REPAYMENT
        # ==============================
        with b1:
            if st.button("Calculate Repayment"):
                r = interest_rate/100/12
                m = loan_amount*r*(1+r)**loan_term/((1+r)**loan_term-1)
                st.write("Monthly:",m)
                st.write("Weekly:",m/4.33)
                st.write("Daily:",m/30)

        # ==============================
        # RISK
        # ==============================
        with b2:
            if st.button("Check Risk"):

                df = pd.DataFrame({
                    "age":[age],
                    "monthly_income":[income],
                    "loan_amount":[loan_amount],
                    "interest_rate":[interest_rate],
                    "loan_term":[loan_term],
                    "car_value":[car_value],
                    "car_age":[5],
                    "mileage":[80000],
                    "previous_loans":[1],
                    "previous_defaults":[0],
                    "employment_type":[0]
                })

                df["loan_to_value_ratio"]=loan_amount/car_value if car_value else 0
                df["income_to_loan_ratio"]=income/loan_amount if loan_amount else 0

                X=df[model.feature_names_in_]
                prob=model.predict_proba(X)[0][1]*100

                st.progress(int(prob))
                st.write("Risk:",prob)

    # ==============================
    # CONTACT (CHAT)
    # ==============================
    elif page == "Contact":

        if st.session_state.user:

            msg = st.text_input("Message")

            if st.button("Send"):
                supabase.table("messages").insert({
                    "user_id":st.session_state.user["id"],
                    "message":msg,
                    "timestamp":str(datetime.now())
                }).execute()

            msgs = supabase.table("messages").select("*").eq(
                "user_id",st.session_state.user["id"]
            ).execute().data

            for m in msgs:
                st.markdown(f"➡️ {m['message']}")
                if m.get("reply"):
                    st.markdown(f"⬅️ {m['reply']}")

    # ==============================
    # ADMIN
    # ==============================
    elif page == "Admin Dashboard":

        u = st.text_input("Admin")
        p = st.text_input("Pass", type="password")

        if st.button("Login Admin"):
            if u==ADMIN_USERNAME and check_password(p):
                st.session_state.logged_in=True

        if st.session_state.logged_in:

            data = supabase.table("messages").select("*").execute().data

            df = pd.DataFrame(data)
            st.metric("Messages",len(df))

            if not df.empty:
                df["timestamp"]=pd.to_datetime(df["timestamp"])
                daily=df.groupby(df["timestamp"].dt.date).size().reset_index(name="count")
                fig=px.line(daily,x="timestamp",y="count")
                st.plotly_chart(fig)

            for m in data:
                st.write(m["message"])
                reply = st.text_input(f"Reply {m['id']}")
                if st.button(f"Send {m['id']}"):
                    supabase.table("messages").update({
                        "reply":reply
                    }).eq("id",m["id"]).execute()

except Exception as e:
    st.error(e)
