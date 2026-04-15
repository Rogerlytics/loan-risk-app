# ==============================
# CONTACT (FULL RESTORED)
# ==============================
elif page == "Contact":

    st.subheader("💬 Customer Support Chat")

    if not st.session_state.user:
        st.warning("Please login to access chat")
    else:

        # MESSAGE INPUT
        msg = st.text_input("Type your message")

        if st.button("Send"):
            if msg.strip() != "":
                supabase.table("messages").insert({
                    "user_id": st.session_state.user["id"],
                    "name": st.session_state.user["username"],
                    "email": st.session_state.user["email"],
                    "message": msg,
                    "status": "sent"
                }).execute()
                st.rerun()

        # FETCH MESSAGES (NEWEST LAST → CHAT FLOW)
        msgs = supabase.table("messages").select("*").eq(
            "user_id", st.session_state.user["id"]
        ).order("id").execute().data

        st.markdown("### 💬 Chat Conversation")

        # CHAT LOOP
        for m in msgs:

            msg_id = m["id"]

            # 👁️ SEEN NOTIFICATION
            if m.get("status") == "seen" and msg_id not in st.session_state.seen_notified:
                st.toast("👁️ Your message was seen")
                st.session_state.seen_notified.add(msg_id)

            user_name = m.get("name", "User")
            timestamp = m.get("timestamp", "")

            # STATUS TICKS
            status = m.get("status", "sent")
            if status == "sent":
                tick = "✓"
            elif status == "delivered":
                tick = "✓✓"
            else:
                tick = "✓✓ 👁️"

            # USER MESSAGE (RIGHT)
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

            # ADMIN REPLY (LEFT)
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

        # AUTO SCROLL
        st.markdown("<div id='bottom'></div>", unsafe_allow_html=True)
        st.markdown("""
        <script>
        var element = document.getElementById("bottom");
        if (element) {
            element.scrollIntoView({behavior: "smooth"});
        }
        </script>
        """, unsafe_allow_html=True)


# ==============================
# ADMIN DASHBOARD (FULL RESTORED)
# ==============================
elif page == "Admin Dashboard":

    st.subheader("📊 Admin Control Panel")

    username = st.text_input("Admin Username")
    password = st.text_input("Password", type="password")

    if st.button("Login Admin"):
        if username == ADMIN_USERNAME and check_password(password):
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.session_state.logged_in:

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        try:
            data = supabase.table("messages").select("*").execute().data
            df = pd.DataFrame(data)

            st.metric("Total Messages", len(df))

            # 📊 ANALYTICS
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                daily = df.groupby(df["timestamp"].dt.date).size().reset_index(name="count")

                fig = px.line(daily, x="timestamp", y="count",
                              title="📈 Messages Over Time")
                st.plotly_chart(fig)

            st.markdown("### 📬 Inbox")

            for m in data:

                # AUTO MARK AS SEEN
                if m.get("status") != "seen":
                    supabase.table("messages").update({
                        "status": "seen"
                    }).eq("id", m["id"]).execute()

                st.markdown(f"""
                <div style='background:#111827; padding:12px; border-radius:10px; margin-bottom:10px'>
                    <b>{m.get("name","User")}</b><br>
                    <small>{m.get("email","")}</small><br><br>
                    {m.get("message","")}
                </div>
                """, unsafe_allow_html=True)

                # REPLY BOX
                reply = st.text_input(f"Reply to message {m['id']}")

                if st.button(f"Send Reply {m['id']}"):
                    supabase.table("messages").update({
                        "reply": reply,
                        "replied_at": str(datetime.now())
                    }).eq("id", m["id"]).execute()
                    st.success("Reply sent")
                    st.rerun()

        except Exception as e:
            st.error(f"Database error: {e}")
