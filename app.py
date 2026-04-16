def show_login_page():
    # Page title and subtitle
    st.markdown('<div class="page-title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

    # Center wrapper
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Sign in to access your account</div>', unsafe_allow_html=True)

    # ==============================
    # PERFECTLY CENTERED ROLE TOGGLE
    # ==============================
    role = st.radio(
        "",
        ["User", "Administrator"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # ==============================
    # CENTERED INPUTS (MATCH CARD WIDTH)
    # ==============================
    col_left, col_center, col_right = st.columns([1, 3, 1])

    with col_center:
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

            st.markdown(
                '<p class="login-footer">Don\'t have an account? <a href="#">Sign up</a></p>',
                unsafe_allow_html=True
            )

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

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
