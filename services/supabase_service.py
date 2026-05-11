# ==============================
# services/supabase_service.py
# ==============================
import streamlit as st
from datetime import datetime


# ── Audit Logging ─────────────────────────────────

def log_action(
    supabase, user_id: str, email: str,
    action: str, details: str = ""
):
    """
    Insert audit log via SECURITY DEFINER RPC function.
    Bypasses RLS — always works regardless of session state.
    Fails silently — never crashes the app.
    """
    try:
        supabase.rpc(
            "insert_audit_log",
            {
                "p_user_id": user_id,
                "p_email":   email,
                "p_action":  action,
                "p_details": details
            }
        ).execute()
    except Exception:
        pass


def get_audit_logs(supabase, limit: int = 100):
    """Fetch most recent audit logs — admin only."""
    try:
        return (
            supabase.table("audit_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute().data
        )
    except Exception:
        return []


# ── Auth ──────────────────────────────────────────

def login_user(supabase, email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
            return {
                "id":            res.user.id,
                "email":         res.user.email,
                "access_token":  res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "confirmed":     res.user.email_confirmed_at is not None
            }
    except Exception as e:
        error_msg = str(e).lower()
        if "email not confirmed" in error_msg:
            return {"error": "email_not_confirmed"}
        if "invalid login" in error_msg or \
                "invalid credentials" in error_msg:
            return {"error": "invalid_credentials"}
        st.error(f"Login error: {e}")
    return None


def signup_user(supabase, email: str, password: str):
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if res.user:
            identities = getattr(res.user, "identities", None)
            if identities is not None and len(identities) == 0:
                return {"error": "already_registered"}
            confirmed = res.user.email_confirmed_at is not None
            return {
                "id":        res.user.id,
                "email":     res.user.email,
                "confirmed": confirmed
            }
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or \
                "already exists" in error_msg or \
                "user already registered" in error_msg:
            return {"error": "already_registered"}
        st.error(f"Signup error: {e}")
    return None


def resend_confirmation_email(supabase, email: str) -> bool:
    try:
        supabase.auth.resend({
            "type":  "signup",
            "email": email
        })
        return True
    except Exception as e:
        st.error(f"Failed to resend confirmation: {e}")
        return False


# ── Profiles ──────────────────────────────────────

def get_user_role(supabase, user_id: str) -> str:
    try:
        profile = (
            supabase.table("profiles")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return profile.data.get("role", "user").lower()
    except Exception:
        return "user"


def get_all_users(supabase):
    """Fetch all users — admin only via RLS policy."""
    try:
        return (
            supabase.table("profiles")
            .select("id, email, role")
            .order("email", desc=False)
            .execute().data
        )
    except Exception:
        return []


def update_user_role(supabase, target_user_id: str, new_role: str):
    """
    Update a user's role via secure RPC function.
    Returns (success: bool, message: str)
    """
    try:
        supabase.rpc(
            "update_user_role",
            {
                "target_user_id": target_user_id,
                "new_role":       new_role
            }
        ).execute()
        return True, "Role updated successfully."
    except Exception as e:
        error_msg = str(e)
        if "only admins can change roles" in error_msg.lower():
            return False, "Permission denied: only admins can change roles."
        if "cannot change your own role" in error_msg.lower():
            return False, "You cannot change your own role."
        if "invalid role" in error_msg.lower():
            return False, "Invalid role value."
        return False, f"Failed to update role: {error_msg}"


# ── Messages ──────────────────────────────────────

def get_user_messages(supabase, user_id: str):
    try:
        return (
            supabase.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=False)
            .execute().data
        )
    except Exception:
        return []


def get_all_messages(supabase):
    try:
        return (
            supabase.table("messages")
            .select("*")
            .order("timestamp", desc=False)
            .execute().data
        )
    except Exception:
        return []


def send_message(supabase, user_id: str, email: str, message: str):
    try:
        return (
            supabase.table("messages").insert({
                "user_id":          user_id,
                "name":             email,
                "email":            email,
                "message":          message,
                "status":           "sent",
                "timestamp":        datetime.now().isoformat(),
                "read_by_customer": False,
                "delivered":        True
            }).execute()
        )
    except Exception as e:
        st.error(f"Failed to send message: {e}")
        return None


def send_reply(supabase, msg_id: str, reply_text: str):
    try:
        return (
            supabase.table("messages").update({
                "reply":      reply_text,
                "replied_at": datetime.now().isoformat(),
                "status":     "replied"
            }).eq("id", msg_id).execute()
        )
    except Exception as e:
        st.error(f"Failed to send reply: {e}")
        return None


def get_unread_reply_count(supabase, user_id: str) -> int:
    try:
        msgs = (
            supabase.table("messages")
            .select("id, reply, read_by_customer")
            .eq("user_id", user_id)
            .execute().data
        )
        return sum(
            1 for m in msgs
            if m.get("reply") and not m.get("read_by_customer", False)
        )
    except Exception:
        return 0


def mark_messages_as_read(supabase, user_id: str):
    try:
        supabase.table("messages") \
            .update({"read_by_customer": True}) \
            .eq("user_id", user_id) \
            .eq("read_by_customer", False) \
            .execute()
    except Exception:
        pass
