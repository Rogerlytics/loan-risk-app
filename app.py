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
# 3. THEME & STYLES (Premium Dark UI + App)
# ==============================
st.markdown("""
<style>
/* Override Streamlit's default top padding */
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 1rem !important;
}

/* Global */
html, body {
    background-color: #0e1117;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}

/* --- Login Page --- */
.title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    text-align: center;
    margin-bottom: 8px;
}
.subtitle {
    color: #A0AEC0;
    text-align: center;
    margin-bottom: 40px;
    font-size: 16px;
}
.section {
    font-size: 22px;
    font-weight: 600;
    text-align: center;
    color: white;
    margin-bottom: 8px;
}
.small {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 24px;
    font-size: 14px;
}

/* Radio buttons horizontal & centered */
div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 12px;
    margin-bottom: 24px;
    justify-content: center;
}
div[role="radiogroup"] label {
    flex: 1;
    min-width: 120px;  /* Ensures "Administrator" fits */
    padding: 12px 16px;
    background: #1a222c;
    border: 1px solid #2a3748;
    border-radius: 12px;
    color: #8a94a3;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    margin: 0 !important;
    white-space: nowrap;  /* Prevents text wrapping */
}
div[role="radiogroup"] label[data-selected="true"] {
    background: #1e3a5f;
    border-color: #3b82f6;
    color: white;
}
div[role="radiogroup"] input {
    display: none !important;
}

/* Input fields */
.stTextInput > div > div > input {
    background: #1a222c;
    border: 1px solid #2a3748;
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    width: 100% !important;
    box-sizing: border-box;
}

/* Sign In button */
.stButton > button {
    background: #1f77ff;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 12px 24px;
    font-weight: 600;
    width: 100%;
    transition: all 0.2s;
    height: 45px;
}
.stButton > button:hover {
    background: #155edb;
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(31, 119, 255, 0.3);
}

/* Sign up link */
.login-footer {
    text-align: center;
    margin-top: 16px;
    color: #8a94a3;
}
.login-footer a {
    color: #3b82f6;
    text-decoration: none;
}

/* Error messages */
.stAlert {
    background: transparent;
    color: #ef4444;
    border: none;
    padding: 8px 0;
}

/* --- App styles (unchanged) --- */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}
.app-subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 20px;
}
.notification-badge {
    background-color: #ef4444;
    color: white;
    border-radius: 50%;
    padding: 2px 8px;
    font-size: 12px;
    margin-left: 8px;
}
.unified-chat {
    background: #0b1220;
    border-radius: 20px;
    border: 1px solid #1f2a36;
    overflow: hidden;
    margin-bottom: 20px;
}
.chat-input-container {
    padding: 16px 20px;
    background: #0e1622;
    border-top: 1px solid #1f2a36;
    margin-top: 0;
}
.chat-input-container .stTextInput > div > div > input {
    background: #1a2330;
    border: 1px solid #2a3748;
    border-radius: 24px;
    color: white;
    padding: 12px 18px;
}
.chat-input-container .stButton > button {
    border-radius: 24px;
    height: auto;
    padding: 10px 20px;
}
.chat-input-container .stForm {
    margin-bottom: 0;
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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None  # "user" or "admin"
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "draft_message" not in st.session_state:
    st.session_state.draft_message = ""

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

def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            u = res.data[0]
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                return u
    except Exception as e:
        st.error(f"Login error: {e}")
    return None

def login_admin(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and check_password(password)

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
            return f"{hours} hour{'s' if hours>1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days>1 else ''} ago"
        else:
            return dt.strftime("%b %d, %I:%M %p")
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
# LOGOUT FUNCTION
# ==============================
def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

# ==============================
# LOGIN PAGE (Premium Centered UI)
# ==============================
def show_login_page():
    # Page title and subtitle
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

    # Centered card using columns
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="small">Sign in to access your account</div>', unsafe_allow_html=True)

        # Role selector (horizontal radio)
        role = st.radio("", ["User", "Administrator"], horizontal=True, label_visibility="collapsed")
        
        if role == "User":
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            if st.button("Sign In", use_container_width=True, key="signin_user"):
                user_data = login_user(email, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.session_state.role = "user"
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            st.markdown('<p class="login-footer">Don\'t have an account? <a href="#">Sign up</a></p>', unsafe_allow_html=True)
        else:
            username = st.text_input("Admin Username", placeholder="admin", key="admin_user")
            password = st.text_input("Admin Password", type="password", placeholder="••••••••", key="admin_pass")
            if st.button("Sign In as Admin", use_container_width=True, key="signin_admin"):
                if login_admin(username, password):
                    st.session_state.authenticated = True
                    st.session_state.user = {"username": username, "role": "admin"}
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")

# ==============================
# MAIN APP (after login)
# ==============================
def show_main_app():
    # Sidebar
    st.sidebar.title("Navigation")
    if st.session_state.role == "user":
        page = st.sidebar.radio("Go to", ["Loan Analysis", "Contact"])
    else:
        page = st.sidebar.radio("Go to", ["Admin Dashboard"])

    st.sidebar.markdown("---")
    if st.session_state.role == "user":
        unread = get_unread_reply_count(st.session_state.user["id"])
        if unread > 0:
            st.sidebar.markdown(f"👤 {st.session_state.user['username']} <span class='notification-badge'>{unread}</span>", unsafe_allow_html=True)
        else:
            st.sidebar.write(f"👤 {st.session_state.user['username']}")
    else:
        st.sidebar.write(f"👑 Admin: {st.session_state.user['username']}")
    
    if st.sidebar.button("Logout", use_container_width=True):
        logout()

    # Header
    st.markdown("<h1 style='text-align:center;color:#3b82f6'>AI Loan Risk Platform</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-subtitle'>Real-time credit risk evaluation powered by machine learning</div>", unsafe_allow_html=True)

    # ------------------------------
    # LOAN ANALYSIS (User only)
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

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Key Financial Metrics")
        k1, k2, k3 = st.columns(3)
        k1.metric("Loan", f"KES {loan_amount:,}")
        k2.metric("Income", f"KES {income:,}")
        k3.metric("Rate", f"{interest_rate}%")
        st.markdown('</div>', unsafe_allow_html=True)

        b1, b2 = st.columns(2)
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
                reasons, citations = explain_risk_with_citations(df)
                for i, r in enumerate(reasons):
                    src = citations[i]
                    st.write(f"• {r}  `[Source: {src['source']}]`  🔵 Confidence: {src['confidence']}")
                st.subheader("💡 Recommendations")
                for s in suggest_improvements(df):
                    st.info(s)
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # CONTACT (User only)
    # ------------------------------
    elif page == "Contact":
        st.subheader("💬 Customer Support Chat")
        user_id = st.session_state.user["id"]
        mark_messages_as_read(user_id)

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            auto = st.checkbox("Auto-refresh (3s)", value=st.session_state.auto_refresh)
            st.session_state.auto_refresh = auto

        try:
            msgs = supabase.table("messages").select("*").eq("user_id", user_id).order("id", desc=False).execute().data
        except Exception as e:
            st.error(f"Failed to load messages: {e}")
            msgs = []

        st.markdown("**Quick Actions**")
        cols = st.columns(4)
        with cols[0]:
            if st.button("📊 Loan Status", use_container_width=True):
                st.session_state.draft_message = "What's my loan application status?"
                st.rerun()
        with cols[1]:
            if st.button("💰 Payment Help", use_container_width=True):
                st.session_state.draft_message = "I need help with my payment"
                st.rerun()
        with cols[2]:
            if st.button("📄 Upload Docs", use_container_width=True):
                st.session_state.draft_message = "I need to upload documents"
                st.rerun()
        with cols[3]:
            if st.button("🔄 Reset Password", use_container_width=True):
                st.session_state.draft_message = "I forgot my password"
                st.rerun()

        date_groups = {}
        for i, msg in enumerate(msgs):
            try:
                dt = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                date_key = dt.strftime("%Y-%m-%d")
                display = dt.strftime("%b %d")
            except:
                date_key = "unknown"
                display = "Unknown"
            if date_key not in date_groups:
                date_groups[date_key] = {"display": display, "first_index": i}
        timeline_data = [{"date": k, "display": v["display"], "index": v["first_index"]} for k, v in date_groups.items()]

        chat_html = f'''
        <html><head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{ margin: 0; background: #0b1220; font-family: 'Inter', sans-serif; color: #e6edf3; display: flex; height: 100%; }}
        .chat-wrapper {{ display: flex; width: 100%; height: 450px; position: relative; }}
        .chat-messages {{ flex: 1; overflow-y: auto; padding: 20px 10px 20px 20px; scrollbar-width: none; -ms-overflow-style: none; }}
        .chat-messages::-webkit-scrollbar {{ display: none; }}
        .chat-messages:hover::-webkit-scrollbar {{ display: block; width: 6px; }}
        .chat-messages:hover::-webkit-scrollbar-thumb {{ background: #3a4450; border-radius: 10px; }}
        .timeline {{ width: 40px; background: transparent; display: flex; flex-direction: column; align-items: center; padding: 20px 5px; position: relative; border-left: 1px dashed #2a3748; }}
        .timeline-dot {{ width: 8px; height: 8px; background: #4b5a6a; border-radius: 50%; margin: 8px 0; cursor: pointer; transition: all 0.2s; position: relative; }}
        .timeline-dot:hover {{ background: #3b82f6; transform: scale(1.5); }}
        .timeline-dot.active {{ background: #3b82f6; box-shadow: 0 0 8px #3b82f6; }}
        .timeline-dot::after {{ content: attr(data-date); position: absolute; right: 20px; top: -4px; background: #1e2630; color: #e4e8f0; padding: 2px 8px; border-radius: 12px; font-size: 10px; white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 0.2s; border: 1px solid #2a3748; }}
        .timeline-dot:hover::after {{ opacity: 1; }}
        .chat-bubble-row {{ display: flex; margin-bottom: 12px; }}
        .chat-bubble-row.user {{ justify-content: flex-end; }}
        .chat-bubble-row.admin {{ justify-content: flex-start; }}
        .chat-bubble {{ max-width: 70%; padding: 12px 16px; border-radius: 18px; font-size: 14px; line-height: 1.4; word-wrap: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
        .user .chat-bubble {{ background: #0084ff; color: white; border-bottom-right-radius: 4px; }}
        .admin .chat-bubble {{ background: #3a3b3c; color: #e4e6eb; border-bottom-left-radius: 4px; }}
        .chat-timestamp {{ font-size: 11px; color: #8a8d91; margin-top: 4px; text-align: right; }}
        .user .chat-timestamp {{ color: #b0d4ff; }}
        .reply-badge {{ background: #1d4ed8; color: white; border-radius: 16px; padding: 4px 12px; font-size: 12px; margin-bottom: 8px; display: inline-block; }}
        .read-receipt {{ font-size: 11px; color: #8a8d91; margin-left: 8px; }}
        </style>
        </head>
        <body>
        <div class="chat-wrapper">
            <div class="chat-messages" id="chatMessages">
        '''
        for msg in msgs:
            timestamp = relative_time(msg.get('timestamp', ''))
            safe_message = html.escape(msg['message'])
            read_status = "✓✓ Read" if msg.get('read_by_customer') else "✓ Delivered"
            chat_html += f'''
            <div class="chat-bubble-row user" data-message-id="{msg['id']}">
                <div style="display:flex; flex-direction:column; align-items:flex-end; max-width:70%;">
                    <div class="chat-bubble">{safe_message}</div>
                    <div style="display:flex; align-items:center;">
                        <div class="chat-timestamp">{timestamp}</div>
                        <div class="read-receipt">{read_status}</div>
                    </div>
                </div>
            </div>
            '''
            if msg.get('reply'):
                reply_time = relative_time(msg.get('replied_at', ''))
                safe_reply = html.escape(msg['reply'])
                chat_html += f'''
                <div class="chat-bubble-row admin" data-message-id="reply_{msg['id']}">
                    <div style="display:flex; flex-direction:column; max-width:70%;">
                        <div class="reply-badge">Reply</div>
                        <div class="chat-bubble">{safe_reply}</div>
                        <div class="chat-timestamp">{reply_time}</div>
                    </div>
                </div>
                '''
        chat_html += '''
            </div>
            <div class="timeline" id="timeline">
        '''
        for item in timeline_data:
            chat_html += f'<div class="timeline-dot" data-date="{item["display"]}" data-index="{item["index"]}"></div>'
        chat_html += '''
            </div>
        </div>
        <script>
        (function() {
            const chatContainer = document.getElementById('chatMessages');
            const timeline = document.getElementById('timeline');
            const dots = timeline.querySelectorAll('.timeline-dot');
            const messageRows = chatContainer.querySelectorAll('.chat-bubble-row');
            
            function scrollToMessageIndex(index) {
                if (index >= 0 && index < messageRows.length) {
                    messageRows[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
            
            dots.forEach(dot => {
                dot.addEventListener('click', function(e) {
                    const idx = parseInt(this.getAttribute('data-index'));
                    scrollToMessageIndex(idx);
                    dots.forEach(d => d.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        })();
        </script>
        </body>
        </html>
        '''

        st.markdown('<div class="unified-chat">', unsafe_allow_html=True)
        components.html(chat_html, height=470, scrolling=False)
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        with st.form(key="message_form", clear_on_submit=True):
            col_input, col_button = st.columns([5, 1])
            with col_input:
                msg = st.text_input(
                    "Message",
                    value=st.session_state.draft_message,
                    placeholder="Type your message...",
                    label_visibility="collapsed",
                    key="chat_input"
                )
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
                    st.session_state.draft_message = ""
                    st.success("Message sent!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to send: {e}")
            else:
                st.session_state.draft_message = msg
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.auto_refresh:
            time.sleep(3)
            st.rerun()

    # ------------------------------
    # ADMIN DASHBOARD
    # ------------------------------
    elif page == "Admin Dashboard":
        st.subheader("📊 Admin Control Panel")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            auto = st.checkbox("Auto-refresh (3s)", value=st.session_state.auto_refresh, key="admin_auto")
            st.session_state.auto_refresh = auto

        try:
            data = supabase.table("messages").select("*").order("timestamp", desc=False).execute().data
        except Exception as e:
            st.error(f"Failed to fetch messages: {e}")
            data = []

        if not data:
            st.info("No messages yet.")
        else:
            st.markdown("### 💬 Customer Conversations")
            users_df = pd.DataFrame(data)
            if not users_df.empty:
                unique_users = users_df[['user_id', 'name', 'email']].drop_duplicates(subset=['user_id'])
                user_list = unique_users.to_dict('records')
            else:
                user_list = []

            col_users, col_chat = st.columns([1, 2])

            with col_users:
                st.markdown("**Conversations**")
                for usr in user_list:
                    if st.button(f"👤 {usr['name']} ({usr['email']})", key=f"user_{usr['user_id']}"):
                        st.session_state.selected_user_id = usr['user_id']
                        st.rerun()

            with col_chat:
                if st.session_state.selected_user_id is None and user_list:
                    st.session_state.selected_user_id = user_list[0]['user_id']

                if st.session_state.selected_user_id:
                    user_msgs = [m for m in data if m['user_id'] == st.session_state.selected_user_id]
                    selected_user_name = next((usr['name'] for usr in user_list if usr['user_id'] == st.session_state.selected_user_id), "User")
                    st.markdown(f"#### Chat with {selected_user_name}")

                    chat_html = '''
                    <html><head><meta charset="UTF-8"><style>
                    body { margin:0; background:#0b1220; font-family:'Inter',sans-serif; }
                    .chat-messages { display:flex; flex-direction:column; padding:20px; }
                    .chat-bubble-row { display:flex; margin-bottom:12px; }
                    .chat-bubble-row.user { justify-content:flex-end; }
                    .chat-bubble-row.admin { justify-content:flex-start; }
                    .chat-bubble { max-width:70%; padding:12px 16px; border-radius:18px; font-size:14px; line-height:1.4; word-wrap:break-word; box-shadow:0 1px 2px rgba(0,0,0,0.1); }
                    .user .chat-bubble { background:#0084ff; color:white; border-bottom-right-radius:4px; }
                    .admin .chat-bubble { background:#3a3b3c; color:#e4e6eb; border-bottom-left-radius:4px; }
                    .chat-timestamp { font-size:11px; color:#8a8d91; margin-top:4px; text-align:right; }
                    .user .chat-timestamp { color:#b0d4ff; }
                    .reply-badge { background:#1d4ed8; color:white; border-radius:16px; padding:4px 12px; font-size:12px; margin-bottom:8px; display:inline-block; }
                    .read-receipt { font-size:11px; color:#8a8d91; margin-left:8px; }
                    </style></head><body><div class="chat-messages">
                    '''
                    for msg in user_msgs:
                        timestamp = relative_time(msg.get('timestamp', ''))
                        safe_message = html.escape(msg['message'])
                        read_status = "✓✓ Read" if msg.get('read_by_customer') else "✓ Delivered"
                        chat_html += f'''
                        <div class="chat-bubble-row user">
                            <div style="display:flex; flex-direction:column; align-items:flex-end; max-width:70%;">
                                <div class="chat-bubble">{safe_message}</div>
                                <div style="display:flex; align-items:center;">
                                    <div class="chat-timestamp">{timestamp}</div>
                                    <div class="read-receipt">{read_status}</div>
                                </div>
                            </div>
                        </div>
                        '''
                        if msg.get('reply'):
                            reply_time = relative_time(msg.get('replied_at', ''))
                            safe_reply = html.escape(msg['reply'])
                            chat_html += f'''
                            <div class="chat-bubble-row admin">
                                <div style="display:flex; flex-direction:column; max-width:70%;">
                                    <div class="reply-badge">Reply</div>
                                    <div class="chat-bubble">{safe_reply}</div>
                                    <div class="chat-timestamp">{reply_time}</div>
                                </div>
                            </div>
                            '''
                    chat_html += '</div></body></html>'
                    components.html(chat_html, height=450, scrolling=True)

                    with st.form(key=f"reply_form_{st.session_state.selected_user_id}", clear_on_submit=True):
                        col_input, col_button = st.columns([5, 1])
                        with col_input:
                            reply_text = st.text_input("", placeholder="Write a reply...", label_visibility="collapsed")
                        with col_button:
                            submitted = st.form_submit_button("📤 Send")
                        if submitted and reply_text.strip():
                            unreplied = [m for m in user_msgs if not m.get('reply')]
                            if unreplied:
                                msg_to_reply = unreplied[-1]
                                try:
                                    supabase.table("messages").update({
                                        "reply": reply_text,
                                        "replied_at": datetime.now().isoformat(),
                                        "status": "replied"
                                    }).eq("id", msg_to_reply["id"]).execute()
                                    st.success("Reply sent!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to send reply: {e}")
                            else:
                                st.warning("No unreplied messages for this user.")
                else:
                    st.info("Select a user from the left to view conversation.")

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

# ==============================
# MAIN ENTRY POINT
# ==============================
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
