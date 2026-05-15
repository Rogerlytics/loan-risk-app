# ==============================
# styles/theme.py
# ==============================
import streamlit as st


def apply_theme():
    """Original global theme – dark background, custom fonts."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0B1220 0%, #0a0f1a 100%);
    }
    .page-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
    }
    .page-subtitle {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 2rem;
        border-left: 3px solid #2563eb;
        padding-left: 1rem;
    }
    .section-heading {
        font-size: 1.8rem;
        font-weight: 600;
        color: #F0F4F8;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0a0f1a;
        border-right: 1px solid #1e293b;
    }
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #1e3a5f, #0f1e30);
        border: 1px solid #2563eb;
        border-radius: 12px;
        color: white;
        font-weight: 500;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }
    /* Inputs */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background-color: #0f1e30 !important;
        border: 1px solid #1e293b !important;
        color: #F0F4F8 !important;
        border-radius: 12px;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #0f1e30;
        border-radius: 12px 12px 0 0;
        color: #94A3B8;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #1e3a5f;
        color: #60A5FA;
        border-bottom: 2px solid #60A5FA;
    }
    </style>
    """, unsafe_allow_html=True)
