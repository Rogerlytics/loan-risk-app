# ==============================
# pages/admin_dashboard.py
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import html
import time
from services.supabase_service import get_all_messages, send_reply
from utils.helpers import relative_time


def show_admin_dashboard(supabase):
    if st.session_state.role != "admin":
        st.error("Access denied 🚫")
        st.stop()

    st.subheader("📊 Admin Control Panel")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        auto = st.checkbox("Auto-refresh (3s)", value=st.session_state.auto_refresh, key="admin_auto")
        st.session_state.auto_refresh = auto

    data = get_all_messages(supabase)

    if not data:
        st.info("No messages yet.")
    else:
        st.markdown("### 💬 Customer Conversations")
        users_df = pd.DataFrame(data)
        unique_users = users_df[['user_id', 'name', 'email']].drop_duplicates(subset=['user_id'])
        user_list = unique_users.to_dict('records')

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
                selected_user_name = next(
                    (usr['name'] for usr in user_list if usr['user_id'] == st.session_state.selected_user_id),
                    "User"
                )
                st.markdown(f"#### Chat with {selected_user_name}")

                chat_html_parts = ['''<html><head><meta charset="UTF-8"><style>
                body { margin:0; background:#0B1B2B; font-family:"Inter",sans-serif; }
                .chat-messages { display:flex; flex-direction:column; padding:20px; }
                .chat-bubble-row { display:flex; margin-bottom:12px; }
                .chat-bubble-row.user { justify-content:flex-end; }
                .chat-bubble-row.admin { justify-content:flex-start; }
                .chat-bubble { max-width:70%; padding:12px 16px; border-radius:18px; font-size:14px; line-height:1.4; word-wrap:break-word; }
                .user .chat-bubble { background:#2563eb; color:white; border-bottom-right-radius:4px; }
                .admin .chat-bubble { background:#334155; color:#F0F4F8; border-bottom-left-radius:4px; }
                .chat-timestamp { font-size:11px; color:#94A3B8; margin-top:4px; }
                .reply-badge { background:#0B1B2B; color:#60A5FA; border-radius:16px; padding:4px 12px; font-size:12px; margin-bottom:8px; display:inline-block; border:1px solid #2563eb; }
                .read-receipt { font-size:11px; color:#94A3B8; margin-left:8px; }
                </style></head><body><div class="chat-messages">''']

                for msg in user_msgs:
                    timestamp = relative_time(msg.get('timestamp', ''))
                    safe_message = html.escape(msg['message'])
                    read_status = "✓✓ Read" if msg.get('read_by_customer') else "✓ Delivered"
                    chat_html_parts.append(f'''
                    <div class="chat-bubble-row user">
                        <div style="display:flex; flex-direction:column; align-items:flex-end; max-width:70%;">
                            <div class="chat-bubble">{safe_message}</div>
                            <div style="display:flex; align-items:center;">
                                <div class="chat-timestamp">{timestamp}</div>
                                <div class="read-receipt">{read_status}</div>
                            </div>
                        </div>
                    </div>''')
                    if msg.get('reply'):
                        reply_time = relative_time(msg.get('replied_at', ''))
                        safe_reply = html.escape(msg['reply'])
                        chat_html_parts.append(f'''
                    <div class="chat-bubble-row admin">
                        <div style="display:flex; flex-direction:column; max-width:70%;">
                            <div class="reply-badge">Reply</div>
                            <div class="chat-bubble">{safe_reply}</div>
                            <div class="chat-timestamp">{reply_time}</div>
                        </div>
                    </div>''')

                chat_html_parts.append('</div></body></html>')
                components.html("".join(chat_html_parts), height=450, scrolling=True)

                with st.form(key=f"reply_form_{st.session_state.selected_user_id}", clear_on_submit=True):
                    col_input, col_button = st.columns([5, 1])
                    with col_input:
                        reply_text = st.text_input("", placeholder="Write a reply...", label_visibility="collapsed")
                    with col_button:
                        submitted = st.form_submit_button("📤 Send")
                    if submitted and reply_text.strip():
                        unreplied = [m for m in user_msgs if not m.get('reply')]
                        if unreplied:
                            send_reply(supabase, unreplied[-1]["id"], reply_text)
                            st.success("Reply sent!")
                            st.rerun()
                        else:
                            st.warning("No unreplied messages for this user.")
            else:
                st.info("Select a user from the left to view conversation.")

        st.markdown("---")
        st.metric("Total Messages", len(data))
        users_df["timestamp"] = pd.to_datetime(users_df["timestamp"], errors='coerce')
        daily = users_df.groupby(users_df["timestamp"].dt.date).size().reset_index(name="count")
        if not daily.empty:
            fig = px.line(daily, x="timestamp", y="count", title="Messages Over Time")
            st.plotly_chart(fig, use_container_width=True)

    if st.session_state.auto_refresh:
        time.sleep(3)
        st.rerun()
