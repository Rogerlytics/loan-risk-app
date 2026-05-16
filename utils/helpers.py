# ==============================
# utils/helpers.py
# ==============================
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import html
import re


# ── Input Sanitisation ──────────────────────────

def sanitise_email(email: str) -> str:
    """Lowercase, strip whitespace, validate format."""
    email = email.strip().lower()
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email address.")
    return email


def sanitise_password(password: str) -> str:
    """Enforce minimum password rules."""
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if len(password) > 128:
        raise ValueError("Password too long. Maximum 128 characters.")
    return password


def sanitise_text(text: str, max_length: int = 500) -> str:
    """Strip whitespace, escape HTML, enforce max length."""
    text = text.strip()
    text = html.escape(text)
    if len(text) > max_length:
        raise ValueError(
            f"Message too long. Maximum {max_length} characters allowed."
        )
    if not text:
        raise ValueError("Message cannot be empty.")
    return text


def sanitise_number(
    value, min_val=0, max_val=1_000_000, label="Value"
) -> float:
    """Ensure a number is within acceptable bounds."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a valid number.")
    if value < min_val or value > max_val:
        raise ValueError(
            f"{label} must be between {min_val:,} and {max_val:,}."
        )
    return value


# ── Risk Explanation ─────────────────────────────

def explain_risk_with_citations(
    df: pd.DataFrame,
) -> Tuple[List[str], List[Dict[str, str]]]:
    reasons   = []
    citations = []
    if df['income_to_loan_ratio'][0] < 0.3:
        reasons.append("Low income vs loan amount")
        citations.append({"source": "Lending Policy §2.4", "confidence": "High"})
    if df['loan_to_value_ratio'][0] > 0.8:
        reasons.append("Loan too high vs car value")
        citations.append({"source": "Asset Valuation Guide", "confidence": "Medium"})
    if df['previous_defaults'][0] > 0:
        reasons.append("Previous defaults on record")
        citations.append({"source": "Credit History", "confidence": "High"})
    if not reasons:
        reasons.append("Strong applicant profile")
        citations.append({"source": "All checks passed", "confidence": "High"})
    return reasons, citations


def suggest_improvements(df: pd.DataFrame) -> List[str]:
    suggestions = []
    if df['income_to_loan_ratio'][0] < 0.3:
        suggestions.append("Increase income or reduce loan amount.")
    if df['loan_to_value_ratio'][0] > 0.8:
        suggestions.append("Provide additional collateral or reduce loan amount.")
    return suggestions


# ── Time Formatting ──────────────────────────────

def relative_time(ts: str) -> str:
    try:
        dt  = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() // 60)
            return f"{mins} min ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime("%b %d, %I:%M %p")
    except Exception:
        return ts


# ── Currency Formatting ──────────────────────────

def format_currency(amount: float, currency: str = "KES") -> str:
    """Format a number as currency string."""
    return f"{currency} {amount:,.2f}"
