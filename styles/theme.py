import streamlit as st

def apply_theme():
    st.markdown("""
<style>
/* ── Hide Streamlit auto page nav ── */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #0B1B2B;
}
.main .block-container {
    background-color: #0B1B2B;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
div[data-testid="stVerticalBlock"] > div,
div[data-testid="stHorizontalBlock"] > div {
    background-color: #0B1B2B !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A192F, #102A43) !important;
    border-right: 1px solid #2563eb;
}
section[data-testid="stSidebar"] * {
    color: #F0F4F8 !important;
}
section[data-testid="stSidebar"] label {
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    width: 100% !important;
    box-sizing: border-box;
    color: #F0F4F8 !important;
    background: transparent;
}
section[data-testid="stSidebar"] label:hover {
    background: rgba(255,255,255,0.1);
}
section[data-testid="stSidebar"] .stButton button {
    background: #2563eb;
    border: none;
    color: white !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #3b82f6;
}

/* ── Hide sidebar on login ── */
.sidebar-hidden section[data-testid="stSidebar"] {
    display: none !important;
}

/* ── Login Page ── */
.title {
    font-size: 42px;
    font-weight: 700;
    color: #F0F4F8;
    text-align: center;
    margin-bottom: 8px;
}
.subtitle {
    color: #A0AEC0;
    text-align: center;
    margin-bottom: 40px;
    font-size: 16px;
}
.section {
    font-size: 22px;
    font-weight: 600;
    text-align: center;
    color: #F0F4F8;
    margin-bottom: 8px;
}
.small {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 24px;
    font-size: 14px;
}
.login-card {
    background: rgba(26,46,68,0.8);
    backdrop-filter: blur(12px);
    border: 1px solid #2563eb;
    border-radius: 24px;
    padding: 40px 32px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    background: #1A2E44;
    border: 1px solid #2563eb;
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    width: 100% !important;
    box-sizing: border-box;
}
.stTextInput > div > div > input::placeholder {
    color: #94A3B8;
}

/* ── Buttons ── */
.stButton > button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 12px 24px;
    font-weight: 600;
    width: 100%;
    transition: all 0.2s;
    height: 45px;
}
.stButton > button:hover {
    background: #3b82f6;
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(37,99,235,0.3);
}

/* ── Cards ── */
.card {
    background: #1A2E44;
    border: 1px solid #2563eb;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.app-subtitle {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 20px;
}

/* ── About Page ── */
.about-card {
    background: #1A2E44;
    border: 1px solid #2563eb;
    padding: 30px;
    border-radius: 24px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}
.about-heading {
    color: #60A5FA;
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 16px;
}
.about-text {
    color: #E2E8F0;
    font-size: 16px;
    line-height: 1.6;
}
.feature-list {
    list-style-type: none;
    padding-left: 0;
}
.feature-list li {
    margin-bottom: 12px;
    color: #E2E8F0;
}

/* ── Chat ── */
.chat-input-container {
    padding: 16px 20px;
    background: #0F2336;
    border-top: 1px solid #2563eb;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0B1B2B; }
::-webkit-scrollbar-thumb { background: #2563eb; border-radius: 10px; }

/* ── Remove stray empty elements ── */
.stRadio > label:empty { display: none; }
.element-container:empty { display: none; }
</style>
""", unsafe_allow_html=True)
