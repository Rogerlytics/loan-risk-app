# ==============================
# 1. IMPORTS
# ==============================
import streamlit as st
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client
from typing import Optional, Dict, Any, List

# ==============================
# 2. CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 3. THEME (Original clean style)
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
.subtitle {
    text-align:center;
    color:#94a3b8;
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 4. SUPABASE
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 5. SESSION
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None

# ==============================
# 6. MODEL
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ==============================
# FUNCTIONS
# ==============================
def check_password(p: str) -> bool:
    return bcrypt.checkpw(p.encode(), ADMIN_PASSWORD_HASH.encode())

def login(email: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            u = res.data[0]
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                return u
    except Exception as e:
        st.error(f"Login error: {e}")
    return None

def explain_risk(df: pd.DataFrame) -> List[str]:
    reasons = []
    if df['income_to_loan_ratio'][0] < 0.3:
        reasons.append("📉 Low income vs loan")
    if df['loan_to_value_ratio'][0] > 0.8:
        reasons.append("🚗 Loan too high vs car value")
    if df['previous_defaults'][0] > 0:
        reasons.append("⚠️ Previous defaults")
    if not reasons:
        reasons.append("✅ Strong profile")
    return reasons

def suggest_improvements(df: pd.DataFrame) -> List[str]:
    suggestions = []
    if df['income_to_loan_ratio'][0] < 0.3:
        suggestions.append("Increase income or reduce loan")
    if df['loan_to_value_ratio'][0] > 0.8:
        suggestions.append("Increase collateral")
    return suggestions

def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %I:%M %p")
    except:
        return ts

# ==============================
# 7. SIDEBAR
# ==============================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Loan Analysis", "Contact", "Admin Dashboard"]
)

# USER LOGIN
st.sidebar.title("User Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    user = login(email, password)
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
st.markdown("<h1 style='text-align:center;color:#3b82f6'>AI Loan Risk Platform</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Real-time credit risk evaluation powered by machine learning</div>", unsafe_allow_html=True)

# ==============================
# 8. PAGES
# ==============================

# ------------------------------
# LOAN ANALYSIS
# ------------------------------
if page == "Loan Analysis":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Input Details")

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
    st.markdown('</div>', unsafe_allow_html=True)

    # KPI
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Key Financial Metrics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan", f"KES {loan_amount:,}")
    k2.metric("Income", f"KES {income:,}")
    k3.metric("Rate", f"{interest_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    b1, b2 = st.columns(2)

    # REPAYMENT
    with b1:
        if st.button("💰 Calculate Repayment"):
            r = interest_rate / 100 / 12
            m = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💳 Repayment Breakdown")
            st.write(f"Monthly: KES {m:,.2f}")
            st.write(f"Weekly: KES {m/4.33:,.2f}")
            st.write(f"Daily: KES {m/30:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

    # RISK
    with b2:
        if st.button("🤖 Check Loan Risk"):

            emp = {"salaried":0,"self-employed":1,"informal":2}[employment_type]

            df = pd.DataFrame({
                'age':[age],'monthly_income':[income],'loan_amount':[loan_amount],
                'interest_rate':[interest_rate],'loan_term':[loan_term],
                'car_value':[car_value],'car_age':[car_age],'mileage':[mileage],
                'previous_loans':[previous_loans],'previous_defaults':[previous_defaults],
                'employment_type':[emp]
            })

            df['loan_to_value_ratio'] = loan_amount / car_value if car_value else 0
            df['income_to_loan_ratio'] = income / loan_amount if loan_amount else 0

            X = df[model.feature_names_in_]
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1] * 100

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🧠 AI Risk Decision")
            st.write(f"Risk Score: {prob:.2f}%")
            st.progress(int(prob))

            if pred == 1:
                st.error("❌ High Risk")
            else:
                st.success("✅ Low Risk")

            st.subheader("📌 Risk Factors")
            for r in explain_risk(df):
                st.write(f"• {r}")

            st.subheader("💡 Recommendations")
            for s in suggest_improvements(df):
                st.info(s)

            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# CONTACT (Customer Support) - Original version
# ------------------------------
elif page == "Contact":

    st.subheader("💬 Customer Support Chat")

    if not st.session_state.user:
        st.warning("Login first")
    else:
        # Message input at top (original placement)
        msg = st.text_input("Type your message...")

        if st.button("Send"):
            if msg.strip():
                try:
                    supabase.table("messages").insert({
                        "user_id": st.session_state.user["id"],
                        "name": st.session_state.user["username"],
                        "email": st.session_state.user["email"],
                        "message": msg,
                        "status": "sent",
                        "timestamp": datetime.now().isoformat()
                    }).execute()
                    st.success("Message sent!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to send: {e}")

        # Display chat history
        st.markdown("### Your Conversation")
        try:
            msgs = supabase.table("messages").select("*").eq(
                "user_id", st.session_state.user["id"]
            ).order("id", desc=False).execute().data

            for m in msgs:
                with st.container():
                    st.markdown(f"**You:** {m['message']}")
                    if m.get("reply"):
                        st.markdown(f"**Support:** {m['reply']}")
                    st.caption(f"_{format_timestamp(m.get('timestamp', ''))}_")
                    st.divider()
        except Exception as e:
            st.error("Could not load messages.")

# ------------------------------
# ADMIN DASHBOARD - Original version
# ------------------------------
elif page == "Admin Dashboard":

    st.subheader("📊 Admin Control Panel")

    # Admin Login
    with st.expander("🔐 Admin Authentication", expanded=not st.session_state.logged_in):
        u = st.text_input("Admin Username")
        p = st.text_input("Password", type="password")
        if st.button("Login Admin"):
            if u == ADMIN_USERNAME and check_password(p):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    if st.session_state.logged_in:

        try:
            data = supabase.table("messages").select("*").execute().data
        except Exception as e:
            st.error(f"Failed to fetch messages: {e}")
            data = []

        if not data:
            st.info("No messages yet.")
        else:
            df = pd.DataFrame(data)
            st.metric("Total Messages", len(df))

            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
                daily = df.groupby(df["timestamp"].dt.date).size().reset_index(name="count")
                if not daily.empty:
                    fig = px.line(daily, x="timestamp", y="count")
                    st.plotly_chart(fig, use_container_width=True)

            # Display each message with reply input
            for m in data:
                st.write(f"**{m['name']} ({m['email']})**: {m['message']}")
                if m.get('reply'):
                    st.write(f"↳ Reply: {m['reply']}")

                reply = st.text_input(f"Reply to message {m['id']}", key=f"reply_{m['id']}")
                if st.button(f"Send Reply {m['id']}", key=f"btn_{m['id']}"):
                    if reply.strip():
                        try:
                            supabase.table("messages").update({
                                "reply": reply,
                                "replied_at": datetime.now().isoformat(),
                                "status": "replied"
                            }).eq("id", m["id"]).execute()
                            st.success("Reply sent!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")
                st.divider()
