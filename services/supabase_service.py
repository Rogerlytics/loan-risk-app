# ==============================
# services/supabase_service.py
# ==============================
import streamlit as st
from datetime import datetime


# ── Auth ─────────────────────────────────────────

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
                "refresh_token": res.session.refresh_token
            }
    except Exception as e:
        st.error(f"Login error: {e}")
    return None


def signup_user(supabase, email: str, password: str):
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if res.user:
            return {
                "id":    res.user.id,
                "email": res.user.email
            }
    except Exception as e:
        st.error(f"Signup error: {e}")
    return None


# ── Profiles ─────────────────────────────────────

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


# ── Messages ─────────────────────────────────────

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
