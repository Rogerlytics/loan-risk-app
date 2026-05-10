# ==============================
# pages/admin_dashboard.py
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import time
from services.supabase_service import get_all_messages, send_reply
from utils.helpers import relative_time
from config.settings import require_role


def _empty_state(icon: str, title: str, subtitle: str):
    """Reusable empty state card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, #111827, #0b1220);
        border: 1px dashed #1f2a36;
        border-radius: 16px;
        padding: 48px 24px;
        text-align: center;
        margin-top: 12px;
    ">
        <div style="font-size:40px; margin-bottom:12px;">{icon}</div>
        <div style="color:#F0F4F8; font-size:18px; font-weight:600;
                    margin-bottom:8px;">{title}</div>
        <div style="color:#94A3B8; font-size:14px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def show_admin_dashboard(supabase):
    require_role(["admin"])

    st.markdown(
        '<div class="section-heading">Admin Control Panel</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    with col2:
        auto = st.checkbox(
            "Auto-refresh (3s)",
            value=st.session_state.auto_refresh,
            key="admin_auto"
        )
        st.session_state.auto_refresh = auto

    with st.spinner("Loading conversations..."):
        data = get_all_messages(supabase)

    # ── No messages at all ──
    if not data:
        _empty_state(
            "💬",
            "No Conversations Yet",
            "When users send messages they will appear here."
        )
        return

    st.markdown(
        '<div class="section-heading">Customer Conversations</div>',
        unsafe_allow_html=True
    )

    users_df   = pd.DataFrame(data)
    unique_users = users_df[
        ['user_id', 'name', 'email']
    ].drop_duplicates(subset=['user_id'])
    user_list  = unique_users.to_dict('records')

    col_users, col_chat = st.columns([1, 2])

    # ── User list ──
    with col_users:
        st.markdown(
            '<div style="color:#60A5FA; font-weight:600; '
            'margin-bottom:12px;">Conversations</div>',
            unsafe_allow_html=True
        )
        for usr in user_list:
            user_msgs = [
                m for m in data if m['user_id'] == usr['user_id']
            ]
            unread = sum(
                1 for m in user_msgs
                if m.get('reply') and not m.get('read_by_customer', False)
            )
            label = usr['email']
            if unread > 0:
                label += f"  ({unread} unread)"
            if st.button(
                label,
                key=f"user_{usr['user_id']}",
                use_container_width=True
            ):
                st.session_state.selected_user_id = usr['user_id']
                st.rerun()

    # ── Chat panel ──
    with col_chat:
        if st.session_state.selected_user_id is None and user_list:
            st.session_state.selected_user_id = user_list[0]['user_id']

        if not st.session_state.selected_user_id:
            _empty_state(
                "👈",
                "No Conversation Selected",
                "Select a user from the left to view their conversation."
            )
        else:
            user_msgs = [
                m for m in data
                if m['user_id'] == st.session_state.selected_user_id
            ]
            selected_email = next(
                (u['email'] for u in user_list
                 if u['user_id'] == st.session_state.selected_user_id),
                "User"
            )
            st.markdown(
                f'<div style="color:#F0F4F8; font-weight:600; '
                f'margin-bottom:12px;">Chat with {selected_email}</div>',
                unsafe_allow_html=True
            )

            # ── No messages in this conversation ──
            if not user_msgs:
                _empty_state(
                    "📭",
                    "No Messages Yet",
                    "This user has not sent any messages yet."
                )
            else:
                chat_html_parts = ['''
                <html><head><meta charset="UTF-8"><style>
                body { margin:0; background:#0e1117;
                       font-family:"Inter",sans-serif; }
                .chat-messages { display:flex; flex-direction:column;
                                 padding:20px; overflow-y:auto;
                                 height:430px; }
                .chat-bubble-row { display:flex; margin-bottom:12px; }
                .chat-bubble-row.user { justify-content:flex-end; }
                .chat-bubble-row.admin { justify-content:flex-start; }
                .chat-bubble { max-width:70%; padding:12px 16px;
                               border-radius:18px; font-size:14px;
                               line-height:1.4; word-wrap:break-word; }
                .user .chat-bubble  { background:#2563eb; color:white;
                                      border-bottom-right-radius:4px; }
                .admin .chat-bubble { background:#1f2a36; color:#F0F4F8;
                                      border-bottom-left-radius:4px; }
                .chat-timestamp { font-size:11px; color:#94A3B8;
                                  margin-top:4px; }
                .reply-badge { background:#0e1117; color:#60A5FA;
                               border-radius:16px; padding:4px 12px;
                               font-size:12px; margin-bottom:8px;
                               display:inline-block;
                               border:1px solid #2563eb; }
                .read-receipt { font-size:11px; color:#94A3B8;
                                margin-left:8px; }
                </style></head><body>
                <div class="chat-messages">''']

                for msg in user_msgs:
                    timestamp    = relative_time(msg.get('timestamp', ''))
                    safe_message = msg['message']
                    read_status  = (
                        "Read" if msg.get('read_by_customer')
                        else "Delivered"
                    )
                    chat_html_parts.append(f'''
                    <div class="chat-bubble-row user">
                        <div style="display:flex; flex-direction:column;
                                    align-items:flex-end; max-width:70%;">
                            <div class="chat-bubble">{safe_message}</div>
                            <div style="display:flex; align-items:center;">
                                <div class="chat-timestamp">{timestamp}</div>
                                <div class="read-receipt">{read_status}</div>
                            </div>
                        </div>
                    </div>''')
                    if msg.get('reply'):
                        reply_time = relative_time(msg.get('replied_at', ''))
                        safe_reply = msg['reply']
                        chat_html_parts.append(f'''
                    <div class="chat-bubble-row admin">
                        <div style="display:flex; flex-direction:column;
                                    max-width:70%;">
                            <div class="reply-badge">Reply</div>
                            <div class="chat-bubble">{safe_reply}</div>
                            <div class="chat-timestamp">{reply_time}</div>
                        </div>
                    </div>''')

                chat_html_parts.append('</div></body></html>')
                components.html(
                    "".join(chat_html_parts), height=450, scrolling=True
                )

                # Reply form
                with st.form(
                    key=f"reply_form_{st.session_state.selected_user_id}",
                    clear_on_submit=True
                ):
                    col_input, col_button = st.columns([5, 1])
                    with col_input:
                        reply_text = st.text_input(
                            "",
                            placeholder="Write a reply...",
                            label_visibility="collapsed"
                        )
                    with col_button:
                        submitted = st.form_submit_button("Send")

                    if submitted:
                        if not reply_text.strip():
                            st.warning("Reply cannot be empty.")
                        else:
                            unreplied = [
                                m for m in user_msgs if not m.get('reply')
                            ]
                            if unreplied:
                                with st.spinner("Sending reply..."):
                                    send_reply(
                                        supabase,
                                        unreplied[-1]["id"],
                                        reply_text.strip()
                                    )
                                st.success("Reply sent!")
                                st.rerun()
                            else:
                                st.warning(
                                    "No unreplied messages for this user."
                                )

    # ── Stats ──
    st.markdown("---")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Messages", len(data))
    col_m2.metric("Total Users",    len(user_list))
    col_m3.metric(
        "Unreplied",
        sum(1 for m in data if not m.get('reply'))
    )

    users_df["timestamp"] = pd.to_datetime(
        users_df["timestamp"], errors='coerce'
    )
    daily = users_df.groupby(
        users_df["timestamp"].dt.date
    ).size().reset_index(name="count")

    if not daily.empty:
        fig = px.line(
            daily, x="timestamp", y="count",
            title="Messages Over Time",
            labels={"timestamp": "Date", "count": "Messages"}
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e6edf3"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        _empty_state(
            "📈",
            "No Chart Data Yet",
            "Message activity will appear here once users start chatting."
        )

    if st.session_state.auto_refresh:
        time.sleep(3)
        st.rerun()
