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
    estimate_value
)


def _car_card(car):
    """Render a single car listing card."""
    badge = ""
    if car.get("featured"):
        badge = '<span style="background:#1d4ed8; color:#bfdbfe; ' \
                'font-size:10px; font-weight:700; padding:2px 8px; ' \
                'border-radius:20px; margin-left:8px;">FEATURED</span>'

    condition_colour = {
        "Excellent": "#22c55e",
        "Very Good": "#60a5fa",
        "Good":      "#f59e0b",
        "Fair":      "#ef4444"
    }.get(car["condition"], "#94A3B8")

    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#111827,#0b1220);
        border:1px solid #1e293b; border-radius:16px;
        overflow:hidden; margin-bottom:16px;
        transition:border-color 0.2s;"
        onmouseover="this.style.borderColor='#2563eb'"
        onmouseout="this.style.borderColor='#1e293b'">
        <img src="{car['image_url']}" alt="{car['make']} {car['model']}"
             style="width:100%; height:180px; object-fit:cover;">
        <div style="padding:16px;">
            <div style="display:flex; align-items:center;
                        justify-content:space-between; margin-bottom:6px;">
                <div style="font-size:16px; font-weight:700;
                            color:#F0F4F8;">
                    {car['year']} {car['make']} {car['model']}{badge}
                </div>
            </div>
            <div style="font-size:22px; font-weight:800;
                        color:#3B82F6; margin-bottom:10px;">
                KES {car['price']:,}
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:6px;
                        margin-bottom:10px;">
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px;
                    border-radius:20px; border:1px solid #1e293b;">
                    {car['transmission']}
                </span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px;
                    border-radius:20px; border:1px solid #1e293b;">
                    {car['fuel_type']}
                </span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px;
                    border-radius:20px; border:1px solid #1e293b;">
                    {car['mileage']:,} km
                </span>
                <span style="background:#0f1e30; color:#94A3B8;
                    font-size:11px; padding:3px 8px;
                    border-radius:20px; border:1px solid #1e293b;">
                    {car['engine_size']}
                </span>
            </div>
            <div style="display:flex; align-items:center;
                        justify-content:space-between;">
                <span style="color:{condition_colour}; font-size:12px;
                             font-weight:600;">
                    ● {car['condition']}
                </span>
                <span style="color:#64748B; font-size:12px;">
                    📍 {car['location']}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "View Details",
        key=f"view_{car['id']}",
        use_container_width=True
    ):
        st.session_state.selected_car_id = car['id']
        st.rerun()


def _car_detail(car):
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
            {car['body_type']} · {car['seller_type']} · {car['location']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_img, col_info = st.columns([3, 2])

    with col_img:
        st.image(car['image_url'], use_column_width=True)

        # Estimated value
        estimated = estimate_value(car)
        diff      = estimated - car['price']
        diff_txt  = f"KES {abs(diff):,} {'below' if diff < 0 else 'above'} market"
        diff_col  = "#22c55e" if diff >= 0 else "#ef4444"

        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px solid #1e293b; border-radius:12px; padding:16px;
            margin-top:12px;">
            <div style="color:#94A3B8; font-size:12px; margin-bottom:8px;
                        text-transform:uppercase; letter-spacing:0.05em;">
                AI Valuation
            </div>
            <div style="font-size:24px; font-weight:800; color:#3B82F6;">
                KES {estimated:,}
            </div>
            <div style="color:{diff_col}; font-size:13px; margin-top:4px;">
                Listed price is {diff_txt}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#111827,#0b1220);
            border:1px solid #1e293b; border-radius:12px; padding:20px;">
            <div style="font-size:32px; font-weight:800; color:#3B82F6;
                        margin-bottom:16px;">KES {car['price']:,}</div>
        """, unsafe_allow_html=True)

        specs = [
            ("Year",         car['year']),
            ("Mileage",      f"{car['mileage']:,} km"),
            ("Fuel",         car['fuel_type']),
            ("Transmission", car['transmission']),
            ("Engine",       car['engine_size']),
            ("Body",         car['body_type']),
            ("Color",        car['color']),
            ("Condition",    car['condition']),
            ("Seller",       car['seller_type']),
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

        # Contact seller button
        if st.button(
            "Contact Seller",
            use_container_width=True,
            key="contact_seller"
        ):
            st.session_state.draft_message = (
                f"Hi, I'm interested in the {car['year']} "
                f"{car['make']} {car['model']} listed at "
                f"KES {car['price']:,}. Is it still available?"
            )
            st.success(
                "Message drafted! Go to Contact page to send it."
            )

    # Description
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#111827,#0b1220);
        border:1px solid #1e293b; border-radius:12px; padding:20px;
        margin-top:16px;">
        <div style="color:#60A5FA; font-size:14px; font-weight:700;
                    margin-bottom:10px; text-transform:uppercase;
                    letter-spacing:0.05em;">Description</div>
        <div style="color:#E2E8F0; font-size:14px; line-height:1.7;">
            {car['description']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_car_marketplace():
    """Main car marketplace page."""
    st.markdown(
        '<div class="section-heading">Car Marketplace</div>',
        unsafe_allow_html=True
    )

    # Initialise selected car state
    if "selected_car_id" not in st.session_state:
        st.session_state.selected_car_id = None

    # ── Detail view ──
    if st.session_state.selected_car_id:
        car = get_car_by_id(st.session_state.selected_car_id)
        if car:
            _car_detail(car)
        else:
            st.error("Car not found.")
            st.session_state.selected_car_id = None
        return

    # ── Featured section ──
    featured = get_featured_cars(limit=3)
    if featured:
        st.markdown("""
        <div style="color:#F0F4F8; font-size:18px; font-weight:700;
                    margin-bottom:12px;">Featured Listings</div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for i, car in enumerate(featured):
            with cols[i]:
                _car_card(car)
        st.markdown(
            '<hr style="border-color:#1e293b; margin:20px 0;">',
            unsafe_allow_html=True
        )

    # ── Filters ──
    with st.expander("Filter & Search", expanded=False):
        fc1, fc2, fc3 = st.columns(3)

        with fc1:
            search_term = st.text_input(
                "Search by make/model", placeholder="e.g. Toyota Harrier"
            )
            makes = ["All"] + get_unique_makes()
            selected_make = st.selectbox("Make", makes)

        with fc2:
            min_price, max_price = get_price_range()
            price_range = st.slider(
                "Price Range (KES)",
                min_value=min_price,
                max_value=max_price,
                value=(min_price, max_price),
                step=50_000,
                format="KES %d"
            )

        with fc3:
            min_year, max_year = get_year_range()
            year_range = st.slider(
                "Year",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year)
            )

        fc4, fc5, fc6 = st.columns(3)
        with fc4:
            fuel_type = st.selectbox(
                "Fuel Type",
                ["All", "Petrol", "Diesel", "Hybrid", "Electric"]
            )
        with fc5:
            transmission = st.selectbox(
                "Transmission",
                ["All", "Automatic", "Manual", "CVT"]
            )
        with fc6:
            body_type = st.selectbox(
                "Body Type",
                ["All", "Sedan", "SUV", "Hatchback", "Pickup",
                 "Wagon", "MPV", "Coupe"]
            )

    # Build filters dict
    filters = {}
    if search_term:
        filters["search_term"] = search_term
    if selected_make != "All":
        filters["make"] = selected_make
    filters["min_price"] = price_range[0]
    filters["max_price"] = price_range[1]
    filters["min_year"]  = year_range[0]
    filters["max_year"]  = year_range[1]
    if fuel_type != "All":
        filters["fuel_type"] = fuel_type
    if transmission != "All":
        filters["transmission"] = transmission
    if body_type != "All":
        filters["body_type"] = body_type

    cars = get_filtered_cars(filters)

    # Results count
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
            padding:48px; text-align:center;">
            <div style="font-size:40px; margin-bottom:12px;">🔍</div>
            <div style="color:#F0F4F8; font-size:18px; font-weight:600;
                        margin-bottom:8px;">No cars found</div>
            <div style="color:#94A3B8; font-size:14px;">
                Try adjusting your filters.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Grid ──
    cols = st.columns(3)
    for i, car in enumerate(cars):
        with cols[i % 3]:
            _car_card(car)
