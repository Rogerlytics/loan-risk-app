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
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SECRETS
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# SESSION
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()

# ==============================
# MODEL
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

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
# HELPERS
# ==============================
def explain_risk(df):
    r=[]
    if df['income_to_loan_ratio'][0]<0.3:
        r.append("📉 Low income vs loan")
    if df['loan_to_value_ratio'][0]>0.8:
        r.append("🚗 Loan too high vs car value")
    if df['previous_defaults'][0]>0:
        r.append("⚠️ Previous defaults")
    if not r:
        r.append("✅ Strong profile")
    return r

def suggest_improvements(df):
    s=[]
    if df['income_to_loan_ratio'][0]<0.3:
        s.append("Increase income")
    if df['loan_to_value_ratio'][0]>0.8:
        s.append("Increase collateral")
    return s

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Loan Analysis","Contact","Admin Dashboard"])

st.sidebar.title("User Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    user = login(email,password)
    if user:
        st.session_state.user = user
        st.sidebar.success("Logged in")
    else:
        st.sidebar.error("Invalid login")

if st.session_state.user:
    st.sidebar.write(f"👤 {st.session_state.user['username']}")

# ==============================
# HEADER
# ==============================
st.markdown("<h1 style='text-align:center;color:#3b82f6'>AI Loan Risk Platform</h1>",unsafe_allow_html=True)

# ==============================
# LOAN ANALYSIS
# ==============================
if page == "Loan Analysis":

    col1,col2=st.columns(2)

    with col1:
        age=st.number_input("Age",0,100,30)
        income=st.number_input("Income",0,1000000,50000)
        loan_amount=st.number_input("Loan",0,1000000,200000)
        rate=st.number_input("Interest",0.0,100.0,12.5)
        term=st.selectbox("Term",[12,24,36,48,60])

    with col2:
        car_value=st.number_input("Car Value",0,1000000,400000)
        car_age=st.slider("Car Age",0,50,5)
        mileage=st.number_input("Mileage",0,500000,80000)
        prev_loans=st.number_input("Loans",0,10,1)
        prev_defaults=st.number_input("Defaults",0,10,0)

    emp=st.selectbox("Employment",["salaried","self-employed","informal"])

    b1,b2=st.columns(2)

    if b1.button("💰 Calculate Repayment"):
        r=rate/100/12
        m=loan_amount*r*(1+r)**term/((1+r)**term-1)
        st.write("Monthly:",m)

    if b2.button("🤖 Check Risk"):

        e={"salaried":0,"self-employed":1,"informal":2}[emp]

        df=pd.DataFrame({
            'age':[age],'monthly_income':[income],'loan_amount':[loan_amount],
            'interest_rate':[rate],'loan_term':[term],'car_value':[car_value],
            'car_age':[car_age],'mileage':[mileage],
            'previous_loans':[prev_loans],'previous_defaults':[prev_defaults],
            'employment_type':[e]
        })

        df['loan_to_value_ratio']=loan_amount/car_value if car_value else 0
        df['income_to_loan_ratio']=income/loan_amount if loan_amount else 0

        X=df[model.feature_names_in_]
        pred=model.predict(X)[0]
        prob=model.predict_proba(X)[0][1]*100

        st.write("Risk:",prob)

        for r in explain_risk(df):
            st.write(r)

        for s in suggest_improvements(df):
            st.info(s)

# ==============================
# CONTACT (CHAT)
# ==============================
elif page=="Contact":

    msg=st.text_area("Message")

    if st.button("Send"):
        if st.session_state.user:
            supabase.table("messages").insert({
                "user_id": st.session_state.user["id"],
                "name": st.session_state.user["username"],
                "email": st.session_state.user["email"],
                "message": msg,
                "status":"sent"
            }).execute()
            st.rerun()

    if st.session_state.user:

        msgs=supabase.table("messages").select("*").eq(
            "user_id",st.session_state.user["id"]
        ).order("id").execute().data

        for m in msgs:

            msg_id=m["id"]

            if m.get("status")=="seen" and msg_id not in st.session_state.seen_notified:
                st.toast("👁️ Seen")
                st.session_state.seen_notified.add(msg_id)

            status=m.get("status","sent")
            tick="✓" if status=="sent" else "✓✓" if status=="delivered" else "✓✓ 👁️"

            st.write(m["message"],tick)

            if m.get("reply"):
                st.write("Admin:",m["reply"])

# ==============================
# ADMIN
# ==============================
elif page=="Admin Dashboard":

    u=st.text_input("Admin")
    p=st.text_input("Pass",type="password")

    if st.button("Login Admin"):
        if u==ADMIN_USERNAME and check_password(p):
            st.session_state.logged_in=True

    if st.session_state.logged_in:

        data=supabase.table("messages").select("*").execute().data

        for m in data:

            if m.get("status")!="seen":
                supabase.table("messages").update({"status":"seen"}).eq("id",m["id"]).execute()

            st.write(m["message"])

            reply=st.text_input(f"Reply {m['id']}")

            if st.button(f"Send {m['id']}"):
                supabase.table("messages").update({
                    "reply":reply,
                    "replied_at":str(datetime.now())
                }).eq("id",m["id"]).execute()
