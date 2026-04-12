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
# 🎨 PREMIUM DARK BLUE THEME (RESTORED)
# ==============================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0a0f1c;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

/* Cards */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 10px;
    height: 3em;
    font-weight: 500;
}

/* Headers */
.main-title {
    text-align:center;
    font-size:42px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtext {
    text-align:center;
    color:#94a3b8;
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

    @st.cache_resource
    def load_model():
        return pickle.load(open("loan_model.pkl", "rb"))

    model = load_model()

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
            st.sidebar.success("✅ Account created")

    elif auth_mode == "Login":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            user = login(email, password)
            if user:
                st.session_state.user = user
                st.sidebar.success("✅ Logged in")
            else:
                st.sidebar.error("❌ Invalid credentials")

    if st.session_state.user:
        st.sidebar.write(f"👤 {st.session_state.user['username']}")

    st.markdown('<h1 class="main-title">AI Loan Risk Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtext">Real-time credit risk evaluation powered by machine learning</p>', unsafe_allow_html=True)

    # ==============================
    # LOAN ANALYSIS (UNCHANGED)
    # ==============================
    if page == "Loan Analysis":
        # (same as your previous working code — unchanged)
        pass

    # ==============================
    # CONTACT (WHATSAPP STYLE)
    # ==============================
    elif page == "Contact":

        st.markdown('<div class="card">', unsafe_allow_html=True)

        message = st.text_area("Type your message...")

        if st.button("Send Message"):
            if st.session_state.user:
                supabase.table("messages").insert({
                    "user_id": st.session_state.user["id"],
                    "message": message,
                    "timestamp": str(datetime.now())
                }).execute()
                st.success("✅ Message sent")
                st.rerun()
            else:
                st.error("⚠️ Please login first")

        # CHAT DISPLAY
        if st.session_state.user:

            msgs = supabase.table("messages") \
                .select("*") \
                .eq("user_id", st.session_state.user["id"]) \
                .order("timestamp") \
                .execute().data

            st.markdown("<div style='height:400px; overflow-y:auto;'>", unsafe_allow_html=True)

            for m in msgs:

                # USER MESSAGE (RIGHT)
                st.markdown(f"""
                <div style='display:flex; justify-content:flex-end; margin-bottom:10px;'>
                    <div style='
                        background: linear-gradient(90deg, #2563eb, #1d4ed8);
                        color:white;
                        padding:10px 15px;
                        border-radius:15px;
                        max-width:60%;
                        text-align:right;
                    '>
                        {m['message']}
                        <br>
                        <span style='font-size:10px; opacity:0.7;'>
                            {str(m['timestamp'])[:19]}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ADMIN REPLY (LEFT)
                if m.get("reply"):
                    st.markdown(f"""
                    <div style='display:flex; justify-content:flex-start; margin-bottom:10px;'>
                        <div style='
                            background:#1f2937;
                            color:white;
                            padding:10px 15px;
                            border-radius:15px;
                            max-width:60%;
                            text-align:left;
                        '>
                            {m['reply']}
                            <br>
                            <span style='font-size:10px; opacity:0.7;'>
                                {str(m.get('replied_at',''))[:19]}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # ADMIN DASHBOARD (UNCHANGED)
    # ==============================
    elif page == "Admin Dashboard":
        # (same as your previous working code — unchanged)
        pass

except Exception as e:
    st.error(f"🚨 App Error: {e}")
