# ==============================
# services/supabase_service.py
# ==============================
import streamlit as st
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Auth functions (used by auth/login.py) ----------
def login_user(email: str, password: str):
    """Authenticate and return user dict with role and tokens."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        user = response.user
        if user:
            user_data = supabase.table("users").select("role").eq("id", user.id).execute()
            role = user_data.data[0].get("role", "user") if user_data.data else "user"
            return {
                "id": user.id,
                "email": user.email,
                "role": role,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
        return None
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None

def signup_user(email: str, password: str):
    """Create a new user account."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        user = response.user
        if user:
            supabase.table("users").insert({
                "id": user.id,
                "email": email,
                "role": "user",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return {
                "id": user.id,
                "email": user.email,
                "role": "user"
            }
        return None
    except Exception as e:
        st.error(f"Signup error: {str(e)}")
        return None

def get_user_role(user_id: str) -> str:
    """Return role of a user."""
    try:
        result = supabase.table("users").select("role").eq("id", user_id).execute()
        if result.data:
            return result.data[0].get("role", "user")
        return "user"
    except:
        return "user"

def get_current_user():
    """Return currently logged-in user from session."""
    return st.session_state.get("user")

def get_unread_reply_count(supabase_client, user_id: str) -> int:
    """Count unread admin replies for a user."""
    try:
        resp = supabase_client.table("messages").select("id", count="exact").eq("user_id", user_id).eq("read_by_customer", False).execute()
        return resp.count if resp.count else 0
    except:
        return 0

def log_action(supabase_client, user_id: str, email: str, action: str, details: str = ""):
    """Log action – fails silently if no permission."""
    try:
        supabase_client.table("audit_logs").insert({
            "user_id": user_id,
            "email": email,
            "action": action,
            "details": details,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"Failed to log action: {e}")

# ---------- Message functions ----------
def get_all_messages(supabase_client):
    return supabase_client.table("messages").select("*").order("timestamp").execute().data

def get_user_messages(supabase_client, user_id):
    return supabase_client.table("messages").select("*").eq("user_id", user_id).order("timestamp").execute().data

def send_message(supabase_client, user_id, user_email, message):
    supabase_client.table("messages").insert({
        "user_id": user_id,
        "email": user_email,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "read_by_customer": True,
        "reply": None,
        "replied_at": None
    }).execute()

def send_reply(supabase_client, message_id, reply_text):
    supabase_client.table("messages").update({
        "reply": reply_text,
        "replied_at": datetime.utcnow().isoformat(),
        "read_by_customer": False
    }).eq("id", message_id).execute()

def mark_messages_as_read(supabase_client, user_id):
    supabase_client.table("messages").update({"read_by_customer": True}).eq("user_id", user_id).eq("read_by_customer", False).execute()

def get_message_count(supabase_client, user_id):
    resp = supabase_client.table("messages").select("id", count="exact").eq("user_id", user_id).execute()
    return resp.count

def get_total_message_count(supabase_client):
    resp = supabase_client.table("messages").select("id", count="exact").execute()
    return resp.count

# ---------- User management ----------
def get_all_users(supabase_client):
    return supabase_client.table("users").select("*").execute().data

def update_user_role(supabase_client, user_id, new_role):
    try:
        supabase_client.table("users").update({"role": new_role}).eq("id", user_id).execute()
        return True, "Role updated"
    except Exception as e:
        return False, str(e)

def get_audit_logs(supabase_client, limit=100):
    try:
        resp = supabase_client.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return resp.data
    except:
        return []
