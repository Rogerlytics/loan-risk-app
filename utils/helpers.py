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
    clean = re.sub(r'<[^>]*>', '', text)
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    return clean.strip()


def sanitise_number(value, default=0):
    """Convert a value to a float, return default if invalid."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_currency(amount):
    """Format a number as Kenyan Shillings (KSh)."""
    return f"KSh {amount:,.2f}"


def calculate_risk_score(income, loan_amount, credit_score, existing_debt):
    """Mock risk score calculation (replace with real model)."""
    # Very simple example – replace with your actual logic
    ratio = loan_amount / max(income, 1)
    score = 100 - (ratio * 20) - (existing_debt / 10000) + (credit_score / 10)
    return max(0, min(100, score))


def explain_risk_with_citations(risk_score, income, loan_amount, credit_score, existing_debt):
    """Return a human-readable explanation of the risk score with citations."""
    if risk_score >= 70:
        level = "Low Risk"
        color = "green"
        advice = "The applicant appears financially stable and likely to repay."
    elif risk_score >= 40:
        level = "Medium Risk"
        color = "orange"
        advice = "Some risk factors present. Consider adjusting loan terms."
    else:
        level = "High Risk"
        color = "red"
        advice = "Significant risk indicators. Recommend further review or collateral."
    
    explanation = f"""
    **Risk Level:** <span style='color:{color}'>{level}</span><br>
    - **Debt-to-Income Ratio:** {loan_amount / max(income, 1):.2f}<br>
    - **Credit Score Factor:** {credit_score} points<br>
    - **Existing Debt:** {format_currency(existing_debt)}<br>
    <br>
    {advice}<br>
    <br>
    <small>† Based on financial rules and historical data.</small>
    """
    return explanation


def suggest_improvements(risk_score, income, loan_amount, credit_score, existing_debt):
    """Suggest actionable improvements to reduce risk."""
    suggestions = []
    if loan_amount / max(income, 1) > 0.5:
        suggestions.append("• Consider reducing the loan amount or extending the repayment period to lower monthly burden.")
    if existing_debt > 100000:
        suggestions.append("• Pay down existing debt before applying for a new loan.")
    if credit_score < 600:
        suggestions.append("• Work on improving your credit score by paying bills on time.")
    if income < loan_amount * 0.2:
        suggestions.append("• Increase income or provide additional collateral.")
    
    if not suggestions:
        suggestions.append("• Your profile looks good. Maintain timely payments.")
    
    return " ".join(suggestions)
