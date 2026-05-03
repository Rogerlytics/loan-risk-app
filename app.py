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
# 3. CUSTOM CSS – FULL DARK BLUE THEME
# ==============================
st.markdown("""
<style>
/* … (same CSS as 08.py) … */
</style>
""", unsafe_allow_html=True)

# ==============================
# 4. SUPABASE
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
# Removed: ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
# Removed: ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]
# New: only store the admin email for role verification
ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]  # must be set in secrets.toml

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 5. SESSION STATE
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "seen_notified" not in st.session_state:
    st.session_state.seen_notified = set()
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "draft_message" not in st.session_state:
    st.session_state.draft_message = ""
if "risk_result" not in st.session_state:
    st.session_state.risk_result = None
if "repayment_result" not in st.session_state:
    st.session_state.repayment_result = None

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
    # Only used for old admin hash – can be removed entirely now
    pass

def login_user(email: str, password: str):
    """Authenticate regular user via Supabase Auth."""
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
            return {
                "id": res.user.id,
                "email": res.user.email
            }
    except Exception as e:
        st.error(f"Login error: {e}")
    return None

def login_admin(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate admin via Supabase Auth.
    The username field in the form is actually the email.
    Returns user dict if successful and the email matches ADMIN_EMAIL.
    """
    try:
        res = supabase.auth.sign_in_with_password({
            "email": username,  # admin form uses "username" but expects email
            "password": password
        })
        if res.user and res.user.email == ADMIN_EMAIL:
            return {
                "id": res.user.id,
                "email": res.user.email,
                "username": username  # for display
            }
    except Exception as e:
        st.error(f"Admin login error: {e}")
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
            return f"{hours} hour{'s' if hours>1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days>1 else ''} ago"
        else:
            return dt.strftime("%b %d, %I:%M %p")
    except:
        return ts

def get_unread_reply_count(user_id: str) -> int:
    try:
        msgs = supabase.table("messages").select("id, reply, read_by_customer").eq("user_id", user_id).execute().data
        unseen = 0
        for m in msgs:
            if m.get("reply") and not m.get("read_by_customer", False):
                unseen += 1
        return unseen
    except:
        return 0

def mark_messages_as_read(user_id: str):
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
# LOGIN PAGE
# ==============================
def show_login_page():
    st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="small">Sign in to access your account</div>', unsafe_allow_html=True)

        role = st.radio("", ["User", "Administrator"], horizontal=True, label_visibility="collapsed")
        
        if role == "User":
            with st.form("login_form_user", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@example.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    user_data = login_user(email, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            "id": user_data["id"],
                            "email": user_data["email"],
                            "username": email
                        }
                        st.session_state.role = "user"
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
            st.markdown('<p class="login-footer">Don\'t have an account? <a href="#">Sign up</a></p>', unsafe_allow_html=True)
        else:
            with st.form("login_form_admin", clear_on_submit=False):
                username = st.text_input("Admin Email", placeholder="admin@example.com", key="admin_user")
                password = st.text_input("Admin Password", type="password", placeholder="••••••••", key="admin_pass")
                submitted = st.form_submit_button("Sign In as Admin", use_container_width=True)
                if submitted:
                    admin_data = login_admin(username, password)
                    if admin_data:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            "id": admin_data["id"],
                            "email": admin_data["email"],
                            "username": admin_data["username"],
                            "role": "admin"
                        }
                        st.session_state.role = "admin"
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# MAIN APP
# ==============================
def show_main_app():
    st.sidebar.markdown("## 🧭 Navigation")
    
    if st.session_state.role == "user":
        menu = ["📊 Loan Analysis", "💬 Contact"]
    else:
        menu = ["📊 Loan Analysis", "💬 Contact", "⚙️ Admin Dashboard"]
    
    page = st.sidebar.radio("", menu)

    st.sidebar.markdown("---")

    if st.session_state.role == "user":
        unread = get_unread_reply_count(st.session_state.user["id"])
        display_name = st.session_state.user["email"]
        if unread > 0:
            st.sidebar.markdown(f"👤 **{display_name}** 🔴 {unread}")
        else:
            st.sidebar.markdown(f"👤 **{display_name}**")
    else:
        safe_name = st.session_state.user.get("username", st.session_state.user.get("email"))
        st.sidebar.markdown(f"👑 **Admin: {safe_name}**")

    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    st.markdown("<h1 style='text-align:center;color:#F0F4F8'>AI Loan Risk Platform</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-subtitle'>Real-time credit risk evaluation powered by machine learning</div>", unsafe_allow_html=True)

    # ------------------------------
    # LOAN ANALYSIS
    # ------------------------------
    if "Loan Analysis" in page:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Loan Input Details")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", 0, 100, 30, key="age")
            income = st.number_input("Monthly Income", 0, 1000000, 50000, key="income")
            loan_amount = st.number_input("Loan Amount", 0, 1000000, 200000, key="loan_amount")
            interest_rate = st.number_input("Interest Rate (%)", 0.0, 100.0, 12.5, key="interest_rate")
            loan_term = st.selectbox("Loan Term", [12, 24, 36, 48, 60], key="loan_term")
        with col2:
            car_value = st.number_input("Car Value", 0, 1000000, 400000, key="car_value")
            car_age = st.slider("Car Age", 0, 50, 5, key="car_age")
            mileage = st.number_input("Mileage", 0, 500000, 80000, key="mileage")
            previous_loans = st.number_input("Previous Loans", 0, 10, 1, key="previous_loans")
            previous_defaults = st.number_input("Previous Defaults", 0, 10, 0, key="previous_defaults")
        employment_type = st.selectbox("Employment Type", ["salaried","self-employed","informal"], key="employment_type")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Key Financial Metrics")
        k1, k2, k3 = st.columns(3)
        k1.metric("Loan", f"KES {loan_amount:,}")
        k2.metric("Income", f"KES {income:,}")
        k3.metric("Rate", f"{interest_rate}%")
        st.markdown('</div>', unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💰 Calculate Repayment", use_container_width=True):
                if interest_rate > 0 and loan_term > 0 and loan_amount > 0:
                    r = interest_rate / 100 / 12
                    m = loan_amount * r * (1 + r) ** loan_term / ((1 + r) ** loan_term - 1)
                    st.session_state.repayment_result = {
                        "monthly": m,
                        "weekly": m/4.33,
                        "daily": m/30
                    }
                else:
                    st.warning("Please ensure loan amount, interest rate, and loan term are valid.")
                    st.session_state.repayment_result = None

        with col_btn2:
            if st.button("🤖 Check Loan Risk", use_container_width=True):
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

                try:
                    X = df[model.feature_names_in_]
                    pred = model.predict(X)[0]
                    prob = model.predict_proba(X)[0][1] * 100
                    reasons, citations = explain_risk_with_citations(df)
                    suggestions = suggest_improvements(df)
                    st.session_state.risk_result = {
                        "prob": prob,
                        "pred": pred,
                        "reasons": reasons,
                        "citations": citations,
                        "suggestions": suggestions
                    }
                except Exception as e:
                    st.error("Model features mismatch. Please check inputs.")
                    st.session_state.risk_result = None

        col_left_result, col_right_result = st.columns(2)
        with col_left_result:
            if st.session_state.repayment_result:
                res = st.session_state.repayment_result
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("💳 Repayment Breakdown")
                st.write(f"Monthly: KES {res['monthly']:,.2f}")
                st.write(f"Weekly: KES {res['weekly']:,.2f}")
                st.write(f"Daily: KES {res['daily']:,.2f}")
                st.markdown('</div>', unsafe_allow_html=True)

        with col_right_result:
            if st.session_state.risk_result:
                res = st.session_state.risk_result
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("🧠 AI Risk Decision")
                st.write(f"Risk Score: {res['prob']:.2f}%")
                st.progress(int(res['prob']))
                if res['pred'] == 1:
                    st.error("❌ High Risk")
                else:
                    st.success("✅ Low Risk")

                st.subheader("📌 Risk Factors")
                for i, r in enumerate(res['reasons']):
                    src = res['citations'][i]
                    st.write(f"• {r}  `[Source: {src['source']}]`  🔵 Confidence: {src['confidence']}")

                st.subheader("💡 Recommendations")
                for s in res['suggestions']:
                    st.info(s)
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # CONTACT (unchanged from 08.py)
    # ------------------------------
    elif "Contact" in page:
        st.subheader("💬 Customer Support Chat")
        if st.session_state.role == "admin":
            st.info("👑 Admin view: You can see all conversations in the Admin Dashboard.")
        else:
            user_id = st.session_state.user["id"]
            user_email = st.session_state.user.get("email", "")
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
            body {{ margin: 0; background: #0B1B2B; font-family: 'Inter', sans-serif; color: #F0F4F8; display: flex; height: 100%; }}
            .chat-wrapper {{ display: flex; width: 100%; height: 450px; position: relative; }}
            .chat-messages {{ flex: 1; overflow-y: auto; padding: 20px 10px 20px 20px; scrollbar-width: none; -ms-overflow-style: none; }}
            .chat-messages::-webkit-scrollbar {{ display: none; }}
            .chat-messages:hover::-webkit-scrollbar {{ display: block; width: 6px; }}
            .chat-messages:hover::-webkit-scrollbar-thumb {{ background: #2563eb; border-radius: 10px; }}
            .timeline {{ width: 40px; background: transparent; display: flex; flex-direction: column; align-items: center; padding: 20px 5px; position: relative; border-left: 1px dashed #2563eb; }}
            .timeline-dot {{ width: 8px; height: 8px; background: #64748B; border-radius: 50%; margin: 8px 0; cursor: pointer; transition: all 0.2s; position: relative; }}
            .timeline-dot:hover {{ background: #2563eb; transform: scale(1.5); }}
            .timeline-dot.active {{ background: #3b82f6; box-shadow: 0 0 8px #3b82f6; }}
            .timeline-dot::after {{ content: attr(data-date); position: absolute; right: 20px; top: -4px; background: #1A2E44; color: #F0F4F8; padding: 2px 8px; border-radius: 12px; font-size: 10px; white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 0.2s; border: 1px solid #2563eb; }}
            .timeline-dot:hover::after {{ opacity: 1; }}
            .chat-bubble-row {{ display: flex; margin-bottom: 12px; }}
            .chat-bubble-row.user {{ justify-content: flex-end; }}
            .chat-bubble-row.admin {{ justify-content: flex-start; }}
            .chat-bubble {{ max-width: 70%; padding: 12px 16px; border-radius: 18px; font-size: 14px; line-height: 1.4; word-wrap: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
            .user .chat-bubble {{ background: #2563eb; color: white; border-bottom-right-radius: 4px; }}
            .admin .chat-bubble {{ background: #334155; color: #F0F4F8; border-bottom-left-radius: 4px; }}
            .chat-timestamp {{ font-size: 11px; color: #94A3B8; margin-top: 4px; text-align: right; }}
            .user .chat-timestamp {{ color: #E0F2FE; }}
            .reply-badge {{ background: #0B1B2B; color: #60A5FA; border-radius: 16px; padding: 4px 12px; font-size: 12px; margin-bottom: 8px; display: inline-block; border: 1px solid #2563eb; }}
            .read-receipt {{ font-size: 11px; color: #94A3B8; margin-left: 8px; }}
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
                            "name": user_email,
                            "email": user_email,
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
    # ADMIN DASHBOARD (unchanged from 08.py)
    # ------------------------------
    elif "Admin Dashboard" in page:
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
                    body { margin:0; background:#0B1B2B; font-family:'Inter',sans-serif; }
                    .chat-messages { display:flex; flex-direction:column; padding:20px; }
                    .chat-bubble-row { display:flex; margin-bottom:12px; }
                    .chat-bubble-row.user { justify-content:flex-end; }
                    .chat-bubble-row.admin { justify-content:flex-start; }
                    .chat-bubble { max-width:70%; padding:12px 16px; border-radius:18px; font-size:14px; line-height:1.4; word-wrap:break-word; box-shadow:0 1px 2px rgba(0,0,0,0.2); }
                    .user .chat-bubble { background:#2563eb; color:white; border-bottom-right-radius:4px; }
                    .admin .chat-bubble { background:#334155; color:#F0F4F8; border-bottom-left-radius:4px; }
                    .chat-timestamp { font-size:11px; color:#94A3B8; margin-top:4px; text-align:right; }
                    .user .chat-timestamp { color:#E0F2FE; }
                    .reply-badge { background:#0B1B2B; color:#60A5FA; border-radius:16px; padding:4px 12px; font-size:12px; margin-bottom:8px; display:inline-block; border:1px solid #2563eb; }
                    .read-receipt { font-size:11px; color:#94A3B8; margin-left:8px; }
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
