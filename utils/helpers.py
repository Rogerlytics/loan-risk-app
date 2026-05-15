# ==============================
# utils/helpers.py
# ==============================
import streamlit as st
from datetime import datetime
import re


def apply_custom_css():
    """Global custom CSS matching your dark theme."""
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: #0B1220;
    }
    
    /* Section heading style */
    .section-heading {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 24px;
        padding-bottom: 8px;
        border-bottom: 2px solid #1e293b;
    }
    
    /* Cards and containers */
    .stMarkdown, .stDataFrame, .stPlotlyChart {
        background: transparent;
    }
    
    /* Input fields */
    .stTextInput > div > div > input, .stSelectbox > div > div, .stNumberInput > div > div {
        background-color: #0f1e30 !important;
        border: 1px solid #1e293b !important;
        color: #F0F4F8 !important;
        border-radius: 12px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #1e3a5f, #0f1e30);
        border: 1px solid #2563eb;
        border-radius: 12px;
        color: #F0F4F8;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #2563eb;
        border-color: #60A5FA;
        transform: translateY(-1px);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #0B1220;
        border-bottom: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 8px 16px;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background: #0f1e30;
        color: #60A5FA;
        border-bottom: 2px solid #60A5FA;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #60A5FA;
        font-size: 28px;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8;
    }
    
    /* Dataframe */
    .stDataFrame {
        background: #0f1e30;
        border-radius: 12px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #60A5FA !important;
    }
    
    /* Success/Info/Warning/Error */
    .stSuccess {
        background: #052e16;
        color: #86efac;
        border-left: 4px solid #22c55e;
    }
    .stError {
        background: #2c0f0f;
        color: #f87171;
        border-left: 4px solid #ef4444;
    }
    .stWarning {
        background: #2c1a0f;
        color: #fbbf24;
        border-left: 4px solid #f59e0b;
    }
    .stInfo {
        background: #0f1e30;
        color: #60A5FA;
        border-left: 4px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)


def relative_time(timestamp_str):
    """Convert ISO timestamp to human-readable relative time."""
    if not timestamp_str:
        return "Just now"
    try:
        # Handle string or datetime
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str
        
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} min{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime("%d %b %Y")
    except Exception:
        return "Unknown"


def sanitise_text(text, max_length=500):
    """Sanitise user input to prevent XSS and trim length."""
    if not text:
        return ""
    # Remove any HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Trim to max length
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    return clean.strip()
