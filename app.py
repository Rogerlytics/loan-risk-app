import streamlit as st

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="AI Loan Risk Platform",
    layout="wide"
)

# ==============================
# 🎨 PREMIUM SAAS UI STYLE
# ==============================
st.markdown("""
<style>

/* Background gradient */
body {
    background: linear-gradient(135deg, #0e1117, #111827);
}

/* Center everything */
.main-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80vh;
}

/* Card */
.login-card {
    background: rgba(255, 255, 255, 0.05);
    padding: 40px;
    border-radius: 16px;
    backdrop-filter: blur(12px);
    width: 380px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

/* Title */
.title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    color: white;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 30px;
}

/* Tabs (User/Admin) */
.role-container {
    display: flex;
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 5px;
    margin-bottom: 20px;
}

.role-container div {
    flex: 1;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    cursor: pointer;
}

/* Input spacing */
.stTextInput {
    margin-bottom: 15px;
}

/* Button */
.stButton>button {
    background: linear-gradient(90deg, #1f77ff, #4f9cff);
    color: white;
    border-radius: 10px;
    height: 45px;
    font-weight: 600;
    border: none;
}

.stButton>button:hover {
    background: linear-gradient(90deg, #155edb, #3a7de0);
}

/* Footer text */
.footer {
    text-align: center;
    color: #6B7280;
    margin-top: 15px;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# CENTER LAYOUT
# ==============================
col1, col2, col3 = st.columns([1,1,1])

with col2:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    # ==============================
    # HEADER
    # ==============================
    st.markdown('<div class="title">AI Loan Risk</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Smart credit decisions powered by AI</div>', unsafe_allow_html=True)

    # ==============================
    # ROLE SELECTOR (PILL STYLE)
    # ==============================
    role = st.radio(
        "",
        ["User", "Administrator"],
        horizontal=True
    )

    # ==============================
    # INPUTS
    # ==============================
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password")

    # ==============================
    # LOGIN BUTTON
    # ==============================
    if st.button("Sign In", use_container_width=True):
        if email and password:
            st.success(f"Welcome back ({role})")
        else:
            st.error("Enter email and password")

    # ==============================
    # FOOTER
    # ==============================
    st.markdown('<div class="footer">Secure • Fast • Intelligent</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
