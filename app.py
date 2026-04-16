import streamlit as st

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="AI Loan Risk Platform",
    layout="wide"
)

# ==============================
# 🎨 DARK PREMIUM THEME
# ==============================
st.markdown("""
<style>
body {
    background-color: #0e1117;
}

/* Center everything */
.center-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

/* Button row */
.button-row {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 10px;
    margin-bottom: 20px;
}

/* Input width control */
.stTextInput > div > div > input {
    width: 350px;
}

/* Title styling */
.title {
    text-align: center;
    font-size: 40px;
    font-weight: bold;
    color: white;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 30px;
}

/* Section text */
.section-text {
    text-align: center;
    font-size: 22px;
    font-weight: 600;
}

/* Small text */
.small-text {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown('<div class="title">AI Loan Risk Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Intelligent credit evaluation for smarter lending</div>', unsafe_allow_html=True)

# ==============================
# LOGIN SECTION
# ==============================
st.markdown("<div class='center-container'>", unsafe_allow_html=True)

st.markdown('<div class="section-text">Welcome back</div>', unsafe_allow_html=True)
st.markdown('<div class="small-text">Sign in to access your account</div>', unsafe_allow_html=True)

# ==============================
# ROLE SELECTION (CENTERED)
# ==============================
st.markdown("<div class='button-row'>", unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

with col1:
    role_user = st.radio("",
                         ["User"],
                         label_visibility="collapsed",
                         key="user_radio")

with col2:
    role_admin = st.radio("",
                          ["Administrator"],
                          label_visibility="collapsed",
                          key="admin_radio")

st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# INPUT FIELDS (CENTERED)
# ==============================
email = st.text_input("Email", placeholder="you@example.com")
password = st.text_input("Password", type="password")

# ==============================
# LOGIN BUTTON
# ==============================
login_col1, login_col2, login_col3 = st.columns([1,1,1])

with login_col2:
    if st.button("Login", use_container_width=True):
        st.success("Login button clicked")

st.markdown("</div>", unsafe_allow_html=True)
