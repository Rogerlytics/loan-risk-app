# ==============================
# views/admin_dashboard.py
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import time
from services.supabase_service import (
    get_all_messages,
    send_reply,
    get_audit_logs,
    get_all_users,
    update_user_role,
    log_action
)
from utils.helpers import relative_time
from config.settings import require_role


def _empty_state(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div style="
        background:linear-gradient(145deg,#111827,#0b1220);
        border:1px dashed #1f2a36; border-radius:16px;
        padding:48px 24px; text-align:center; margin-top:12px;">
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

    tab1, tab2, tab3 = st.tabs([
        "Conversations", "User Management", "Audit Log"
    ])

    # ════════════════════════════
    # TAB 1 — Conversations
    # ════════════════════════════
    with tab1:
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

        if not data:
            _empty_state(
                "💬", "No Conversations Yet",
                "When users send messages they will appear here."
            )
        else:
            users_df     = pd.DataFrame(data)
            unique_users = users_df[
                ['user_id', 'name', 'email']
            ].drop_duplicates(subset=['user_id'])
            user_list    = unique_users.to_dict('records')

            col_users, col_chat = st.columns([1, 2])

            with col_users:
                st.markdown(
                    '<div style="color:#60A5FA; font-weight:600; '
                    'margin-bottom:12px;">Conversations</div>',
                    unsafe_allow_html=True
                )
                for usr in user_list:
                    user_msgs = [
                        m for m in data
                        if m['user_id'] == usr['user_id']
                    ]
                    unread = sum(
                        1 for m in user_msgs
                        if m.get('reply') and
                        not m.get('read_by_customer', False)
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

            with col_chat:
                if st.session_state.selected_user_id is None \
                        and user_list:
                    st.session_state.selected_user_id = \
                        user_list[0]['user_id']

                if not st.session_state.selected_user_id:
                    _empty_state(
                        "👈", "No Conversation Selected",
                        "Select a user from the left."
                    )
                else:
                    user_msgs = [
                        m for m in data
                        if m['user_id'] ==
                        st.session_state.selected_user_id
                    ]
                    selected_email = next(
                        (u['email'] for u in user_list
                         if u['user_id'] ==
                         st.session_state.selected_user_id),
                        "User"
                    )
                    st.markdown(
                        f'<div style="color:#F0F4F8; font-weight:600; '
                        f'margin-bottom:12px;">'
                        f'Chat with {selected_email}</div>',
                        unsafe_allow_html=True
                    )

                    if not user_msgs:
                        _empty_state(
                            "📭", "No Messages Yet",
                            "This user has not sent any messages yet."
                        )
                    else:
                        chat_html_parts = ['''
                        <html><head><meta charset="UTF-8"><style>
                        body{margin:0;background:#0e1117;
                            font-family:"Inter",sans-serif;}
                        .chat-messages{display:flex;flex-direction:column;
                            padding:20px;overflow-y:auto;height:430px;}
                        .chat-bubble-row{display:flex;margin-bottom:12px;}
                        .chat-bubble-row.user{justify-content:flex-end;}
                        .chat-bubble-row.admin{justify-content:flex-start;}
                        .chat-bubble{max-width:70%;padding:12px 16px;
                            border-radius:18px;font-size:14px;
                            line-height:1.4;word-wrap:break-word;}
                        .user .chat-bubble{background:#2563eb;color:white;
                            border-bottom-right-radius:4px;}
                        .admin .chat-bubble{background:#1f2a36;
                            color:#F0F4F8;border-bottom-left-radius:4px;}
                        .chat-timestamp{font-size:11px;color:#94A3B8;
                            margin-top:4px;}
                        .reply-badge{background:#0e1117;color:#60A5FA;
                            border-radius:16px;padding:4px 12px;
                            font-size:12px;margin-bottom:8px;
                            display:inline-block;border:1px solid #2563eb;}
                        .read-receipt{font-size:11px;color:#94A3B8;
                            margin-left:8px;}
                        </style></head><body>
                        <div class="chat-messages">''']

                        for msg in user_msgs:
                            timestamp    = relative_time(
                                msg.get('timestamp', '')
                            )
                            safe_message = msg['message']
                            read_status  = (
                                "Read" if msg.get('read_by_customer')
                                else "Delivered"
                            )
                            chat_html_parts.append(f'''
                            <div class="chat-bubble-row user">
                                <div style="display:flex;
                                    flex-direction:column;
                                    align-items:flex-end;max-width:70%;">
                                    <div class="chat-bubble">
                                        {safe_message}</div>
                                    <div style="display:flex;
                                        align-items:center;">
                                        <div class="chat-timestamp">
                                            {timestamp}</div>
                                        <div class="read-receipt">
                                            {read_status}</div>
                                    </div>
                                </div>
                            </div>''')
                            if msg.get('reply'):
                                reply_time = relative_time(
                                    msg.get('replied_at', '')
                                )
                                safe_reply = msg['reply']
                                chat_html_parts.append(f'''
                            <div class="chat-bubble-row admin">
                                <div style="display:flex;
                                    flex-direction:column;max-width:70%;">
                                    <div class="reply-badge">Reply</div>
                                    <div class="chat-bubble">
                                        {safe_reply}</div>
                                    <div class="chat-timestamp">
                                        {reply_time}</div>
                                </div>
                            </div>''')

                        chat_html_parts.append('</div></body></html>')
                        components.html(
                            "".join(chat_html_parts),
                            height=450, scrolling=True
                        )

                        with st.form(
                            key=f"reply_form_"
                                f"{st.session_state.selected_user_id}",
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
                                        m for m in user_msgs
                                        if not m.get('reply')
                                    ]
                                    if unreplied:
                                        with st.spinner("Sending..."):
                                            send_reply(
                                                supabase,
                                                unreplied[-1]["id"],
                                                reply_text.strip()
                                            )
                                        admin = st.session_state.user
                                        log_action(
                                            supabase,
                                            admin["id"], admin["email"],
                                            "admin_reply",
                                            f"Replied to {selected_email}"
                                        )
                                        st.success("Reply sent!")
                                        st.rerun()
                                    else:
                                        st.warning(
                                            "No unreplied messages "
                                            "for this user."
                                        )

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
                    "📈", "No Chart Data Yet",
                    "Message activity will appear here once "
                    "users start chatting."
                )

        if st.session_state.auto_refresh:
            time.sleep(3)
            st.rerun()

    # ════════════════════════════
    # TAB 2 — User Management
    # ════════════════════════════
    with tab2:
        st.markdown(
            '<div class="section-heading">User Management</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="color:#94A3B8; font-size:13px; '
            'margin-bottom:20px;">Promote users to admin or demote '
            'admins back to user. You cannot change your own role.'
            '</div>',
            unsafe_allow_html=True
        )

        with st.spinner("Loading users..."):
            all_users = get_all_users(supabase)

        if not all_users:
            _empty_state(
                "👥", "No Users Found",
                "No users have signed up yet."
            )
        else:
            current_admin_id = st.session_state.user["id"]

            for usr in all_users:
                uid     = usr["id"]
                email   = usr.get("email", "Unknown")
                role    = usr.get("role", "user")
                is_self = uid == current_admin_id

                if role == "admin":
                    badge_bg, badge_fg = "#7c3aed22", "#a78bfa"
                    badge_border = "#7c3aed44"
                else:
                    badge_bg, badge_fg = "#0369a122", "#38bdf8"
                    badge_border = "#0369a144"

                col_email, col_badge, col_action = st.columns([3, 1, 1])

                with col_email:
                    self_label = " (you)" if is_self else ""
                    st.markdown(
                        f'<div style="color:#F0F4F8; font-size:14px; '
                        f'padding-top:8px;">{email}'
                        f'<span style="color:#64748B; font-size:12px;">'
                        f'{self_label}</span></div>',
                        unsafe_allow_html=True
                    )

                with col_badge:
                    st.markdown(
                        f'<div style="background:{badge_bg}; '
                        f'color:{badge_fg}; '
                        f'border:1px solid {badge_border}; '
                        f'border-radius:20px; padding:6px 12px; '
                        f'font-size:11px; font-weight:700; '
                        f'text-transform:uppercase; text-align:center; '
                        f'margin-top:4px;">{role}</div>',
                        unsafe_allow_html=True
                    )

                with col_action:
                    if is_self:
                        st.markdown(
                            '<div style="color:#64748B; font-size:12px; '
                            'padding-top:10px; text-align:center;">'
                            'Your account</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        new_role  = "user" if role == "admin" else "admin"
                        btn_label = (
                            "Demote to User"
                            if role == "admin"
                            else "Promote to Admin"
                        )
                        if st.button(
                            btn_label,
                            key=f"role_btn_{uid}",
                            use_container_width=True
                        ):
                            with st.spinner("Updating role..."):
                                success, message = update_user_role(
                                    supabase, uid, new_role
                                )
                            if success:
                                admin = st.session_state.user
                                log_action(
                                    supabase,
                                    admin["id"], admin["email"],
                                    "role_changed",
                                    f"{email}: {role} → {new_role}"
                                )
                                st.success(
                                    f"{email} is now {new_role.upper()}."
                                )
                                st.rerun()
                            else:
                                st.error(message)

                st.markdown(
                    '<hr style="border-color:#1f2a36; margin:8px 0;">',
                    unsafe_allow_html=True
                )

    # ════════════════════════════
    # TAB 3 — Audit Log
    # ════════════════════════════
    with tab3:
        st.markdown(
            '<div class="section-heading">Audit Log</div>',
            unsafe_allow_html=True
        )

        with st.spinner("Loading audit log..."):
            logs = get_audit_logs(supabase, limit=100)

        if not logs:
            _empty_state(
                "📋", "No Audit Logs Yet",
                "User actions will be recorded here."
            )
        else:
            action_colours = {
                "login":                ("#dcfce7", "#166534"),
                "logout":               ("#fee2e2", "#991b1b"),
                "signup":               ("#dbeafe", "#1e40af"),
                "risk_check":           ("#fef3c7", "#92400e"),
                "repayment_calculated": ("#ede9fe", "#5b21b6"),
                "message_sent":         ("#e0f2fe", "#075985"),
                "admin_reply":          ("#fce7f3", "#9d174d"),
                "role_changed":         ("#fef9c3", "#713f12"),
            }
            for log in logs:
                action  = log.get("action", "unknown")
                email   = log.get("email", "unknown")
                details = log.get("details", "")
                ts      = relative_time(log.get("created_at", ""))
                bg, fg  = action_colours.get(
                    action, ("#1f2a36", "#94A3B8")
                )
                st.markdown(f"""
                <div style="background:linear-gradient(
                        145deg,#111827,#0b1220);
                    border:1px solid #1f2a36;border-radius:12px;
                    padding:12px 16px;margin-bottom:8px;
                    display:flex;align-items:center;gap:12px;">
                    <div style="background:{bg};color:{fg};
                        border-radius:20px;padding:3px 10px;
                        font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.5px;
                        white-space:nowrap;min-width:140px;
                        text-align:center;">
                        {action.replace("_", " ")}</div>
                    <div style="flex:1;">
                        <div style="color:#F0F4F8;font-size:13px;
                            font-weight:600;">{email}</div>
                        <div style="color:#94A3B8;font-size:12px;">
                            {details}</div>
                    </div>
                    <div style="color:#64748B;font-size:11px;
                        white-space:nowrap;">{ts}</div>
                </div>
                """, unsafe_allow_html=True)
