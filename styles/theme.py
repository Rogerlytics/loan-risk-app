# ==============================
# styles/theme.py
# ==============================
import streamlit as st

def apply_theme():
    st.markdown("""
<style>

/* ── Hide Streamlit auto page nav ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Global Reset ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0e1117; }
.main .block-container {
    background-color: #0e1117;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
div[data-testid="stVerticalBlock"] > div,
div[data-testid="stHorizontalBlock"] > div {
    background-color: #0e1117 !important;
}

/* ── 3D Gradient Blue Title — used across ALL pages ── */
.page-title {
    text-align: center;
    font-size: 52px;
    font-weight: 800;
    background: linear-gradient(180deg, #93C5FD 0%, #3B82F6 45%, #1D4ED8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.6));
    letter-spacing: -1px;
    margin-bottom: 8px;
    line-height: 1.1;
}
.page-subtitle {
    text-align: center;
    color: #94A3B8;
    font-size: 16px;
    margin-bottom: 28px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220, #0e1622) !important;
    border-right: 1px solid #1f2a36;
}
section[data-testid="stSidebar"] * { color: #F0F4F8 !important; }
section[data-testid="stSidebar"] label {
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    width: 100% !important;
    box-sizing: border-box;
    background: transparent;
}
section[data-testid="stSidebar"] label:hover {
    background: #1a2330;
}
section[data-testid="stSidebar"] .stButton button {
    background: #1f77ff;
    border: none;
    color: white !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #155edb;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    background: #1a222c;
    border: 1px solid #2a3748;
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    width: 100% !important;
    box-sizing: border-box;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #3b82f6;
    outline: none;
}
.stTextInput > div > div > input::placeholder { color: #94A3B8; }

/* ── Buttons ── */
.stButton > button {
    background: #1f77ff;
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
    background: #155edb;
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(31,119,255,0.3);
}

/* ── Cards ── */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid #1f2a36;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}
.app-subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 20px;
}

/* ── Section headings ── */
.section-heading {
    font-size: 20px;
    font-weight: 700;
    color: #60A5FA;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1f2a36;
}

/* ── About Page ── */
.about-card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid #1f2a36;
    padding: 30px;
    border-radius: 24px;
}
.about-heading { color: #60A5FA; font-size: 24px; font-weight: 600; margin-bottom: 16px; }
.about-text { color: #E2E8F0; font-size: 16px; line-height: 1.6; }
.feature-list { list-style-type: none; padding-left: 0; }
.feature-list li { margin-bottom: 12px; color: #E2E8F0; }

/* ── Role badges ── */
.role-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.role-badge.admin { background:#7c3aed22; color:#a78bfa; border:1px solid #7c3aed44; }
.role-badge.user  { background:#0369a122; color:#38bdf8; border:1px solid #0369a144; }

/* ── Chat ── */
.chat-input-container {
    padding: 16px 20px;
    background: #0e1622;
    border-top: 1px solid #1f2a36;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0e1117; }
::-webkit-scrollbar-thumb { background: #2563eb; border-radius: 10px; }

/* ── Hide empty element containers ── */
.element-container:empty { display: none !important; }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:empty {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)
