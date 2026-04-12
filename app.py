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
    border-radius: 15px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SAFE START (PREVENT BLANK SCREEN)
# ==============================
try:

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

    # ==============================
    # LOAD MODEL
    # ==============================
    @st.cache_resource
    def load_model():
        return pickle.load(open("loan_model.pkl", "rb"))

    model = load_model()

    # ==============================
    # AUTH FUNCTIONS
    # ==============================
    def check_password(password):
        return bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())

    def signup(username, email, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        supabase.table("users").insert({
            "username": username,
            "email": email,
            "password": hashed
        }).execute()

    def login(email, password):
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            user = res.data[0]
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                return user
        return None

    # ==============================
    # ML HELPERS
    # ==============================
    def explain_risk(data):
        reasons = []
        if data['income_to_loan_ratio'].values[0] < 0.3:
            reasons.append("📉 Low income compared to loan")
        if data['loan_to_value_ratio'].values[0] > 0.8:
            reasons.append("🚗 Loan too high vs car value")
        if data['previous_defaults'].values[0] > 0:
            reasons.append("⚠️ Previous defaults")
        if data['previous_loans'].values[0] > 3:
            reasons.append("📊 Too many loans")
        if not reasons:
            reasons.append("✅ Strong financial profile")
        return reasons

    def suggest_improvements(data):
        suggestions = []
        if data['income_to_loan_ratio'].values[0] < 0.3:
            suggestions.append("💡 Increase income or reduce loan")
        if data['loan_to_value_ratio'].values[0] > 0.8:
            suggestions.append("💡 Reduce loan or increase collateral")
        return suggestions

    # ==============================
    # SIDEBAR
    # ==============================
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact", "Admin Dashboard"])

    st.sidebar.title("User Account")

    auth_mode = st.sidebar.selectbox("Account", ["Login", "Sign Up"])

    if auth_mode == "Sign Up":
        username = st.sidebar.text_input("Username")
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Sign Up"):
            signup(username, email, password)
            st.sidebar.success("Account created")

    elif auth_mode == "Login":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            user = login(email, password)
            if user:
                st.session_state.user = user
                st.sidebar.success("Logged in")
            else:
                st.sidebar.error("Invalid credentials")

    if st.session_state.user:
        st.sidebar.write(f"👤 {st.session_state.user['username']}")

    # ==============================
    # HEADER
    # ==============================
    st.title("AI Loan Risk Intelligence Platform")

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
            loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60])

        with col2:
            car_value = st.number_input("Car Value", 0, 1000000, 400000)
            car_age = st.slider("Car Age", 0, 50, 5)
            mileage = st.number_input("Mileage", 0, 500000, 80000)
            previous_loans = st.number_input("Previous Loans", 0, 10, 1)
            previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)

        employment_type = st.selectbox("Employment Type", ["salaried","self-employed","informal"])

        btn1, btn2 = st.columns(2)

        with btn1:
            if st.button("💰 Calculate Repayment"):
                r = interest_rate/100/12
                m = loan_amount*r*(1+r)**loan_term / ((1+r)**loan_term - 1)
                st.write(f"Monthly: {m:,.2f}")
                st.write(f"Weekly: {m/4.33:,.2f}")
                st.write(f"Daily: {m/30:,.2f}")

        with btn2:
            if st.button("🤖 Check Loan Risk"):

                emp = {"salaried":0,"self-employed":1,"informal":2}[employment_type]

                df = pd.DataFrame({
                    'age':[age],'monthly_income':[income],'loan_amount':[loan_amount],
                    'interest_rate':[interest_rate],'loan_term':[loan_term],
                    'car_value':[car_value],'car_age':[car_age],'mileage':[mileage],
                    'previous_loans':[previous_loans],'previous_defaults':[previous_defaults],
                    'employment_type':[emp]
                })

                df['loan_to_value_ratio'] = loan_amount/car_value if car_value else 0
                df['income_to_loan_ratio'] = income/loan_amount if loan_amount else 0

                X = df[model.feature_names_in_]
                pred = model.predict(X)[0]
                prob = model.predict_proba(X)[0][1]*100

                st.write(f"Risk Score: {prob:.2f}%")
                st.progress(int(prob))

                for r in explain_risk(df):
                    st.write(f"• {r}")

                for s in suggest_improvements(df):
                    st.info(s)

    # ==============================
    # CONTACT (CHAT)
    # ==============================
    elif page == "Contact":

        message = st.text_area("Message")

        if st.button("Send Message"):

            if st.session_state.user:
                supabase.table("messages").insert({
                    "user_id": st.session_state.user["id"],
                    "message": message,
                    "timestamp": str(datetime.now())
                }).execute()

                st.success("Message sent")
                st.rerun()
            else:
                st.error("Login first")

        if st.session_state.user:
            msgs = supabase.table("messages") \
                .select("*") \
                .eq("user_id", st.session_state.user["id"]) \
                .order("timestamp") \
                .execute().data

            for m in msgs:
                st.write(f"👤 You: {m['message']}")
                if m.get("reply"):
                    st.write(f"🛠 Admin: {m['reply']}")

    # ==============================
    # ADMIN DASHBOARD
    # ==============================
    elif page == "Admin Dashboard":

        if not st.session_state.logged_in:

            u = st.text_input("Admin Username")
            p = st.text_input("Password", type="password")

            if st.button("Login"):
                if u == ADMIN_USERNAME and check_password(p):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid")

        else:

            data = supabase.table("messages").select("*").execute().data
            df = pd.DataFrame(data)

            st.metric("Total Messages", len(df))

            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["date"] = df["timestamp"].dt.date

                daily = df.groupby("date").size().reset_index(name="count")
                fig = px.line(daily, x="date", y="count")
                st.plotly_chart(fig)

            for m in data:
                st.write(f"User: {m['user_id']}")
                st.write(f"Message: {m['message']}")

                if not m.get("reply"):
                    reply = st.text_input(f"Reply {m['id']}")
                    if st.button(f"Send {m['id']}"):
                        supabase.table("messages").update({
                            "reply": reply,
                            "replied_at": str(datetime.now())
                        }).eq("id", m["id"]).execute()
                        st.rerun()
                else:
                    st.success(f"Reply: {m['reply']}")

except Exception as e:
    st.error(f"🚨 App Error: {e}")
