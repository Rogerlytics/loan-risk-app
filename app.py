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
# 🎨 PREMIUM DARK BLUE THEME
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
    font-weight: 500;
}

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
        r = []
        if df['income_to_loan_ratio'][0] < 0.3:
            r.append("📉 Low income vs loan")
        if df['loan_to_value_ratio'][0] > 0.8:
            r.append("🚗 Loan too high vs car value")
        if df['previous_defaults'][0] > 0:
            r.append("⚠️ Previous defaults")
        if not r:
            r.append("✅ Strong profile")
        return r

    def suggest_improvements(df):
        s = []
        if df['income_to_loan_ratio'][0] < 0.3:
            s.append("Increase income or reduce loan")
        if df['loan_to_value_ratio'][0] > 0.8:
            s.append("Increase collateral")
        return s

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

    st.markdown('<h1 class="main-title">AI Loan Risk Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtext">Real-time credit risk evaluation powered by ML</p>', unsafe_allow_html=True)

    if page == "Loan Analysis":
        # (UNCHANGED — omitted for brevity, remains exactly same in your app)
        pass

    elif page == "Contact":

        st.markdown('<div class="card">', unsafe_allow_html=True)

        msg = st.text_area("Message")

        if st.button("Send"):
            if st.session_state.user:
                supabase.table("messages").insert({
                    "user_id": st.session_state.user["id"],
                    "name": st.session_state.user["username"],
                    "email": st.session_state.user["email"],
                    "message": msg,
                    "status": "sent"
                }).execute()
                st.rerun()

        if st.session_state.user:

            # ✅ STEP 1 — SESSION TRACKING
            if "seen_notified" not in st.session_state:
                st.session_state.seen_notified = set()

            sort_order = st.selectbox("Sort Messages", ["Oldest First", "Newest First"])
            desc = True if sort_order == "Newest First" else False

            msgs = supabase.table("messages").select("*").eq(
                "user_id", st.session_state.user["id"]
            ).order("id", desc=desc).execute().data

            st.markdown("### 💬 Chat Conversation")

            for m in msgs:

                # ✅ STEP 2 — SEEN DETECTION
                msg_id = m["id"]
                if m.get("status") == "seen" and msg_id not in st.session_state.seen_notified:
                    st.toast("👁️ Your message was seen")
                    st.session_state.seen_notified.add(msg_id)

                user_name = m.get("name", "User")
                timestamp = m.get("timestamp", "")

                status = m.get("status", "sent")
                if status == "sent":
                    tick = "✓"
                elif status == "delivered":
                    tick = "✓✓"
                else:
                    tick = "✓✓ 👁️"

                st.markdown(f"""
                <div style='display:flex; justify-content:flex-end; margin:8px 0'>
                    <div style='background:#2563eb; color:white; padding:10px 14px;
                                border-radius:12px; max-width:70%; text-align:right'>
                        <div style='font-size:12px; opacity:0.8'>{user_name}</div>
                        <div>{m['message']}</div>
                        <div style='font-size:10px; opacity:0.6'>{timestamp} {tick}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if m.get("reply"):
                    reply_time = m.get("replied_at", "")

                    st.markdown(f"""
                    <div style='display:flex; justify-content:flex-start; margin:8px 0'>
                        <div style='background:#1f2937; color:white; padding:10px 14px;
                                    border-radius:12px; max-width:70%; text-align:left'>
                            <div style='font-size:12px; opacity:0.8'>Admin</div>
                            <div>{m['reply']}</div>
                            <div style='font-size:10px; opacity:0.6'>{reply_time}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div id='bottom'></div>", unsafe_allow_html=True)
            st.markdown("""
            <script>
            var element = document.getElementById("bottom");
            if (element) {
                element.scrollIntoView({behavior: "smooth"});
            }
            </script>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Admin Dashboard":
        # (UNCHANGED — remains exactly as your previous version)
        pass

except Exception as e:
    st.error(e)
