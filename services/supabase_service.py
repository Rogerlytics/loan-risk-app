# ==============================
# services/supabase_service.py
# ==============================
import streamlit as st
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import bcrypt

# Initialize client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def sign_in(email: str, password: str):
    """Authenticate user with email and password."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        user = response.user
        if user:
            # Fetch custom role from 'users' table
            user_data = supabase.table("users").select("role").eq("id", user.id).execute()
            role = "user"
            if user_data.data and len(user_data.data) > 0:
                role = user_data.data[0].get("role", "user")
            return {
                "id": user.id,
                "email": user.email,
                "role": role
            }
        return None
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None


def sign_up(email: str, password: str):
    """Create a new user account."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        user = response.user
        if user:
            # Insert into 'users' table with default role 'user'
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


def sign_out():
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass  # ignore if already signed out


def get_current_user():
    """Return currently logged-in user from session."""
    user = st.session_state.get("user")
    if user:
        return user
    return None


def log_action(supabase_client, user_id: str, email: str, action: str, details: str = ""):
    """Log user action – fails silently if no permission or table missing."""
    try:
        supabase_client.table("audit_logs").insert({
            "user_id": user_id,
            "email": email,
            "action": action,
            "details": details,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        # Silently ignore permission errors (e.g., if RLS denies insert)
        print(f"Failed to log action: {e}")


# ---------- Message functions ----------
def get_all_messages(supabase_client):
    """Fetch all messages from the database."""
    response = supabase_client.table("messages").select("*").order("timestamp").execute()
    return response.data


def get_user_messages(supabase_client, user_id):
    """Fetch messages for a specific user."""
    response = supabase_client.table("messages").select("*").eq("user_id", user_id).order("timestamp").execute()
    return response.data


def send_message(supabase_client, user_id, user_email, message):
    """Send a new message from user to support."""
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
    """Send a reply to a specific message."""
    supabase_client.table("messages").update({
        "reply": reply_text,
        "replied_at": datetime.utcnow().isoformat(),
        "read_by_customer": False
    }).eq("id", message_id).execute()


def mark_messages_as_read(supabase_client, user_id):
    """Mark all admin replies as read by customer."""
    supabase_client.table("messages").update({
        "read_by_customer": True
    }).eq("user_id", user_id).eq("read_by_customer", False).execute()


def get_message_count(supabase_client, user_id):
    """Get total message count for a user."""
    response = supabase_client.table("messages").select("id", count="exact").eq("user_id", user_id).execute()
    return response.count


def get_total_message_count(supabase_client):
    """Get total messages across all users."""
    response = supabase_client.table("messages").select("id", count="exact").execute()
    return response.count


# ---------- User management ----------
def get_all_users(supabase_client):
    """Fetch all users from the 'users' table."""
    response = supabase_client.table("users").select("*").execute()
    return response.data


def update_user_role(supabase_client, user_id, new_role):
    """Update user role."""
    try:
        supabase_client.table("users").update({"role": new_role}).eq("id", user_id).execute()
        return True, "Role updated successfully"
    except Exception as e:
        return False, str(e)


def get_audit_logs(supabase_client, limit=100):
    """Fetch recent audit logs – returns empty list if permission denied or table missing."""
    try:
        response = supabase_client.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        # Permission denied or table doesn't exist – return empty list gracefully
        print(f"Could not fetch audit logs: {e}")
        return []
