import streamlit as st

def apply_theme():
    st.markdown("""
<style>
/* ---------- GLOBAL RESET ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Force dark blue on the entire app */
.stApp {
    background-color: #0B1B2B;
}

/* Main content container */
.main .block-container {
    background-color: #0B1B2B;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Override any white containers */
div[data-testid="stVerticalBlock"] > div,
div[data-testid="stHorizontalBlock"] > div,
section[data-testid="stSidebar"] {
    background-color: #0B1B2B !important;
}

/* ---------- SIDEBAR (Left Column) ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A192F, #102A43) !important;
    border-right: 1px solid #2563eb;
}
section[data-testid="stSidebar"] * {
    color: #F0F4F8 !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stButton button {
    color: #F0F4F8 !important;
}

/* Sidebar radio buttons */
section[data-testid="stSidebar"] .stRadio > div {
    gap: 10px;
}
section[data-testid="stSidebar"] label {
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    white-space: nowrap !important;
    width: 100% !important;
    box-sizing: border-box;
    color: #F0F4F8 !important;
    background: transparent;
}
section[data-testid="stSidebar"] label:hover {
    background: rgba(255, 255, 255, 0.1);
}
section[data-testid="stSidebar"] label[data-selected="true"] {
    background: #2563eb;
    color: white !important;
}

/* Sidebar user info and logout */
section[data-testid="stSidebar"] .stButton button {
    background: #2563eb;
    border: none;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #3b82f6;
}

/* ---------- LOGIN / SIGNUP PAGE ---------- */
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

/* Login card */
.login-card {
    background: rgba(26, 46, 68, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid #2563eb;
    border-radius: 24px;
    padding: 40px 32px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

/* Input fields */
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

/* Buttons */
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
    box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
}

/* Error messages */
.stAlert {
    background: transparent;
    color: #F87171;
    border: none;
    padding: 8px 0;
}

/* ---------- APP CARDS ---------- */
.card {
    background: #1A2E44;
    border: 1px solid #2563eb;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.app-subtitle {
    text-align: center;
    color: #A0AEC0;
    margin-bottom: 20px;
}
.notification-badge {
    background-color: #EF4444;
    color: white;
    border-radius: 50%;
    padding: 2px 8px;
    font-size: 12px;
    margin-left: 8px;
}

/* About page specific */
.about-card {
    background: #1A2E44;
    border: 1px solid #2563eb;
    padding: 30px;
    border-radius: 24px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
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

/* ---------- CHAT PANEL ---------- */
.unified-chat {
    background: #1A2E44;
    border-radius: 20px;
    border: 1px solid #2563eb;
    overflow: hidden;
    margin-bottom: 20px;
}
.chat-input-container {
    padding: 16px 20px;
    background: #0F2336;
    border-top: 1px solid #2563eb;
    margin-top: 0;
}
.chat-input-container .stTextInput > div > div > input {
    background: #1A2E44;
    border: 1px solid #2563eb;
    border-radius: 24px;
    color: white;
    padding: 12px 18px;
}
.chat-input-container .stButton > button {
    border-radius: 24px;
    height: auto;
    padding: 10px 20px;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #0B1B2B;
}
::-webkit-scrollbar-thumb {
    background: #2563eb;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)
