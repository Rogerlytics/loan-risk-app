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

    # ── Smart polling state ──
    if "last_msg_count" not in st.session_state:
        st.session_state.last_msg_count = 0
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False

    with st.spinner("Loading messages..."):
        mark_messages_as_read(supabase, user_id)
        msgs = get_user_messages(supabase, user_id)

    st.session_state.last_msg_count = len(msgs)

    # ── Single row: dot | Refresh | Toggle ──
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
    .live-bar {{
        display:flex; align-items:center; gap:10px;
        padding:6px 0; margin-bottom:4px;
    }}
    .live-dot {{
        width:10px; height:10px; border-radius:50%;
        background:{dot_col}; {pulse} flex-shrink:0;
    }}
    .live-label {{
        color:{dot_col}; font-size:13px; font-weight:600;
    }}
    </style>
    <div class="live-bar">
        <div class="live-dot"></div>
        <span class="live-label">{dot_txt}</span>
    </div>
    """, unsafe_allow_html=True)

    col_r, col_t, col_sp = st.columns([1, 1, 4])
    with col_r:
        if st.button(
            "Refresh", use_container_width=True, key="contact_refresh"
        ):
            st.rerun()
    with col_t:
        if st.button(
            tog_lbl, use_container_width=True, key="contact_live_toggle"
        ):
            st.session_state.auto_refresh = not st.session_state.auto_refresh
            st.rerun()

    # Quick actions
    st.markdown(
        '<div style="color:#94A3B8; font-size:12px; '
        'margin:12px 0 6px 0;">Quick Actions</div>',
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

    # Build chat HTML
    chat_html_parts = ['''<html><head>
    <meta charset="UTF-8">
    <style>
    * { box-sizing:border-box; }
    body { margin:0; background:#0e1117;
           font-family:"Inter",sans-serif; color:#F0F4F8; }
    .chat-wrap { height:450px; overflow-y:auto; padding:20px;
                 scroll-behavior:smooth; }
    .chat-bubble-row { display:flex; margin-bottom:12px; }
    .chat-bubble-row.user  { justify-content:flex-end; }
    .chat-bubble-row.admin { justify-content:flex-start; }
    .chat-bubble { max-width:70%; padding:12px 16px;
                   border-radius:18px; font-size:14px;
                   line-height:1.4; word-wrap:break-word; }
    .user  .chat-bubble { background:#2563eb; color:white;
                          border-bottom-right-radius:4px; }
    .admin .chat-bubble { background:#1f2a36; color:#F0F4F8;
                          border-bottom-left-radius:4px; }
    .chat-timestamp { font-size:11px; color:#94A3B8;
                      margin-top:4px; text-align:right; }
    .reply-badge { background:#0e1117; color:#60A5FA;
                   border-radius:16px; padding:4px 12px;
                   font-size:12px; margin-bottom:8px;
                   display:inline-block; border:1px solid #2563eb; }
    .empty-state { text-align:center; color:#94A3B8;
                   padding:60px 20px; font-size:14px; }
    </style></head><body>
    <div class="chat-wrap" id="chatWrap">''']

    if not msgs:
        chat_html_parts.append(
            '<div class="empty-state">'
            'No messages yet.<br>'
            'Send a message below to get started.'
            '</div>'
        )
    else:
        for msg in msgs:
            timestamp    = relative_time(msg.get('timestamp', ''))
            safe_message = msg['message']
            chat_html_parts.append(f'''
            <div class="chat-bubble-row user">
                <div style="display:flex; flex-direction:column;
                            align-items:flex-end; max-width:70%;">
                    <div class="chat-bubble">{safe_message}</div>
                    <div class="chat-timestamp">{timestamp}</div>
                </div>
            </div>''')
            if msg.get('reply'):
                reply_time = relative_time(msg.get('replied_at', ''))
                safe_reply = msg['reply']
                chat_html_parts.append(f'''
            <div class="chat-bubble-row admin">
                <div style="display:flex; flex-direction:column;
                            max-width:70%;">
                    <div class="reply-badge">Support</div>
                    <div class="chat-bubble">{safe_reply}</div>
                    <div class="chat-timestamp">{reply_time}</div>
                </div>
            </div>''')

    # Auto scroll to bottom
    chat_html_parts.append('''
    <div id="anchor"></div>
    </div>
    <script>
        const wrap = document.getElementById("chatWrap");
        if (wrap) wrap.scrollTop = wrap.scrollHeight;
    </script>
    </body></html>''')

    components.html(
        "".join(chat_html_parts), height=460, scrolling=False
    )

    # Message input
    st.markdown(
        '<div class="chat-input-container">', unsafe_allow_html=True
    )
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
