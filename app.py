import streamlit as st

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="AI Loan Risk Platform",
    layout="wide"
)

# ==============================
# 🎨 PREMIUM DARK UI
# ==============================
st.markdown("""
<style>

/* Background */
body {
    background-color: #0e1117;
}

/* Main container */
.block-container {
    padding-top: 3rem;
}

/* Center column text */
.center-text {
    text-align: center;
}

/* Title */
.title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    text-align: center;
}

/* Subtitle */
.subtitle {
    color: #A0AEC0;
    text-align: center;
    margin-bottom: 40px;
}

/* Section header */
.section {
    font-size: 22px;
    font-weight: 600;
    text-align: center;
}

/* Small text */
.small {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 20px;
}

/* Radio buttons horizontal spacing */
div[role="radiogroup"] {
    justify-content: center;
}

/* Button styling */
.stButton>button {
    background-color: #1f77ff;
    color: white;
    border-radius: 8px;
    height: 45px;
    font-weight: 600;
}

.stButton>button:hover {
    background-color: #155edb;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

# ==============================
# CENTERED LOGIN CARD
# ==============================
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    st.markdown('<div class="section">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Sign in to access your account</div>', unsafe_allow_html=True)

    # ==============================
    # ROLE SELECTION (CLEAN TOGGLE)
    # ==============================
    role = st.radio(
        "",
        ["User", "Administrator"],
        horizontal=True
    )

    # ==============================
    # INPUT FIELDS
    # ==============================
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password")

    # ==============================
    # LOGIN BUTTON
    # ==============================
    if st.button("Login", use_container_width=True):
        if email and password:
            st.success(f"Logging in as {role}")
        else:
            st.error("Please enter email and password")
