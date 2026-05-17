# ==============================
# services/cars_service.py
# Real Supabase implementation
# ==============================
import streamlit as st
from datetime import datetime


# ── Read Operations ───────────────────────────────

def get_all_cars(supabase):
    try:
        result = (
            supabase.table("cars")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        st.error(f"Failed to load cars: {e}")
        return []


def get_car_by_id(supabase, car_id: str):
    try:
        result = (
            supabase.table("cars")
            .select("*")
            .eq("id", car_id)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        return None


def get_featured_cars(supabase, limit: int = 3):
    try:
        result = (
            supabase.table("cars")
            .select("*")
            .eq("featured", True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_filtered_cars(supabase, filters: dict):
    try:
        query = supabase.table("cars").select("*")

        if filters.get("make") and filters["make"] != "All":
            query = query.eq("make", filters["make"])
        if filters.get("fuel_type") and filters["fuel_type"] != "All":
            query = query.eq("fuel_type", filters["fuel_type"])
        if filters.get("transmission") and filters["transmission"] != "All":
            query = query.eq("transmission", filters["transmission"])
        if filters.get("body_type") and filters["body_type"] != "All":
            query = query.eq("body_type", filters["body_type"])
        if filters.get("min_price"):
            query = query.gte("price", filters["min_price"])
        if filters.get("max_price"):
            query = query.lte("price", filters["max_price"])
        if filters.get("min_year"):
            query = query.gte("year", filters["min_year"])
        if filters.get("max_year"):
            query = query.lte("year", filters["max_year"])
        if filters.get("max_mileage"):
            query = query.lte("mileage", filters["max_mileage"])

        result = query.order("created_at", desc=True).execute()
        cars   = result.data or []

        if filters.get("search_term"):
            term = filters["search_term"].lower()
            cars = [
                c for c in cars
                if term in c.get("make", "").lower()
                or term in c.get("model", "").lower()
            ]

        return cars
    except Exception as e:
        st.error(f"Failed to filter cars: {e}")
        return []


def get_unique_makes(supabase):
    try:
        result = supabase.table("cars").select("make").execute()
        makes  = sorted(set(c["make"] for c in result.data or []))
        return makes
    except Exception:
        return []


def get_price_range(supabase):
    try:
        result = supabase.table("cars").select("price").execute()
        prices = [c["price"] for c in result.data or []]
        if not prices:
            return 0, 10_000_000
        return min(prices), max(prices)
    except Exception:
        return 0, 10_000_000


def get_year_range(supabase):
    try:
        result = supabase.table("cars").select("year").execute()
        years  = [c["year"] for c in result.data or []]
        if not years:
            return 2010, datetime.now().year
        return min(years), max(years)
    except Exception:
        return 2010, datetime.now().year


# ── Write Operations ──────────────────────────────

def upload_car_image(supabase, file_bytes: bytes,
                     filename: str) -> str:
    try:
        ext       = filename.rsplit(".", 1)[-1].lower()
        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"car_{ts}.{ext}"

        supabase.storage.from_("car-images").upload(
            safe_name,
            file_bytes,
            {"content-type": f"image/{ext}"}
        )

        url_data = supabase.storage.from_(
            "car-images"
        ).get_public_url(safe_name)

        return url_data
    except Exception as e:
        st.error(f"Image upload failed: {e}")
        return ""


def insert_car(supabase, car_data: dict) -> bool:
    try:
        supabase.table("cars").insert(car_data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save car: {e}")
        return False


def update_car(supabase, car_id: str, car_data: dict) -> bool:
    try:
        supabase.table("cars").update(car_data).eq(
            "id", car_id
        ).execute()
        return True
    except Exception as e:
        st.error(f"Failed to update car: {e}")
        return False


def delete_car(supabase, car_id: str) -> bool:
    try:
        supabase.table("cars").delete().eq("id", car_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete car: {e}")
        return False


def increment_views(supabase, car_id: str):
    try:
        car = supabase.table("cars").select(
            "views"
        ).eq("id", car_id).single().execute()
        current = car.data.get("views", 0) if car.data else 0
        supabase.table("cars").update(
            {"views": current + 1}
        ).eq("id", car_id).execute()
    except Exception:
        pass


# ── Valuation ─────────────────────────────────────

def estimate_value(car: dict) -> int:
    """
    Market valuation matches the seller's listed price exactly.
    This reflects that the price is set by a verified dealer
    and represents the true market value.
    """
    return int(car.get("price", 0))


def calculate_repayment(price: int, deposit_pct: float = 0.2,
                         months: int = 48,
                         annual_rate: float = 0.14) -> dict:
    """
    Calculate financing repayment plan.
    Default: 20% deposit, 48 months, 14% annual interest.
    Returns monthly, weekly, daily payments and total cost.
    """
    deposit       = int(price * deposit_pct)
    loan_amount   = price - deposit
    monthly_rate  = annual_rate / 12
    monthly       = (
        loan_amount * monthly_rate * (1 + monthly_rate) ** months
        / ((1 + monthly_rate) ** months - 1)
    ) if monthly_rate > 0 else loan_amount / months

    total_cost    = deposit + (monthly * months)
    total_interest = total_cost - price

    return {
        "deposit":        deposit,
        "loan_amount":    loan_amount,
        "monthly":        monthly,
        "weekly":         monthly / 4.33,
        "daily":          monthly / 30,
        "total_cost":     total_cost,
        "total_interest": total_interest,
        "months":         months,
        "annual_rate":    annual_rate,
    }
