# ==============================
# services/cars_service.py
# Real Supabase implementation
# ==============================
import streamlit as st
from datetime import datetime


# ── Read Operations ───────────────────────────────

def get_all_cars(supabase):
    """Fetch all car listings from Supabase."""
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
    """Return a single car by its UUID."""
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
    """Return featured car listings."""
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
    """Filter cars based on search criteria."""
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

        # Text search (client-side for simplicity)
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
    """Return sorted list of unique car makes."""
    try:
        result = supabase.table("cars").select("make").execute()
        makes  = sorted(set(c["make"] for c in result.data or []))
        return makes
    except Exception:
        return []


def get_price_range(supabase):
    """Return min and max price across all cars."""
    try:
        result = supabase.table("cars").select("price").execute()
        prices = [c["price"] for c in result.data or []]
        if not prices:
            return 0, 10_000_000
        return min(prices), max(prices)
    except Exception:
        return 0, 10_000_000


def get_year_range(supabase):
    """Return min and max year across all cars."""
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
    """
    Upload image to Supabase Storage.
    Returns the public URL or empty string on failure.
    """
    try:
        # Make filename unique using timestamp
        ext       = filename.rsplit(".", 1)[-1].lower()
        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"car_{ts}.{ext}"

        supabase.storage.from_("car-images").upload(
            safe_name,
            file_bytes,
            {"content-type": f"image/{ext}"}
        )

        # Get public URL
        url_data = supabase.storage.from_(
            "car-images"
        ).get_public_url(safe_name)

        return url_data
    except Exception as e:
        st.error(f"Image upload failed: {e}")
        return ""


def insert_car(supabase, car_data: dict) -> bool:
    """Insert a new car listing. Returns True on success."""
    try:
        supabase.table("cars").insert(car_data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save car: {e}")
        return False


def update_car(supabase, car_id: str, car_data: dict) -> bool:
    """Update an existing car listing."""
    try:
        supabase.table("cars").update(car_data).eq(
            "id", car_id
        ).execute()
        return True
    except Exception as e:
        st.error(f"Failed to update car: {e}")
        return False


def delete_car(supabase, car_id: str) -> bool:
    """Delete a car listing."""
    try:
        supabase.table("cars").delete().eq("id", car_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete car: {e}")
        return False


def increment_views(supabase, car_id: str):
    """Increment view count for a car."""
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
    """AI valuation based on age, mileage and condition."""
    base_price  = car.get("price", 0)
    current_year = datetime.now().year
    age         = current_year - car.get("year", current_year)

    depreciation = max(0.3, 1 - (0.15 * age))

    mileage_over   = max(0, (car.get("mileage", 0) - 30_000) / 5_000)
    mileage_penalty = max(0.6, 1 - (mileage_over * 0.01))

    condition_multiplier = {
        "Excellent": 1.05,
        "Very Good": 1.00,
        "Good":      0.95,
        "Fair":      0.85
    }.get(car.get("condition", "Good"), 0.95)

    return int(base_price * depreciation * mileage_penalty
               * condition_multiplier)
