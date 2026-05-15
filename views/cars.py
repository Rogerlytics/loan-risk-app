# views/cars.py
"""
Car Marketplace - A complete car listing and discovery platform.
"""
import streamlit as st
import pandas as pd
from services.cars_service import (
    get_all_cars,
    get_car_by_id,
    get_featured_cars,
    get_filtered_cars,
    get_unique_makes,
    get_price_range,
    get_year_range,
    estimate_value
)
from utils.helpers import sanitise_text
import time


def _car_card(car, is_compare=False, show_actions=True):
    """
    Render a single car card with consistent styling.
    Returns HTML for the card.
    """
    price_ksh = f"KSh {car['price']:,}"
    mileage_km = f"{car['mileage']:,} km"
    
    # Condition badge colour
    condition_colors = {
        "Excellent": "#22c55e",
        "Very Good": "#38bdf8",
        "Good": "#f59e0b",
        "Fair": "#ef4444"
    }
    condition_color = condition_colors.get(car["condition"], "#64748B")
    
    card_html = f"""
    <div class="car-card" data-car-id="{car['id']}">
        <div class="car-card-image">
            <img src="{car['image_url']}" alt="{car['make']} {car['model']}">
            { '<div class="featured-badge">⭐ Featured</div>' if car.get('featured') else '' }
        </div>
        <div class="car-card-content">
            <div class="car-card-title">
                <span class="car-make-model">{car['make']} {car['model']}</span>
                <span class="car-year">{car['year']}</span>
            </div>
            <div class="car-card-price">{price_ksh}</div>
            <div class="car-card-specs">
                <div class="spec-item">
                    <span class="spec-icon">📏</span> {mileage_km}
                </div>
                <div class="spec-item">
                    <span class="spec-icon">⛽</span> {car['fuel_type']}
                </div>
                <div class="spec-item">
                    <span class="spec-icon">⚙️</span> {car['transmission']}
                </div>
                <div class="spec-item">
                    <span class="spec-icon">🎨</span> {car['color']}
                </div>
            </div>
            <div class="car-card-location">
                📍 {car['location']}
            </div>
            <div class="car-card-condition">
                <span style="background:{condition_color}20; color:{condition_color}; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600;">
                    {car['condition']}
                </span>
            </div>
        </div>
    </div>
    """
    
    if is_compare:
        return card_html
    
    # Add action buttons below the card (outside HTML, handled by Streamlit)
    return card_html


def _comparison_page(comparison_cars):
    """Render the comparison view for selected cars."""
    if not comparison_cars:
        return
    
    st.markdown("### 🔍 Car Comparison")
    st.markdown(f"Comparing {len(comparison_cars)} vehicles")
    
    # Create comparison table
    compare_data = []
    attributes = ["Make", "Model", "Year", "Price (KSh)", "Mileage (km)", 
                  "Fuel Type", "Transmission", "Body Type", "Color", "Condition", "Location"]
    
    for car in comparison_cars:
        row = {
            "Make": car["make"],
            "Model": car["model"],
            "Year": car["year"],
            "Price (KSh)": f"{car['price']:,}",
            "Mileage (km)": f"{car['mileage']:,}",
            "Fuel Type": car["fuel_type"],
            "Transmission": car["transmission"],
            "Body Type": car["body_type"],
            "Color": car["color"],
            "Condition": car["condition"],
            "Location": car["location"],
        }
        compare_data.append(row)
    
    compare_df = pd.DataFrame(compare_data).T
    compare_df.columns = [f"{c['make']} {c['model']} ({c['year']})" for c in comparison_cars]
    
    st.dataframe(compare_df, use_container_width=True)
    
    # Clear comparison button
    if st.button("Clear Comparison", use_container_width=True):
        st.session_state.car_comparison = []
        st.rerun()


def _recently_viewed_car(car):
    """Display a small card for recently viewed cars."""
    price = f"KSh {car['price']:,}"
    with st.container():
        st.markdown(f"""
        <div style="background:#0f1e30; border-radius:12px; padding:10px; margin-bottom:8px; border:1px solid #1e293b;">
            <div style="display:flex; gap:10px; align-items:center;">
                <img src="{car['image_url']}" style="width:60px; height:45px; border-radius:8px; object-fit:cover;">
                <div style="flex:1;">
                    <div style="color:#F0F4F8; font-size:13px; font-weight:600;">{car['make']} {car['model']}</div>
                    <div style="color:#60A5FA; font-size:12px;">{price}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _valuation_tool():
    """Interactive car valuation calculator."""
    st.markdown("### 💰 Car Valuation Tool")
    st.markdown("Get an instant estimate of your car's current market value")
    
    col1, col2 = st.columns(2)
    
    with col1:
        make = st.selectbox("Make", ["Toyota", "Honda", "Nissan", "Mazda", "Subaru", "Volkswagen", "Mercedes", "BMW", "Isuzu", "Mitsubishi"])
        model = st.text_input("Model", placeholder="e.g., Fielder, Vezel, Outlander")
        year = st.number_input("Year", min_value=2000, max_value=2025, value=2018)
        
    with col2:
        mileage = st.number_input("Mileage (km)", min_value=0, max_value=500000, value=80000, step=5000)
        condition = st.selectbox("Condition", ["Excellent", "Very Good", "Good", "Fair"])
        body_type = st.selectbox("Body Type", ["Sedan", "SUV", "Hatchback", "Pickup", "Wagon"])
    
    if st.button("Calculate Estimated Value", use_container_width=True):
        # Create a temporary car object for valuation
        temp_car = {
            "make": make,
            "model": model,
            "year": year,
            "mileage": mileage,
            "condition": condition,
            "body_type": body_type,
            "price": 2000000,  # Base placeholder
        }
        estimated = estimate_value(temp_car)
        
        st.success(f"### Estimated Market Value: **KSh {estimated:,}**")
        st.info("This is an estimate based on current market trends. Actual price may vary depending on specific features, service history, and demand.")


def _search_filters():
    """Render the search and filter sidebar section."""
    st.sidebar.markdown("### 🔍 Search & Filter")
    
    # Search term
    search_term = st.sidebar.text_input("Search by make/model", placeholder="e.g., Toyota Fielder")
    
    # Price range
    min_price, max_price = get_price_range()
    price_range = st.sidebar.slider(
        "Price Range (KSh)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=50000,
        format="KSh %d"
    )
    
    # Year range
    min_year, max_year = get_year_range()
    year_range = st.sidebar.slider(
        "Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )
    
    # Make filter
    makes = ["All"] + get_unique_makes()
    selected_make = st.sidebar.selectbox("Make", makes)
    
    # Mileage filter
    mileage_range = st.sidebar.slider(
        "Mileage (km)",
        min_value=0,
        max_value=300000,
        value=(0, 300000),
        step=10000,
        format="%d km"
    )
    
    # Fuel type
    fuel_types = ["All", "Petrol", "Diesel", "Hybrid", "Electric"]
    selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)
    
    # Transmission
    transmissions = ["All", "Automatic", "Manual", "CVT"]
    selected_trans = st.sidebar.selectbox("Transmission", transmissions)
    
    # Body type
    body_types = ["All", "Sedan", "SUV", "Hatchback", "Pickup", "Wagon", "MPV", "Coupe", "Convertible"]
    selected_body = st.sidebar.selectbox("Body Type", body_types)
    
    # Build filters dict
    filters = {}
    if search_term:
        filters["search_term"] = search_term
    if selected_make != "All":
        filters["make"] = selected_make
    filters["min_price"] = price_range[0]
    filters["max_price"] = price_range[1]
    filters["min_year"] = year_range[0]
    filters["max_year"] = year_range[1]
    filters["min_mileage"] = mileage_range[0]
    filters["max_mileage"] = mileage_range[1]
    if selected_fuel != "All":
        filters["fuel_type"] = selected_fuel
    if selected_trans != "All":
        filters["transmission"] = selected_trans
    if selected_body != "All":
        filters["body_type"] = selected_body
    
    return filters


def _display_car_grid(cars, cars_per_row=3):
    """
    Display cars in a responsive grid with action buttons.
    """
    if not cars:
        st.info("No cars found matching your criteria. Try adjusting your filters.")
        return
    
    # Create rows of columns
    rows = [cars[i:i + cars_per_row] for i in range(0, len(cars), cars_per_row)]
    
    for row_cars in rows:
        cols = st.columns(cars_per_row)
        for idx, car in enumerate(row_cars):
            with cols[idx]:
                # Render the card using custom HTML
                card_html = _car_card(car)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Action buttons row
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🔍 View", key=f"view_{car['id']}", use_container_width=True):
                        st.session_state.selected_car = car["id"]
                        st.session_state.show_detail = True
                        # Add to recently viewed
                        if "recently_viewed" not in st.session_state:
                            st.session_state.recently_viewed = []
                        # Remove if already exists, then add to front
                        st.session_state.recently_viewed = [c for c in st.session_state.recently_viewed if c["id"] != car["id"]]
                        st.session_state.recently_viewed.insert(0, car)
                        st.session_state.recently_viewed = st.session_state.recently_viewed[:5]
                        st.rerun()
                
                with col_b:
                    is_in_comparison = any(c["id"] == car["id"] for c in st.session_state.get("car_comparison", []))
                    btn_label = "❌ Remove" if is_in_comparison else "📊 Compare"
                    if st.button(btn_label, key=f"compare_{car['id']}", use_container_width=True):
                        if "car_comparison" not in st.session_state:
                            st.session_state.car_comparison = []
                        if is_in_comparison:
                            st.session_state.car_comparison = [c for c in st.session_state.car_comparison if c["id"] != car["id"]]
                        else:
                            if len(st.session_state.car_comparison) >= 3:
                                st.warning("You can compare up to 3 cars at a time.")
                            else:
                                st.session_state.car_comparison.append(car)
                        st.rerun()


def _car_detail_view(car):
    """Show detailed view for a single car."""
    price = f"KSh {car['price']:,}"
    mileage = f"{car['mileage']:,} km"
    
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#111827,#0b1220); border-radius:16px; padding:24px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
            <div>
                <div style="font-size:28px; font-weight:700; color:#F0F4F8;">{car['make']} {car['model']}</div>
                <div style="color:#94A3B8; font-size:14px;">{car['year']} · {car['condition']}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:28px; font-weight:700; color:#60A5FA;">{price}</div>
                <div style="color:#64748B; font-size:12px;">{car['location']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_img, col_specs = st.columns([1, 1])
    
    with col_img:
        st.image(car['image_url'], use_container_width=True)
    
    with col_specs:
        st.markdown("### 📋 Specifications")
        specs_df = pd.DataFrame([
            {"Attribute": "Make", "Value": car["make"]},
            {"Attribute": "Model", "Value": car["model"]},
            {"Attribute": "Year", "Value": car["year"]},
            {"Attribute": "Mileage", "Value": mileage},
            {"Attribute": "Fuel Type", "Value": car["fuel_type"]},
            {"Attribute": "Transmission", "Value": car["transmission"]},
            {"Attribute": "Body Type", "Value": car["body_type"]},
            {"Attribute": "Color", "Value": car["color"]},
            {"Attribute": "Engine Size", "Value": car["engine_size"]},
            {"Attribute": "Seller", "Value": car["seller_type"]},
        ])
        st.dataframe(specs_df, use_container_width=True, hide_index=True)
    
    st.markdown("### 📝 Description")
    st.write(car["description"])
    
    # Valuation estimate
    estimated = estimate_value(car)
    st.info(f"💡 **Estimated current market value:** KSh {estimated:,} (based on year, mileage, and condition)")
    
    col_back, col_compare = st.columns(2)
    with col_back:
        if st.button("← Back to Listings", use_container_width=True):
            st.session_state.show_detail = False
            st.session_state.selected_car = None
            st.rerun()
    with col_compare:
        is_in_comparison = any(c["id"] == car["id"] for c in st.session_state.get("car_comparison", []))
        if st.button("Remove from Comparison" if is_in_comparison else "Add to Comparison", use_container_width=True):
            if "car_comparison" not in st.session_state:
                st.session_state.car_comparison = []
            if is_in_comparison:
                st.session_state.car_comparison = [c for c in st.session_state.car_comparison if c["id"] != car["id"]]
            else:
                if len(st.session_state.car_comparison) >= 3:
                    st.warning("You can compare up to 3 cars at a time.")
                else:
                    st.session_state.car_comparison.append(car)
            st.rerun()


def show_cars(supabase):
    """Main entry point for the Car Marketplace page."""
    
    # Page header
    st.markdown(
        '<div class="section-heading">🚗 Car Marketplace</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="color:#94A3B8; font-size:14px; margin-bottom:24px;">'
        'Find your perfect car from verified sellers across Kenya</div>',
        unsafe_allow_html=True
    )
    
    # Initialise session state
    if "selected_car" not in st.session_state:
        st.session_state.selected_car = None
    if "show_detail" not in st.session_state:
        st.session_state.show_detail = False
    if "car_comparison" not in st.session_state:
        st.session_state.car_comparison = []
    if "recently_viewed" not in st.session_state:
        st.session_state.recently_viewed = []
    
    # Search filters (sidebar)
    filters = _search_filters()
    
    # Main content area
    if st.session_state.show_detail and st.session_state.selected_car:
        car = get_car_by_id(st.session_state.selected_car)
        if car:
            _car_detail_view(car)
        else:
            st.session_state.show_detail = False
            st.rerun()
    else:
        # Show comparison banner if any cars selected
        if st.session_state.car_comparison:
            with st.container():
                st.markdown("---")
                _comparison_page(st.session_state.car_comparison)
                st.markdown("---")
        
        # Get filtered cars
        filtered_cars = get_filtered_cars(filters)
        
        # Sorting options
        sort_option = st.selectbox(
            "Sort by",
            ["Featured", "Price (Low to High)", "Price (High to Low)", "Year (Newest First)", "Mileage (Low to High)"],
            index=0
        )
        
        # Apply sorting
        if sort_option == "Price (Low to High)":
            filtered_cars = sorted(filtered_cars, key=lambda x: x["price"])
        elif sort_option == "Price (High to Low)":
            filtered_cars = sorted(filtered_cars, key=lambda x: x["price"], reverse=True)
        elif sort_option == "Year (Newest First)":
            filtered_cars = sorted(filtered_cars, key=lambda x: x["year"], reverse=True)
        elif sort_option == "Mileage (Low to High)":
            filtered_cars = sorted(filtered_cars, key=lambda x: x["mileage"])
        else:  # Featured
            filtered_cars = sorted(filtered_cars, key=lambda x: (x.get("featured", False), x["price"]), reverse=True)
        
        # Display results count
        st.markdown(f"### 🎯 {len(filtered_cars)} cars found")
        
        # Display car grid
        _display_car_grid(filtered_cars, cars_per_row=3)
        
        # Recently viewed section (sidebar)
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👁️ Recently Viewed")
            if st.session_state.recently_viewed:
                for car in st.session_state.recently_viewed:
                    _recently_viewed_car(car)
            else:
                st.caption("Click 'View' on any car to see it here")
            
            st.markdown("---")
            _valuation_tool()
    
    # Custom CSS for car cards
    st.markdown("""
    <style>
    .car-card {
        background: #0f1e30;
        border: 1px solid #1e293b;
        border-radius: 16px;
        overflow: hidden;
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 12px;
    }
    .car-card:hover {
        transform: translateY(-2px);
        border-color: #2563eb;
    }
    .car-card-image {
        position: relative;
        height: 160px;
        overflow: hidden;
        background: #0B1220;
    }
    .car-card-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .featured-badge {
        position: absolute;
        top: 8px;
        left: 8px;
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
    }
    .car-card-content {
        padding: 14px;
    }
    .car-card-title {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 8px;
    }
    .car-make-model {
        font-weight: 700;
        font-size: 16px;
        color: #F0F4F8;
    }
    .car-year {
        color: #64748B;
        font-size: 13px;
    }
    .car-card-price {
        font-size: 20px;
        font-weight: 700;
        color: #60A5FA;
        margin-bottom: 12px;
    }
    .car-card-specs {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 12px;
    }
    .spec-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #94A3B8;
    }
    .spec-icon {
        font-size: 12px;
    }
    .car-card-location {
        font-size: 12px;
        color: #64748B;
        margin-bottom: 8px;
    }
    .car-card-condition {
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
