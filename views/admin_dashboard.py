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
    get_total_message_count,
    log_action
)
from utils.helpers import relative_time
from config.settings import require_role


# ── Shared chat CSS — text-align:left, bubbles fill width ──
CHAT_CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
html,body { height:100%; background:#0e1117;
            font-family:"Inter",-apple-system,sans-serif; }
.chat-messages { overflow-y:auto; padding:16px;
    display:flex; flex-direction:column; gap:10px;
    scroll-behavior:smooth; height:100%; }
.chat-messages::-webkit-scrollbar { width:4px; }
.chat-messages::-webkit-scrollbar-track { background:transparent; }
.chat-messages::-webkit-scrollbar-thumb { background:#334155;
    border-radius:4px; }
.row-user  { display:flex; justify-content:flex-end; }
.row-admin { display:flex; justify-content:flex-start; }
.bubble-wrap { display:flex; flex-direction:column; max-width:78%; }
.row-user  .bubble-wrap { align-items:flex-end; }
.row-admin .bubble-wrap { align-items:flex-start; }
.bubble { padding:10px 14px; border-radius:18px;
          font-size:14px; line-height:1.55;
          word-break:break-word; word-wrap:break-word;
          white-space:pre-wrap;
          text-align:left;
          width:100%; }
.bubble-user  { background:#2563eb; color:#fff;
                border-bottom-right-radius:4px; }
.bubble-admin { background:#1e293b; color:#F0F4F8;
                border-bottom-left-radius:4px;
                border:1px solid #334155; }
.meta { font-size:11px; color:#64748B;
        margin-top:3px; padding:0 4px; }
.admin-label { font-size:11px; color:#60A5FA; font-weight:600;
    margin-bottom:3px; padding:0 4px; }
.receipt { font-size:11px; color:#64748B; margin-left:6px; }
.empty-state { display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    height:200px; color:#64748B; text-align:center; }
"""


def _build_chat_html(messages, height=440):
    rows = ""
    if not messages:
        rows = """
        <div class="empty-state">
            <div style="font-size:32px;margin-bottom:8px;">📭</div>
            <div>No messages yet.</div>
        </div>"""
    else:
        for msg in messages:
            ts           = relative_time(msg.get('timestamp', ''))
            safe_message = msg['message']
            receipt      = "✓✓" if msg.get('read_by_customer') else "✓"
            rows += f"""
            <div class="row-user">
                <div class="bubble-wrap">
                    <div class="bubble bubble-user">{safe_message}</div>
                    <div class="meta" style="text-align:right;">
                        {ts}
                        <span class="receipt">{receipt}</span>
                    </div>
                </div>
            </div>"""
            if msg.get('reply'):
                reply_ts   = relative_time(msg.get('replied_at', ''))
                safe_reply = msg['reply']
                rows += f"""
            <div class="row-admin">
                <div class="bubble-wrap">
                    <div class="admin-label">You (Admin)</div>
                    <div class="bubble bubble-admin">{safe_reply}</div>
                    <div class="meta">{reply_ts}</div>
                </div>
            </div>"""

    return f"""
    <!DOCTYPE html><html><head>
    <meta charset="UTF-8">
    <style>
    {CHAT_CSS}
    body {{ height:{height}px; overflow:hidden; }}
    </style>
    </head><body>
    <div class="chat-messages" id="chatMessages">
        {rows}
        <div id="chatEnd"></div>
    </div>
    <script>
        const el = document.getElementById("chatEnd");
        if (el) el.scrollIntoView({{ behavior:"smooth" }});
    </script>
    </body></html>
    """


def _empty_state(icon, title, subtitle):
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#111827,#0b1220);
        border:1px dashed #1f2a36;border-radius:16px;
        padding:48px 24px;text-align:center;margin-top:12px;">
        <div style="font-size:40px;margin-bottom:12px;">{icon}</div>
        <div style="color:#F0F4F8;font-size:18px;font-weight:600;
                    margin-bottom:8px;">{title}</div>
        <div style="color:#94A3B8;font-size:14px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def show_admin_dashboard(supabase):
    require_role(["admin"])

    st.markdown(
        '<div class="section-heading">Admin Control Panel</div>',
        unsafe_allow_html=True
    )

    if "admin_last_count" not in st.session_state:
        st.session_state.admin_last_count = 0

    tab1, tab2, tab3 = st.tabs([
        "Conversations", "User Management", "Audit Log"
    ])

    # ════════════════════════════
    # TAB 1 — Conversations
    # ════════════════════════════
    with tab1:
        if st.session_state.auto_refresh:
            dot_col = "#22c55e"
            dot_txt = "Live"
            tog_lbl = "Turn OFF"
            pulse   = "animation:pulse 1.5s infinite;"
        else:
            dot_col = "#64748B"
            dot_txt = "Off"
            tog_lbl = "Turn ON"
            pulse   = ""

        st.markdown(f"""
        <style>
        @keyframes pulse {{
            0%  {{ box-shadow:0 0 0 0 rgba(34,197,94,0.6); }}
            70% {{ box-shadow:0 0 0 6px rgba(34,197,94,0); }}
            100%{{ box-shadow:0 0 0 0 rgba(34,197,94,0); }}
        }}
        .admin-live-bar {{ display:flex;align-items:center;gap:10px;
                           padding:4px 0;margin-bottom:6px; }}
        .admin-live-dot {{ width:10px;height:10px;border-radius:50%;
                           background:{dot_col};{pulse}flex-shrink:0; }}
        .admin-live-lbl {{ color:{dot_col};font-size:13px;font-weight:600; }}
        </style>
        <div class="admin-live-bar">
            <div class="admin-live-dot"></div>
            <span class="admin-live-lbl">{dot_txt}</span>
        </div>
        """, unsafe_allow_html=True)

        col_r, col_t, col_sp = st.columns([1, 1, 4])
        with col_r:
            if st.button("Refresh", use_container_width=True,
                         key="admin_refresh"):
                st.rerun()
        with col_t:
            if st.button(tog_lbl, use_container_width=True,
                         key="admin_live_toggle"):
                st.session_state.auto_refresh = \
                    not st.session_state.auto_refresh
                st.rerun()

        with st.spinner("Loading conversations..."):
            data = get_all_messages(supabase)

        st.session_state.admin_last_count = len(data)

        if not data:
            _empty_state("💬", "No Conversations Yet",
                         "When users send messages they will appear here.")
        else:
            users_df     = pd.DataFrame(data)
            unique_users = users_df[
                ['user_id', 'name', 'email']
            ].drop_duplicates(subset=['user_id'])
            user_list    = unique_users.to_dict('records')

            col_users, col_chat = st.columns([1, 2])

            with col_users:
                st.markdown(
                    '<div style="color:#60A5FA;font-weight:600;'
                    'font-size:13px;margin-bottom:10px;'
                    'text-transform:uppercase;letter-spacing:0.05em;">'
                    'Conversations</div>',
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
                    is_selected = (
                        st.session_state.selected_user_id == usr['user_id']
                    )
                    bg     = "#1e3a5f" if is_selected else "#0f1e30"
                    border = "#2563eb" if is_selected else "#1e293b"

                    unread_badge = (
                        f'<span style="background:#ef4444;color:white;'
                        f'border-radius:50%;padding:1px 6px;'
                        f'font-size:10px;margin-left:6px;">'
                        f'{unread}</span>'
                    ) if unread > 0 else ""

                    last_msg = ""
                    if user_msgs:
                        raw = user_msgs[-1]['message']
                        last_msg = raw[:32] + "..." if len(raw) > 32 else raw

                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};
                        border-radius:12px;padding:10px 14px;
                        margin-bottom:6px;">
                        <div style="color:#F0F4F8;font-size:13px;
                                    font-weight:600;">
                            {usr['email']}{unread_badge}
                        </div>
                        <div style="color:#64748B;font-size:12px;
                            margin-top:2px;white-space:nowrap;
                            overflow:hidden;text-overflow:ellipsis;">
                            {last_msg}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        "Open",
                        key=f"open_{usr['user_id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_user_id = usr['user_id']
                        st.rerun()

            with col_chat:
                if st.session_state.selected_user_id is None and user_list:
                    st.session_state.selected_user_id = \
                        user_list[0]['user_id']

                if not st.session_state.selected_user_id:
                    _empty_state("👈", "No Conversation Selected",
                                 "Select a user from the left.")
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

                    st.markdown(f"""
                    <div style="background:#0f1e30;border:1px solid #1e293b;
                        border-radius:12px 12px 0 0;padding:12px 16px;
                        display:flex;align-items:center;gap:10px;">
                        <div style="width:36px;height:36px;border-radius:50%;
                            background:#2563eb;display:flex;
                            align-items:center;justify-content:center;
                            font-size:16px;flex-shrink:0;">👤</div>
                        <div>
                            <div style="color:#F0F4F8;font-size:14px;
                                        font-weight:600;">
                                {selected_email}</div>
                            <div style="color:#64748B;font-size:12px;">
                                {len(user_msgs)} message
                                {"s" if len(user_msgs) != 1 else ""}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if not user_msgs:
                        _empty_state("📭", "No Messages Yet",
                                     "This user has not sent any messages.")
                    else:
                        components.html(
                            _build_chat_html(user_msgs, height=440),
                            height=460, scrolling=False
                        )

                    with st.form(
                        key=f"reply_{st.session_state.selected_user_id}",
                        clear_on_submit=True
                    ):
                        col_i, col_b = st.columns([5, 1])
                        with col_i:
                            reply_text = st.text_input(
                                "Reply",
                                placeholder="Type a reply...",
                                label_visibility="collapsed"
                            )
                        with col_b:
                            sub = st.form_submit_button(
                                "Send", use_container_width=True
                            )
                        if sub:
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
                                    st.info(
                                        "All messages have been replied to."
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
                _empty_state("📈", "No Chart Data Yet",
                             "Message activity will appear here.")

        if st.session_state.auto_refresh:
            time.sleep(2)
            current_count = get_total_message_count(supabase)
            if current_count != st.session_state.admin_last_count:
                st.session_state.admin_last_count = current_count
                st.rerun()
            else:
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
            '<div style="color:#94A3B8;font-size:13px;margin-bottom:20px;">'
            'Promote users to admin or demote admins back to user. '
            'You cannot change your own role.</div>',
            unsafe_allow_html=True
        )

        with st.spinner("Loading users..."):
            all_users = get_all_users(supabase)

        if not all_users:
            _empty_state("👥", "No Users Found",
                         "No users have signed up yet.")
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
                        f'<div style="color:#F0F4F8;font-size:14px;'
                        f'padding-top:8px;">{email}'
                        f'<span style="color:#64748B;font-size:12px;">'
                        f'{self_label}</span></div>',
                        unsafe_allow_html=True
                    )
                with col_badge:
                    st.markdown(
                        f'<div style="background:{badge_bg};'
                        f'color:{badge_fg};border:1px solid {badge_border};'
                        f'border-radius:20px;padding:6px 12px;'
                        f'font-size:11px;font-weight:700;'
                        f'text-transform:uppercase;text-align:center;'
                        f'margin-top:4px;">{role}</div>',
                        unsafe_allow_html=True
                    )
                with col_action:
                    if is_self:
                        st.markdown(
                            '<div style="color:#64748B;font-size:12px;'
                            'padding-top:10px;text-align:center;">'
                            'Your account</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        new_role  = "user" if role == "admin" else "admin"
                        btn_label = (
                            "Demote" if role == "admin" else "Promote"
                        )
                        if st.button(
                            btn_label, key=f"role_{uid}",
                            use_container_width=True
                        ):
                            with st.spinner("Updating..."):
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
                                    f"{email} → {new_role.upper()}"
                                )
                                st.rerun()
                            else:
                                st.error(message)

                st.markdown(
                    '<hr style="border-color:#1f2a36;margin:8px 0;">',
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
            _empty_state("📋", "No Audit Logs Yet",
                         "User actions will be recorded here.")
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
