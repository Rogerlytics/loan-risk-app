# ==============================
# 1. IMPORTS
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict, Any, List, Tuple
import html
import time

# ==============================
# 2. CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
# 3. DEEPSEEK‑INSPIRED THEME
# ==============================
st.markdown("""
<style>
/* Global reset & fonts */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0b0f15;
    color: #eceef2;
}

/* Hide Streamlit default padding and menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.appview-container .main .block-container {
    padding: 1rem 2rem 1rem 2rem;
    max-width: 100%;
}

/* Cards and containers */
.card {
    background: #151a22;
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid #2a323c;
    margin-bottom: 1.5rem;
}

/* Buttons */
.stButton>button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s;
}
.stButton>button:hover {
    background: #3b82f6;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2);
}

/* Notification badge */
.notification-badge {
    background-color: #ef4444;
    color: white;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 12px;
    margin-left: 8px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #0f141c;
    border-right: 1px solid #2a323c;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* Conversation list (left panel) */
.conversation-list {
    background: transparent;
    border-right: 1px solid #2a323c;
    height: 100%;
    overflow-y: auto;
}
.conversation-item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 4px 0;
    cursor: pointer;
    transition: background 0.15s;
}
.conversation-item:hover {
    background: #1e2630;
}
.conversation-item.active {
    background: #1e3a5f;
    border-left: 3px solid #3b82f6;
}

/* Chat container – DeepSeek style */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: 60vh;
    min-height: 400px;
    background: #0f141c;
    border-radius: 20px;
    border: 1px solid #2a323c;
    overflow: hidden;
    margin-bottom: 20px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px 24px;
    scrollbar-width: thin;
    scrollbar-color: #3a4450 #0f141c;
}
.chat-messages::-webkit-scrollbar {
    width: 6px;
}
.chat-messages::-webkit-scrollbar-track {
    background: #0f141c;
}
.chat-messages::-webkit-scrollbar-thumb {
    background: #3a4450;
    border-radius: 10px;
}
.chat-messages:hover::-webkit-scrollbar-thumb {
    background: #4b5a6a;
}

/* Chat bubbles */
.chat-row {
    display: flex;
    margin-bottom: 16px;
}
.chat-row.user {
    justify-content: flex-end;
}
.chat-row.admin {
    justify-content: flex-start;
}
.chat-bubble {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.5;
    word-wrap: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
.user .chat-bubble {
    background: #2563eb;
    color: white;
    border-bottom-right-radius: 4px;
}
.admin .chat-bubble {
    background: #1e2630;
    color: #e4e8f0;
    border-bottom-left-radius: 4px;
}
.chat-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #1e3a5f;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    margin: 0 12px;
    flex-shrink: 0;
}
.user .chat-avatar { order: 2; }
.admin .chat-avatar { order: 1; }

.chat-meta {
    display: flex;
    align-items: center;
    margin-top: 4px;
    font-size: 11px;
    color: #8a94a3;
}
.user .chat-meta { justify-content: flex-end; }
.read-receipt {
    margin-left: 8px;
    color: #6b7a8a;
}

.reply-badge {
    background: #1e3a5f;
    color: #a0c4ff;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 11px;
    margin-bottom: 6px;
    display: inline-block;
}

/* Input area */
.chat-input-container {
    border-top: 1px solid #2a323c;
    padding: 16px 24px;
    background: #0f141c;
}
.chat-input-container .stTextInput>div>div>input {
    background: #1a222c;
    border: 1px solid #2a323c;
    border-radius: 24px;
    color: white;
    padding: 12px 18px;
}

/* Quick actions */
.quick-actions {
    display: flex;
    gap: 10px;
    margin: 16px 0;
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
# 5. SESSION STATE
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "pending_message" not in st.session_state:
    st.session_state.pending_message = ""

# ==============================
# 6. MODEL
# ==============================
@st.cache_resource
def load_model():
    return pickle.load(open("loan_model.pkl", "rb"))

model = load_model()

# ==============================
# HELPER FUNCTIONS
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

def explain_risk_with_citations(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, str]]]:
    reasons = []
    citations = []
    if df['income_to_loan_ratio'][0] < 0.3:
        reasons.append("📉 Low income vs loan")
        citations.append({"source": "Lending Policy §2.4", "confidence": "High"})
    if df['loan_to_value_ratio'][0] > 0.8:
        reasons.append("🚗 Loan too high vs car value")
        citations.append({"source": "Asset Valuation Guide", "confidence": "Medium"})
    if df['previous_defaults'][0] > 0:
        reasons.append("⚠️ Previous defaults")
        citations.append({"source": "Credit History", "confidence": "High"})
    if not reasons:
        reasons.append("✅ Strong profile")
        citations.append({"source": "All checks passed", "confidence": "High"})
    return reasons, citations

def suggest_improvements(df: pd.DataFrame) -> List[str]:
    suggestions = []
    if df['income_to_loan_ratio'][0] < 0.3:
        suggestions.append("Increase income or reduce loan amount")
    if df['loan_to_value_ratio'][0] > 0.8:
        suggestions.append("Provide additional collateral or reduce loan amount")
    return suggestions

def relative_time(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() // 60)
            return f"{mins} min ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hr ago"
        elif diff < timedelta(days=7):
            return f"{diff.days} d ago"
        else:
            return dt.strftime("%b %d")
    except:
        return ts

def get_unread_reply_count(user_id: int) -> int:
    try:
        msgs = supabase.table("messages").select("id, reply, read_by_customer").eq("user_id", user_id).execute().data
        unseen = 0
        for m in msgs:
            if m.get("reply") and not m.get("read_by_customer", False):
                unseen += 1
        return unseen
    except:
        return 0

def mark_messages_as_read(user_id: int):
    try:
        supabase.table("messages").update({"read_by_customer": True})\
            .eq("user_id", user_id).eq("read_by_customer", False).execute()
    except:
        pass

# ==============================
# 7. SIDEBAR
# ==============================
st.sidebar.title("LoanRisk AI")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Loan Analysis", "Contact", "Admin Dashboard"])

st.sidebar.markdown("---")
st.sidebar.subheader("Account")
email = st.sidebar.text_input("Email", placeholder="user@example.com")
password = st.sidebar.text_input("Password", type="password", placeholder="••••••••")
if st.sidebar.button("Sign In", use_container_width=True):
    user = login(email, password)
    if user:
        st.session_state.user = user
        st.sidebar.success(f"Welcome, {user['username']}")
        time.sleep(0.5)
        st.rerun()
    else:
        st.sidebar.error("Invalid credentials")

if st.session_state.user:
    unread = get_unread_reply_count(st.session_state.user["id"])
    if unread > 0:
        st.sidebar.markdown(f"👤 {st.session_state.user['username']} <span class='notification-badge'>{unread}</span>", unsafe_allow_html=True)
    else:
        st.sidebar.write(f"👤 {st.session_state.user['username']}")

# ==============================
# HEADER
# ==============================
st.markdown("<h1 style='font-weight:600; margin-bottom:0'>AI Loan Risk Platform</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8a94a3; margin-top:0'>Real‑time credit evaluation · Powered by machine learning</p>", unsafe_allow_html=True)

# ==============================
# 8. PAGES
# ==============================

# ------------------------------
# LOAN ANALYSIS
# ------------------------------
if page == "Loan Analysis":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Loan Application Details")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 0, 100, 30)
        income = st.number_input("Monthly Income (KES)", 0, 1000000, 50000)
        loan_amount = st.number_input("Loan Amount (KES)", 0, 1000000, 200000)
        interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5)
        loan_term = st.selectbox("Loan Term (months)", [12, 24, 36, 48, 60])
    with col2:
        car_value = st.number_input("Car Value (KES)", 0, 1000000, 400000)
        car_age = st.slider("Car Age (years)", 0, 50, 5)
        mileage = st.number_input("Mileage (km)", 0, 500000, 80000)
        previous_loans = st.number_input("Previous Loans", 0, 10, 1)
        previous_defaults = st.number_input("Previous Defaults", 0, 10, 0)
    employment_type = st.selectbox("Employment Type", ["salaried","self-employed","informal"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 Key Metrics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Loan Amount", f"KES {loan_amount:,}")
    k2.metric("Monthly Income", f"KES {income:,}")
    k3.metric("Interest Rate", f"{interest_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    col_calc, col_risk = st.columns(2)
    with col_calc:
        if st.button("💰 Calculate Repayment", use_container_width=True):
            r = interest_rate / 100 / 12
            m = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Repayment Breakdown")
            st.write(f"Monthly: KES {m:,.2f}")
            st.write(f"Weekly: KES {m/4.33:,.2f}")
            st.write(f"Daily: KES {m/30:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
    with col_risk:
        if st.button("🤖 Analyze Risk", use_container_width=True):
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
            st.subheader("Risk Assessment")
            st.write(f"**Risk Score:** {prob:.1f}%")
            st.progress(int(prob))
            if pred == 1:
                st.error("❌ High Risk – Application may require review")
            else:
                st.success("✅ Low Risk – Eligible for standard terms")
            reasons, citations = explain_risk_with_citations(df)
            st.markdown("**Key Factors**")
            for i, r in enumerate(reasons):
                src = citations[i]
                st.write(f"• {r}  `[{src['source']}]`  🔵 {src['confidence']}")
            st.markdown("**Recommendations**")
            for s in suggest_improvements(df):
                st.info(s)
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# CONTACT (Customer Support)
# ------------------------------
elif page == "Contact":
    st.subheader("💬 Customer Support")
    if not st.session_state.user:
        st.warning("Please sign in to access chat support.")
    else:
        user_id = st.session_state.user["id"]
        mark_messages_as_read(user_id)

        col_refresh, col_auto = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col_auto:
            auto = st.checkbox("Auto‑refresh (3s)", value=st.session_state.auto_refresh)
            st.session_state.auto_refresh = auto

        try:
            msgs = supabase.table("messages").select("*").eq("user_id", user_id).order("id", desc=False).execute().data
        except Exception as e:
            st.error(f"Could not load messages: {e}")
            msgs = []

        # Chat message display (DeepSeek style)
        if msgs:
            chat_html = '<div class="chat-wrapper"><div class="chat-messages">'
            for msg in msgs:
                timestamp = relative_time(msg.get('timestamp', ''))
                safe_msg = html.escape(msg['message'])
                read_status = "✓✓ Read" if msg.get('read_by_customer') else "✓"
                chat_html += f'''
                <div class="chat-row user">
                    <div class="chat-avatar">U</div>
                    <div style="display:flex; flex-direction:column; align-items:flex-end; max-width:70%;">
                        <div class="chat-bubble">{safe_msg}</div>
                        <div class="chat-meta">
                            <span>{timestamp}</span>
                            <span class="read-receipt">{read_status}</span>
                        </div>
                    </div>
                </div>
                '''
                if msg.get('reply'):
                    reply_time = relative_time(msg.get('replied_at', ''))
                    safe_reply = html.escape(msg['reply'])
                    chat_html += f'''
                    <div class="chat-row admin">
                        <div class="chat-avatar">A</div>
                        <div style="display:flex; flex-direction:column; max-width:70%;">
                            <span class="reply-badge">Support replied</span>
                            <div class="chat-bubble">{safe_reply}</div>
                            <div class="chat-meta"><span>{reply_time}</span></div>
                        </div>
                    </div>
                    '''
            chat_html += '</div></div>'
            components.html(chat_html, height=500, scrolling=True)
        else:
            st.info("💬 No messages yet. Start a conversation below.")

        # Quick reply buttons
        st.markdown("**Quick replies:**")
        cols = st.columns(4)
        with cols[0]:
            if st.button("📊 Loan status", use_container_width=True):
                st.session_state.pending_message = "What's my loan status?"
                st.rerun()
        with cols[1]:
            if st.button("💰 Payment help", use_container_width=True):
                st.session_state.pending_message = "I need payment assistance"
                st.rerun()
        with cols[2]:
            if st.button("📄 Documents", use_container_width=True):
                st.session_state.pending_message = "How do I upload documents?"
                st.rerun()
        with cols[3]:
            if st.button("🔄 Reset password", use_container_width=True):
                st.session_state.pending_message = "I forgot my password"
                st.rerun()

        # Message input form (functional)
        with st.form(key="message_form", clear_on_submit=True):
            default_msg = st.session_state.get("pending_message", "")
            col_input, col_button = st.columns([5, 1])
            with col_input:
                msg = st.text_input("Message", value=default_msg, placeholder="Type your message...", label_visibility="collapsed")
            with col_button:
                submitted = st.form_submit_button("📤 Send", use_container_width=True)
            if submitted and msg.strip():
                try:
                    supabase.table("messages").insert({
                        "user_id": user_id,
                        "name": st.session_state.user["username"],
                        "email": st.session_state.user["email"],
                        "message": msg,
                        "status": "sent",
                        "timestamp": datetime.now().isoformat(),
                        "read_by_customer": False,
                        "delivered": True
                    }).execute()
                    st.session_state.pending_message = ""
                    st.success("Message sent!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to send: {e}")

        if st.session_state.auto_refresh:
            time.sleep(3)
            st.rerun()

# ------------------------------
# ADMIN DASHBOARD
# ------------------------------
elif page == "Admin Dashboard":
    st.subheader("Admin Panel")
    if not st.session_state.logged_in:
        with st.expander("Admin Authentication", expanded=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                if u == ADMIN_USERNAME and check_password(p):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        col_refresh, col_auto = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col_auto:
            auto = st.checkbox("Auto‑refresh (3s)", value=st.session_state.auto_refresh, key="admin_auto")
            st.session_state.auto_refresh = auto

        try:
            data = supabase.table("messages").select("*").order("timestamp", desc=False).execute().data
        except Exception as e:
            st.error(f"Error: {e}")
            data = []

        if not data:
            st.info("No conversations yet.")
        else:
            users_df = pd.DataFrame(data)
            unique_users = users_df[['user_id', 'name', 'email']].drop_duplicates(subset=['user_id']).to_dict('records')

            col_left, col_right = st.columns([1, 2.5])
            with col_left:
                st.markdown("#### Conversations")
                for usr in unique_users:
                    active = (st.session_state.selected_user_id == usr['user_id'])
                    btn_label = f"{usr['name']} ({usr['email']})"
                    if active:
                        btn_label = "🔹 " + btn_label
                    if st.button(btn_label, key=f"user_{usr['user_id']}", use_container_width=True):
                        st.session_state.selected_user_id = usr['user_id']
                        st.rerun()

            with col_right:
                if st.session_state.selected_user_id is None and unique_users:
                    st.session_state.selected_user_id = unique_users[0]['user_id']
                if st.session_state.selected_user_id:
                    user_msgs = [m for m in data if m['user_id'] == st.session_state.selected_user_id]
                    user_name = next((u['name'] for u in unique_users if u['user_id'] == st.session_state.selected_user_id), "User")
                    st.markdown(f"#### Chat with {user_name}")

                    if user_msgs:
                        chat_html = '<div class="chat-wrapper"><div class="chat-messages">'
                        for msg in user_msgs:
                            ts = relative_time(msg.get('timestamp', ''))
                            safe_msg = html.escape(msg['message'])
                            read = "✓✓ Read" if msg.get('read_by_customer') else "✓"
                            chat_html += f'''
                            <div class="chat-row user">
                                <div class="chat-avatar">U</div>
                                <div style="display:flex; flex-direction:column; align-items:flex-end; max-width:70%;">
                                    <div class="chat-bubble">{safe_msg}</div>
                                    <div class="chat-meta"><span>{ts}</span><span class="read-receipt">{read}</span></div>
                                </div>
                            </div>
                            '''
                            if msg.get('reply'):
                                rts = relative_time(msg.get('replied_at', ''))
                                safe_rep = html.escape(msg['reply'])
                                chat_html += f'''
                                <div class="chat-row admin">
                                    <div class="chat-avatar">A</div>
                                    <div style="display:flex; flex-direction:column; max-width:70%;">
                                        <span class="reply-badge">You replied</span>
                                        <div class="chat-bubble">{safe_rep}</div>
                                        <div class="chat-meta"><span>{rts}</span></div>
                                    </div>
                                </div>
                                '''
                        chat_html += '</div></div>'
                        components.html(chat_html, height=450, scrolling=True)
                    else:
                        st.info("No messages yet.")

                    # Admin reply form
                    with st.form(key=f"reply_form_{st.session_state.selected_user_id}", clear_on_submit=True):
                        col_input, col_button = st.columns([5, 1])
                        with col_input:
                            reply_text = st.text_input("Reply", placeholder="Write a reply...", label_visibility="collapsed")
                        with col_button:
                            submitted = st.form_submit_button("📤 Send")
                        if submitted and reply_text.strip():
                            unreplied = [m for m in user_msgs if not m.get('reply')]
                            if unreplied:
                                try:
                                    supabase.table("messages").update({
                                        "reply": reply_text,
                                        "replied_at": datetime.now().isoformat(),
                                        "status": "replied"
                                    }).eq("id", unreplied[-1]["id"]).execute()
                                    st.success("Reply sent!")
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                            else:
                                st.warning("No unreplied messages.")

            # Metrics
            st.markdown("---")
            st.metric("Total Messages", len(data))
            if not users_df.empty:
                users_df["timestamp"] = pd.to_datetime(users_df["timestamp"], errors='coerce')
                daily = users_df.groupby(users_df["timestamp"].dt.date).size().reset_index(name="count")
                if not daily.empty:
                    fig = px.line(daily, x="timestamp", y="count", title="Messages Over Time")
                    st.plotly_chart(fig, use_container_width=True)

        if st.session_state.auto_refresh:
            time.sleep(3)
            st.rerun()
