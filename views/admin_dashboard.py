col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Refresh", use_container_width=True):
                st.rerun()
        with col2:
            auto = st.checkbox(
                "Auto",
                value=st.session_state.auto_refresh,
                key="admin_auto",
                help="Auto-refresh when new messages arrive"
            )
            st.session_state.auto_refresh = auto
        with col3:
            if st.session_state.auto_refresh:
                st.markdown(
                    '<div style="color:#22c55e; font-size:13px; '
                    'padding-top:8px;">● Live</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="color:#64748B; font-size:13px; '
                    'padding-top:8px;">○ Paused</div>',
                    unsafe_allow_html=True
                )
