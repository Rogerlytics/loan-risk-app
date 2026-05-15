# ==============================
# views/contact.py
# ==============================
import streamlit as st
import streamlit.components.v1 as components
import time
from services.supabase_service import (
    get_user_messages,
    send_message,
    mark_messages_as_read,
    get_message_count,
    log_action
)
from utils.helpers import relative_time, sanitise_text


def show_contact(supabase):
    st.markdown(
        '<div class="section-heading">Customer Support Chat</div>',
        unsafe_allow_html=True
    )

    if st.session_state.role == "admin":
        st.info(
            "Admin view: See all conversations in the Admin Dashboard."
        )
        return

    user_id    = st.session_state.user["id"]
    user_email = st.session_state.user.get("email", "")

    if "last_msg_count" not in st.session_state:
        st.session_state.last_msg_count = 0
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False

    with st.spinner("Loading messages..."):
        mark_messages_as_read(supabase, user_id)
        msgs = get_user_messages(supabase, user_id)

    st.session_state.last_msg_count = len(msgs)

    # ── Control bar ──
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
    .live-bar {{ display:flex; align-items:center; gap:10px;
                 padding:4px 0; margin-bottom:6px; }}
    .live-dot  {{ width:10px; height:10px; border-radius:50%;
                  background:{dot_col}; {pulse} flex-shrink:0; }}
    .live-label{{ color:{dot_col}; font-size:13px; font-weight:600; }}
    </style>
    <div class="live-bar">
        <div class="live-dot"></div>
        <span class="live-label">{dot_txt}</span>
    </div>
    """, unsafe_allow_html=True)

    col_r, col_t, col_sp = st.columns([1, 1, 4])
    with col_r:
        if st.button("Refresh", use_container_width=True,
                     key="contact_refresh"):
            st.rerun()
    with col_t:
        if st.button(tog_lbl, use_container_width=True,
                     key="contact_live_toggle"):
            st.session_state.auto_refresh = not st.session_state.auto_refresh
            st.rerun()

    # Quick actions
    st.markdown(
        '<div style="color:#94A3B8; font-size:12px; '
        'margin:10px 0 6px 0;">Quick Actions</div>',
        unsafe_allow_html=True
    )
    cols = st.columns(4)
    quick_actions = [
        ("Loan Status",    "What is my loan application status?"),
        ("Payment Help",   "I need help with my payment."),
        ("Upload Docs",    "I need to upload documents."),
        ("Reset Password", "I forgot my password."),
    ]
    for i, (label, draft) in enumerate(quick_actions):
        with cols[i]:
            if st.button(label, use_container_width=True, key=f"qa_{i}"):
                st.session_state.draft_message = draft
                st.rerun()

    # ── Professional chat window ──
    chat_rows = ""
    if not msgs:
        chat_rows = '''
        <div style="display:flex; flex-direction:column; align-items:center;
                    justify-content:center; height:100%; padding:40px 20px;">
            <div style="font-size:40px; margin-bottom:12px;">💬</div>
            <div style="color:#F0F4F8; font-size:16px; font-weight:600;
                        margin-bottom:6px;">No messages yet</div>
            <div style="color:#64748B; font-size:13px; text-align:center;">
                Send a message below to start the conversation.</div>
        </div>'''
    else:
        for msg in msgs:
            ts           = relative_time(msg.get('timestamp', ''))
            safe_message = msg['message']
            # Sender row (right aligned)
            chat_rows += f'''
            <div style="display:flex; justify-content:flex-end;
                        margin-bottom:4px; padding:0 16px;">
                <div style="max-width:80%;">
                    <div style="background:#2563eb; color:#fff;
                                padding:10px 14px; border-radius:18px
                                18px 4px 18px; font-size:14px;
                                line-height:1.5; word-break:break-word;
                                white-space:pre-wrap;">
                        {safe_message}
                    </div>
                    <div style="text-align:right; font-size:11px;
                                color:#64748B; margin-top:3px;
                                padding-right:4px;">{ts}</div>
                </div>
            </div>'''
            if msg.get('reply'):
                reply_ts   = relative_time(msg.get('replied_at', ''))
                safe_reply = msg['reply']
                # Support row (left aligned)
                chat_rows += f'''
            <div style="display:flex; justify-content:flex-start;
                        margin-bottom:4px; padding:0 16px;">
                <div style="max-width:80%;">
                    <div style="font-size:11px; color:#60A5FA;
                                font-weight:600; margin-bottom:3px;
                                padding-left:4px;">Support</div>
                    <div style="background:#1e293b; color:#F0F4F8;
                                padding:10px 14px; border-radius:18px
                                18px 18px 4px; font-size:14px;
                                line-height:1.5; word-break:break-word;
                                white-space:pre-wrap; border:1px solid #334155;">
                        {safe_reply}
                    </div>
                    <div style="text-align:left; font-size:11px;
                                color:#64748B; margin-top:3px;
                                padding-left:4px;">{reply_ts}</div>
                </div>
            </div>'''

    chat_html = f"""
    <!DOCTYPE html><html><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    html, body {{ height:100%; background:#0B1220;
                  font-family:"Inter",-apple-system,sans-serif; }}
    .chat-container {{
        display:flex; flex-direction:column;
        height:500px; background:#0B1220;
        border:1px solid #1e293b; border-radius:16px;
        overflow:hidden;
    }}
    .chat-header {{
        padding:12px 16px;
        background:#0f1e30;
        border-bottom:1px solid #1e293b;
        display:flex; align-items:center; gap:10px;
    }}
    .chat-avatar {{
        width:36px; height:36px; border-radius:50%;
        background:#2563eb; display:flex; align-items:center;
        justify-content:center; font-size:16px; flex-shrink:0;
    }}
    .chat-header-info {{ flex:1; }}
    .chat-header-name {{ color:#F0F4F8; font-size:14px; font-weight:600; }}
    .chat-header-status {{ color:#22c55e; font-size:12px; }}
    .chat-messages {{
        flex:1; overflow-y:auto; padding:16px 0;
        display:flex; flex-direction:column; gap:8px;
        scroll-behavior:smooth;
    }}
    .chat-messages::-webkit-scrollbar {{ width:4px; }}
    .chat-messages::-webkit-scrollbar-track {{ background:transparent; }}
    .chat-messages::-webkit-scrollbar-thumb {{
        background:#334155; border-radius:4px;
    }}
    .date-divider {{
        display:flex; align-items:center; gap:10px;
        padding:4px 16px; margin:4px 0;
    }}
    .date-divider hr {{
        flex:1; border:none; border-top:1px solid #1e293b;
    }}
    .date-divider span {{
        color:#64748B; font-size:11px; white-space:nowrap;
    }}
    </style>
    </head><body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="chat-avatar">🎧</div>
            <div class="chat-header-info">
                <div class="chat-header-name">Support Team</div>
                <div class="chat-header-status">● Online</div>
            </div>
        </div>
        <div class="chat-messages" id="chatMessages">
            {chat_rows}
            <div id="chatEnd"></div>
        </div>
    </div>
    <script>
        const el = document.getElementById("chatEnd");
        if (el) el.scrollIntoView({{ behavior:"smooth" }});
    </script>
    </body></html>
    """

    components.html(chat_html, height=520, scrolling=False)

    # Message input
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_button = st.columns([5, 1])
        with col_input:
            msg = st.text_input(
                "",
                placeholder="Type a message...",
                value=st.session_state.draft_message,
                label_visibility="collapsed",
                key="chat_input"
            )
        with col_button:
            submitted = st.form_submit_button(
                "Send", use_container_width=True
            )
        if submitted and msg.strip():
            try:
                clean_msg = sanitise_text(msg, max_length=500)
                with st.spinner("Sending..."):
                    send_message(supabase, user_id, user_email, clean_msg)
                log_action(
                    supabase, user_id, user_email,
                    "message_sent",
                    f"Message length: {len(clean_msg)} chars"
                )
                st.session_state.draft_message = ""
                st.success("Message sent!")
                time.sleep(0.3)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Smart polling ──
    if st.session_state.auto_refresh:
        time.sleep(2)
        current_count = get_message_count(supabase, user_id)
        if current_count != st.session_state.last_msg_count:
            st.session_state.last_msg_count = current_count
            st.rerun()
        else:
            st.rerun()
