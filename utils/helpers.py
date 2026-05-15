# ==============================
# utils/helpers.py
# ==============================
import streamlit as st
from datetime import datetime
import re


def apply_custom_css():
    """Global custom CSS – matches original theme."""
    st.markdown("""
    <style>
    .stApp { background: #0B1220; }
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
    .stButton > button {
        background: linear-gradient(145deg, #1e3a5f, #0f1e30);
        border: 1px solid #2563eb;
        border-radius: 12px;
        color: #F0F4F8;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }
    .stTextInput > div > div > input {
        background-color: #0f1e30 !important;
        border: 1px solid #1e293b !important;
        color: #F0F4F8 !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def relative_time(timestamp_str):
    if not timestamp_str:
        return "Just now"
    try:
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        sec = diff.total_seconds()
        if sec < 60:
            return "Just now"
        elif sec < 3600:
            mins = int(sec // 60)
            return f"{mins} min{'s' if mins > 1 else ''} ago"
        elif sec < 86400:
            hrs = int(sec // 3600)
            return f"{hrs} hour{'s' if hrs > 1 else ''} ago"
        elif sec < 604800:
            days = int(sec // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime("%d %b %Y")
    except:
        return "Unknown"


def sanitise_text(text, max_length=500):
    if not text:
        return ""
    clean = re.sub(r'<[^>]*>', '', text)
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    return clean.strip()


def sanitise_number(value, default=0):
    try:
        return float(value)
    except:
        return default


def format_currency(amount):
    return f"KSh {amount:,.2f}"


def calculate_risk_score(income, loan_amount, credit_score, existing_debt):
    ratio = loan_amount / max(income, 1)
    score = 100 - (ratio * 20) - (existing_debt / 10000) + (credit_score / 10)
    return max(0, min(100, score))


def explain_risk_with_citations(risk_score, income, loan_amount, credit_score, existing_debt):
    if risk_score >= 70:
        level = "Low Risk"
        color = "green"
        advice = "The applicant appears financially stable."
    elif risk_score >= 40:
        level = "Medium Risk"
        color = "orange"
        advice = "Some risk factors present. Consider adjusting terms."
    else:
        level = "High Risk"
        color = "red"
        advice = "Significant risk indicators. Recommend further review."
    return f"""
    <span style='color:{color}'><b>{level}</b></span><br>
    Debt-to-Income Ratio: {loan_amount / max(income, 1):.2f}<br>
    Credit Score: {credit_score}<br>
    Existing Debt: {format_currency(existing_debt)}<br><br>
    {advice}
    """


def suggest_improvements(risk_score, income, loan_amount, credit_score, existing_debt):
    suggestions = []
    if loan_amount / max(income, 1) > 0.5:
        suggestions.append("• Reduce loan amount or extend repayment period.")
    if existing_debt > 100000:
        suggestions.append("• Pay down existing debt before applying.")
    if credit_score < 600:
        suggestions.append("• Improve credit score by paying bills on time.")
    if not suggestions:
        suggestions.append("• Your profile looks good. Maintain timely payments.")
    return " ".join(suggestions)
