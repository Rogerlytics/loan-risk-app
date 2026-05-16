# ==============================
# views/car_marketplace.py
# ==============================
import streamlit as st
from services.cars_service import (
    get_all_cars,
    get_featured_cars,
    get_filtered_cars,
    get_unique_makes,
    get_price_range,
    get_year_range,
    get_car_by_id,
    estimate_value,
    increment_views
)


def _car_card(car, supabase, key_prefix="grid"):
    """Render a single car listing card."""
    badge = ""
    if car.get("featured"):
        badge = (
            '<span style="background:#1d4ed8; color:#bfdbfe; '
            'font-size:10px; font-weight:700; padding:2px 8px; '
            'border-radius:20px; margin-left:6px;">FEATURED</span>'
        )

    condition_colour = {
        "Excellent": "#22c55e",
        "Very Good": "#60a5fa",
        "Good":      "#f59e0b",
        "Fair":      "#ef4444"
    }.get(car.get("condition", "Good"), "#94A3B8")

    # Image — real or placeholder
    img_html = ""
    if car.get("image_url"):
        img_html = (
            f'<img src="{car["image_url"]}" '
            f'alt="{car["make"]} {car["model"]}" '
            f'style="width:100%; height:200px; object-fit:cover;">'
        )
    else:
        img_html = (
            '<div style="width:100%; height:200px; background:#0f1e30; '
            'display:flex; align-items:center; justify-content:center; '
            'font-size:48px; color:#334155;">🚗</div>'
        )

    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#111827,#0b1220);
        border:1px solid #1e293b; border-radius:16px;
        overflow:hidden; margin-bottom:4px;
        transition:border-color 0.2s;">
        {img_html}
        <div style="padding:14px;">
            <div style="font-size:15px; font-weight:700;
                        color:#F0F4F8; margin-bottom:4px;">
                {car['year']} {car['make']} {car['model']}{badge}
            </div>
            <div style="font-size:22px; font-weight:800;
                        color:#3B82F6; margin-bottom:10px;">
                KES {car['price']:,}
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:5px;
                        margin-bottom:10px;">
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px; border-radius:20px;
                    border:1px solid #1e293b;">{car['transmission']}</span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px; border-radius:20px;
                    border:1px solid #1e293b;">{car['fuel_type']}</span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px; border-radius:20px;
                    border:1px solid #1e293b;">{car['mileage']:,} km</span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px; border-radius:20px;
                    border:1px solid #1e293b;">{car['engine_size']}</span>
            </div>
            <div style="display:flex; align-items:center;
                        justify-content:space-between;">
                <span style="color:{condition_colour}; font-size:12px;
                             font-weight:600;">● {car['condition']}</span>
                <span style="color:#64748B; font-size:12px;">
                    📍 {car['location']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "View Details",
        key=f"{key_prefix}_view_{car['id']}",
        use_container_width=True
    ):
        st.session_state.selected_car_id = car['id']
        increment_views(supabase, car['id'])
        st.rerun()


def _car_detail(car, supabase):
    """Render full car detail view."""
    if st.button("← Back to Listings", key="back_to_listings"):
        st.session_state.selected_car_id = None
        st.rerun()

    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <div style="font-size:28px; font-weight:800; color:#F0F4F8;
                    margin-bottom:4px;">
            {car['year']} {car['make']} {car['model']}
        </div>
        <div style="color:#94A3B8; font-size:14px;">
            {car.get('body_type','')} · {car.get('seller_type','')}
            · {car.get('location','')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_img, col_info = st.columns([3, 2])

    with col_img:
        if car.get("image_url"):
            st.image(car["image_url"], use_column_width=True)
        else:
            st.markdown("""
            <div style="background:#0f1e30; border:1px solid #1e293b;
                border-radius:12px; height:300px; display:flex;
                align-items:center; justify-content:center;
                font-size:64px; color:#334155;">🚗</div>
            """, unsafe_allow_html=True)

        # AI Valuation
        estimated = estimate_value(car)
        diff      = estimated - car['price']
        diff_txt  = (
            f"KES {abs(diff):,} "
            f"{'below' if diff < 0 else 'above'} market estimate"
        )
        diff_col = "#22c55e" if diff >= 0 else "#ef4444"

        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px solid #1e293b; border-radius:12px;
            padding:16px; margin-top:12px;">
            <div style="color:#94A3B8; font-size:11px; margin-bottom:6px;
                        text-transform:uppercase; letter-spacing:0.08em;">
                AI Market Valuation
            </div>
            <div style="font-size:24px; font-weight:800; color:#3B82F6;">
                KES {estimated:,}
            </div>
            <div style="color:{diff_col}; font-size:13px; margin-top:4px;">
                {diff_txt}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px solid #1e293b; border-radius:12px; padding:20px;">
            <div style="font-size:30px; font-weight:800; color:#3B82F6;
                        margin-bottom:16px;">KES {car['price']:,}</div>
        """, unsafe_allow_html=True)

        specs = [
            ("Year",         car.get('year', '')),
            ("Mileage",      f"{car.get('mileage', 0):,} km"),
            ("Fuel",         car.get('fuel_type', '')),
            ("Transmission", car.get('transmission', '')),
            ("Engine",       car.get('engine_size', '')),
            ("Body",         car.get('body_type', '')),
            ("Color",        car.get('color', '')),
            ("Condition",    car.get('condition', '')),
            ("Seller",       car.get('seller_type', '')),
            ("Views",        f"{car.get('views', 0):,}"),
        ]

        for label, value in specs:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between;
                        padding:8px 0; border-bottom:1px solid #1e293b;">
                <span style="color:#64748B; font-size:13px;">{label}</span>
                <span style="color:#F0F4F8; font-size:13px;
                             font-weight:600;">{value}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Contact Seller",
            use_container_width=True,
            key="contact_seller_btn"
        ):
            st.session_state.draft_message = (
                f"Hi, I'm interested in the {car['year']} "
                f"{car['make']} {car['model']} listed at "
                f"KES {car['price']:,}. Is it still available?"
            )
            st.success(
                "Message drafted! Go to the Contact page to send it."
            )

    # Description
    if car.get("description"):
        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px solid #1e293b; border-radius:12px;
            padding:20px; margin-top:16px;">
            <div style="color:#60A5FA; font-size:13px; font-weight:700;
                        margin-bottom:10px; text-transform:uppercase;
                        letter-spacing:0.05em;">Description</div>
            <div style="color:#E2E8F0; font-size:14px; line-height:1.7;">
                {car['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_car_marketplace(supabase):
    """Main car marketplace page."""

    if "selected_car_id" not in st.session_state:
        st.session_state.selected_car_id = None

    # ── Detail view ──
    if st.session_state.selected_car_id:
        car = get_car_by_id(supabase, st.session_state.selected_car_id)
        if car:
            _car_detail(car, supabase)
        else:
            st.error("Car not found.")
            st.session_state.selected_car_id = None
        return

    # ── Filters — always visible top row ──
    st.markdown(
        '<div class="section-heading">Find Your Car</div>',
        unsafe_allow_html=True
    )

    with st.container():
        f1, f2, f3, f4, f5 = st.columns(5)

        with f1:
            search_term = st.text_input(
                "Search",
                placeholder="Make or model...",
                key="mp_search",
                label_visibility="collapsed"
            )
            st.caption("Search")

        with f2:
            makes = ["All Makes"] + get_unique_makes(supabase)
            selected_make = st.selectbox(
                "Make", makes, key="mp_make",
                label_visibility="collapsed"
            )
            st.caption("Make")

        with f3:
            fuel_type = st.selectbox(
                "Fuel",
                ["All Fuel", "Petrol", "Diesel", "Hybrid", "Electric"],
                key="mp_fuel",
                label_visibility="collapsed"
            )
            st.caption("Fuel Type")

        with f4:
            transmission = st.selectbox(
                "Transmission",
                ["All Trans.", "Automatic", "Manual", "CVT"],
                key="mp_trans",
                label_visibility="collapsed"
            )
            st.caption("Transmission")

        with f5:
            body_type = st.selectbox(
                "Body",
                ["All Types", "Sedan", "SUV", "Hatchback",
                 "Pickup", "Wagon", "MPV", "Coupe"],
                key="mp_body",
                label_visibility="collapsed"
            )
            st.caption("Body Type")

    # Price and year row
    p1, p2 = st.columns(2)
    with p1:
        min_price, max_price = get_price_range(supabase)
        if min_price == max_price:
            min_price = 0
            max_price = 10_000_000
        price_range = st.slider(
            "Price Range (KES)",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            step=50_000,
            format="KES %d",
            key="mp_price"
        )
    with p2:
        min_year, max_year = get_year_range(supabase)
        if min_year == max_year:
            min_year -= 1
        year_range = st.slider(
            "Year Range",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            key="mp_year"
        )

    st.markdown(
        '<hr style="border-color:#1e293b; margin:12px 0 16px 0;">',
        unsafe_allow_html=True
    )

    # Build filters dict
    filters = {
        "min_price": price_range[0],
        "max_price": price_range[1],
        "min_year":  year_range[0],
        "max_year":  year_range[1],
    }
    if search_term:
        filters["search_term"] = search_term
    if selected_make != "All Makes":
        filters["make"] = selected_make
    if fuel_type != "All Fuel":
        filters["fuel_type"] = fuel_type
    if transmission != "All Trans.":
        filters["transmission"] = transmission
    if body_type != "All Types":
        filters["body_type"] = body_type

    # ── Featured section ──
    featured = get_featured_cars(supabase, limit=3)
    if featured and not any(filters.get(k) for k in [
        "search_term", "make", "fuel_type", "transmission", "body_type"
    ]):
        st.markdown("""
        <div style="color:#F0F4F8; font-size:16px; font-weight:700;
                    margin-bottom:12px;">⭐ Featured</div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for i, car in enumerate(featured):
            with cols[i]:
                _car_card(car, supabase, key_prefix="featured")
        st.markdown(
            '<hr style="border-color:#1e293b; margin:16px 0;">',
            unsafe_allow_html=True
        )

    # ── All listings ──
    cars = get_filtered_cars(supabase, filters)

    st.markdown(f"""
    <div style="color:#94A3B8; font-size:13px; margin-bottom:16px;">
        Showing <b style="color:#F0F4F8;">{len(cars)}</b>
        vehicle{"s" if len(cars) != 1 else ""}
    </div>
    """, unsafe_allow_html=True)

    if not cars:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px dashed #1e293b; border-radius:16px;
            padding:48px; text-align:center; margin-top:20px;">
            <div style="font-size:40px; margin-bottom:12px;">🔍</div>
            <div style="color:#F0F4F8; font-size:18px; font-weight:600;
                        margin-bottom:8px;">No cars found</div>
            <div style="color:#94A3B8; font-size:14px;">
                Try adjusting your filters or add new listings.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    cols = st.columns(3)
    for i, car in enumerate(cars):
        with cols[i % 3]:
            _car_card(car, supabase, key_prefix="grid")
