# ==============================
# views/car_upload.py
# Admin — Add / Edit / Delete Cars
# ==============================
import streamlit as st
from config.settings import require_role
from services.cars_service import (
    get_all_cars,
    insert_car,
    update_car,
    delete_car,
    upload_car_image
)

MAKES = [
    "Audi", "BMW", "Ford", "Honda", "Hyundai", "Isuzu",
    "Kia", "Mazda", "Mercedes", "Mitsubishi", "Nissan",
    "Subaru", "Suzuki", "Toyota", "Volkswagen", "Other"
]
FUEL_TYPES    = ["Petrol", "Diesel", "Hybrid", "Electric"]
TRANSMISSIONS = ["Automatic", "Manual", "CVT"]
BODY_TYPES    = ["Sedan", "SUV", "Hatchback", "Pickup",
                 "Wagon", "MPV", "Coupe", "Convertible"]
CONDITIONS    = ["Excellent", "Very Good", "Good", "Fair"]
LOCATIONS     = ["Nairobi", "Mombasa", "Kisumu", "Nakuru",
                 "Eldoret", "Thika", "Malindi", "Naivasha", "Other"]
SELLER_TYPES  = ["Private Seller", "Dealership", "Certified Pre-owned"]
ENGINE_SIZES  = ["1.0L", "1.3L", "1.5L", "1.8L", "2.0L",
                 "2.5L", "3.0L", "3.5L", "4.0L"]


def _car_form(supabase, existing_car=None):
    is_edit = existing_car is not None
    prefix  = f"edit_{existing_car['id']}" if is_edit else "add"

    st.markdown(
        f'<div class="section-heading">'
        f'{"Edit Car Listing" if is_edit else "Add New Car Listing"}'
        f'</div>',
        unsafe_allow_html=True
    )

    if is_edit and existing_car.get("image_url"):
        st.image(existing_car["image_url"], width=280)
        st.caption("Upload a new image below to replace the current one.")

    uploaded_file = st.file_uploader(
        "Car Photo (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"{prefix}_image"
    )

    st.markdown(
        '<hr style="border-color:#1e293b;margin:12px 0;">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        make = st.selectbox(
            "Make *", MAKES,
            index=MAKES.index(existing_car["make"])
                  if is_edit and existing_car.get("make") in MAKES else 0,
            key=f"{prefix}_make"
        )
        model = st.text_input(
            "Model *",
            value=existing_car.get("model", "") if is_edit else "",
            placeholder="e.g. Harrier",
            key=f"{prefix}_model"
        )
        year = st.number_input(
            "Year *", min_value=1990, max_value=2026,
            value=existing_car.get("year", 2020) if is_edit else 2020,
            key=f"{prefix}_year"
        )
        price = st.number_input(
            "Price (KES) *", min_value=0, max_value=50_000_000,
            value=existing_car.get("price", 0) if is_edit else 0,
            step=10_000, key=f"{prefix}_price"
        )
        color = st.text_input(
            "Color",
            value=existing_car.get("color", "") if is_edit else "",
            placeholder="e.g. Pearl White",
            key=f"{prefix}_color"
        )

    with col2:
        mileage = st.number_input(
            "Mileage (km)", min_value=0, max_value=1_000_000,
            value=existing_car.get("mileage", 0) if is_edit else 0,
            step=1_000, key=f"{prefix}_mileage"
        )
        fuel_type = st.selectbox(
            "Fuel Type", FUEL_TYPES,
            index=FUEL_TYPES.index(existing_car["fuel_type"])
                  if is_edit and existing_car.get("fuel_type")
                  in FUEL_TYPES else 0,
            key=f"{prefix}_fuel"
        )
        transmission = st.selectbox(
            "Transmission", TRANSMISSIONS,
            index=TRANSMISSIONS.index(existing_car["transmission"])
                  if is_edit and existing_car.get("transmission")
                  in TRANSMISSIONS else 0,
            key=f"{prefix}_trans"
        )
        engine_size = st.selectbox(
            "Engine Size", ENGINE_SIZES,
            index=ENGINE_SIZES.index(existing_car["engine_size"])
                  if is_edit and existing_car.get("engine_size")
                  in ENGINE_SIZES else 2,
            key=f"{prefix}_engine"
        )
        body_type = st.selectbox(
            "Body Type", BODY_TYPES,
            index=BODY_TYPES.index(existing_car["body_type"])
                  if is_edit and existing_car.get("body_type")
                  in BODY_TYPES else 1,
            key=f"{prefix}_body"
        )

    with col3:
        condition = st.selectbox(
            "Condition", CONDITIONS,
            index=CONDITIONS.index(existing_car["condition"])
                  if is_edit and existing_car.get("condition")
                  in CONDITIONS else 2,
            key=f"{prefix}_condition"
        )
        location = st.selectbox(
            "Location", LOCATIONS,
            index=LOCATIONS.index(existing_car["location"])
                  if is_edit and existing_car.get("location")
                  in LOCATIONS else 0,
            key=f"{prefix}_location"
        )
        seller_type = st.selectbox(
            "Seller Type", SELLER_TYPES,
            index=SELLER_TYPES.index(existing_car["seller_type"])
                  if is_edit and existing_car.get("seller_type")
                  in SELLER_TYPES else 1,
            key=f"{prefix}_seller"
        )
        featured = st.checkbox(
            "Mark as Featured",
            value=existing_car.get("featured", False) if is_edit else False,
            key=f"{prefix}_featured"
        )

    description = st.text_area(
        "Description",
        value=existing_car.get("description", "") if is_edit else "",
        placeholder="Describe the car — condition, features, service history...",
        height=120,
        key=f"{prefix}_desc"
    )

    # ── Add button with success state ──
    if is_edit:
        if st.button(
            "Update Car Listing",
            use_container_width=True,
            key=f"{prefix}_submit"
        ):
            if not model.strip():
                st.error("Please enter the car model.")
                return
            if price <= 0:
                st.error("Please enter a valid price.")
                return

            image_url = existing_car.get("image_url", "")
            if uploaded_file:
                with st.spinner("Uploading image..."):
                    image_url = upload_car_image(
                        supabase, uploaded_file.read(), uploaded_file.name
                    )
                if not image_url:
                    st.error("Image upload failed.")
                    return

            car_data = {
                "make": make, "model": model.strip(),
                "year": int(year), "price": int(price),
                "mileage": int(mileage), "fuel_type": fuel_type,
                "transmission": transmission, "body_type": body_type,
                "color": color.strip(), "engine_size": engine_size,
                "condition": condition, "location": location,
                "seller_type": seller_type, "description": description.strip(),
                "image_url": image_url, "featured": featured,
            }
            with st.spinner("Updating..."):
                success = update_car(supabase, existing_car["id"], car_data)
            if success:
                st.success(f"{year} {make} {model} updated successfully!")
                st.session_state.editing_car_id = None
                st.rerun()

    else:
        # ── Add New Car — success state hides the button ──
        success_key = "car_add_success"
        if success_key not in st.session_state:
            st.session_state[success_key] = False
        added_car_key = "car_add_last"
        if added_car_key not in st.session_state:
            st.session_state[added_car_key] = {}

        if st.session_state[success_key]:
            last = st.session_state[added_car_key]
            st.markdown(f"""
            <div style="
                background:linear-gradient(135deg,#052e16 0%,#0a3d1f 100%);
                border:2px solid #16a34a;
                border-radius:20px;
                padding:32px 28px;
                text-align:center;
                margin-top:8px;">
                <div style="font-size:52px;margin-bottom:12px;">🎉</div>
                <div style="color:#4ade80;font-size:22px;font-weight:800;
                            margin-bottom:8px;">
                    Car Successfully Listed!
                </div>
                <div style="color:#86efac;font-size:15px;margin-bottom:16px;">
                    <b style="color:#F0F4F8;">
                        {last.get('year','')} {last.get('make','')}
                        {last.get('model','')}
                    </b> has been added to the marketplace.
                </div>
                <div style="display:flex;justify-content:center;
                            flex-wrap:wrap;gap:10px;margin-bottom:20px;">
                    <span style="background:rgba(34,197,94,0.15);
                        color:#86efac;font-size:12px;padding:4px 12px;
                        border-radius:20px;border:1px solid #16a34a;">
                        ✓ Listing Published
                    </span>
                    <span style="background:rgba(34,197,94,0.15);
                        color:#86efac;font-size:12px;padding:4px 12px;
                        border-radius:20px;border:1px solid #16a34a;">
                        ✓ Visible in Marketplace
                    </span>
                    <span style="background:rgba(34,197,94,0.15);
                        color:#86efac;font-size:12px;padding:4px 12px;
                        border-radius:20px;border:1px solid #16a34a;">
                        ✓ Financing Info Attached
                    </span>
                </div>
                <div style="color:#64748B;font-size:13px;">
                    Listed at
                    <b style="color:#3B82F6;">
                        KES {last.get('price', 0):,}
                    </b>
                    · {last.get('location','')}
                    · {last.get('condition','')} Condition
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(
                    "Add Another Car",
                    use_container_width=True,
                    key="add_another_car"
                ):
                    st.session_state[success_key] = False
                    st.session_state[added_car_key] = {}
                    st.rerun()
            with col_b:
                if st.button(
                    "View Marketplace",
                    use_container_width=True,
                    key="go_to_marketplace"
                ):
                    st.session_state[success_key] = False
                    st.session_state[added_car_key] = {}
                    st.session_state["page_override"] = "Car Marketplace"
                    st.rerun()

        else:
            if st.button(
                "Add Car Listing",
                use_container_width=True,
                key=f"{prefix}_submit"
            ):
                if not model.strip():
                    st.error("Please enter the car model.")
                    return
                if price <= 0:
                    st.error("Please enter a valid price.")
                    return
                if not uploaded_file:
                    st.warning(
                        "No image uploaded — listing will show a placeholder."
                    )

                image_url = ""
                if uploaded_file:
                    with st.spinner("Uploading image..."):
                        image_url = upload_car_image(
                            supabase,
                            uploaded_file.read(),
                            uploaded_file.name
                        )
                    if not image_url:
                        st.error("Image upload failed. Please try again.")
                        return

                car_data = {
                    "make": make, "model": model.strip(),
                    "year": int(year), "price": int(price),
                    "mileage": int(mileage), "fuel_type": fuel_type,
                    "transmission": transmission, "body_type": body_type,
                    "color": color.strip(), "engine_size": engine_size,
                    "condition": condition, "location": location,
                    "seller_type": seller_type,
                    "description": description.strip(),
                    "image_url": image_url, "featured": featured,
                }

                with st.spinner("Publishing listing..."):
                    success = insert_car(supabase, car_data)

                if success:
                    st.session_state[success_key]  = True
                    st.session_state[added_car_key] = car_data
                    st.rerun()


def show_car_management(supabase):
    require_role(["admin"])

    st.markdown(
        '<div class="section-heading">Car Management</div>',
        unsafe_allow_html=True
    )

    if "editing_car_id" not in st.session_state:
        st.session_state.editing_car_id = None
    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None

    tab_add, tab_manage = st.tabs(["Add New Car", "Manage Listings"])

    with tab_add:
        _car_form(supabase)

    with tab_manage:
        with st.spinner("Loading listings..."):
            cars = get_all_cars(supabase)

        if not cars:
            st.markdown("""
            <div style="background:linear-gradient(145deg,#111827,#0b1220);
                border:1px dashed #1e293b;border-radius:16px;
                padding:48px;text-align:center;">
                <div style="font-size:40px;margin-bottom:12px;">🚗</div>
                <div style="color:#F0F4F8;font-size:18px;font-weight:600;
                            margin-bottom:8px;">No cars listed yet</div>
                <div style="color:#94A3B8;font-size:14px;">
                    Add your first car using the "Add New Car" tab.</div>
            </div>
            """, unsafe_allow_html=True)
            return

        st.markdown(
            f'<div style="color:#94A3B8;font-size:13px;margin-bottom:16px;">'
            f'<b style="color:#F0F4F8;">{len(cars)}</b> listing'
            f'{"s" if len(cars) != 1 else ""} total</div>',
            unsafe_allow_html=True
        )

        if st.session_state.editing_car_id:
            edit_car = next(
                (c for c in cars
                 if c["id"] == st.session_state.editing_car_id),
                None
            )
            if edit_car:
                st.markdown("""
                <div style="background:linear-gradient(145deg,#111827,#0b1220);
                    border:1px solid #2563eb;border-radius:16px;
                    padding:24px;margin-bottom:20px;">
                """, unsafe_allow_html=True)
                _car_form(supabase, existing_car=edit_car)
                if st.button(
                    "Cancel Edit", key="cancel_edit",
                    use_container_width=True
                ):
                    st.session_state.editing_car_id = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        for car in cars:
            col_img, col_info, col_actions = st.columns([1, 3, 1])

            with col_img:
                if car.get("image_url"):
                    st.image(car["image_url"], use_container_width=True)
                else:
                    st.markdown("""
                    <div style="background:#0f1e30;border:1px solid #1e293b;
                        border-radius:8px;height:80px;display:flex;
                        align-items:center;justify-content:center;
                        color:#64748B;font-size:24px;">🚗</div>
                    """, unsafe_allow_html=True)

            with col_info:
                featured_badge = (
                    ' <span style="background:#1d4ed8;color:#bfdbfe;'
                    'font-size:10px;font-weight:700;padding:2px 8px;'
                    'border-radius:20px;">FEATURED</span>'
                    if car.get("featured") else ""
                )
                st.markdown(
                    f'<div style="color:#F0F4F8;font-size:15px;'
                    f'font-weight:700;">'
                    f'{car["year"]} {car["make"]} {car["model"]}'
                    f'{featured_badge}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div style="color:#3B82F6;font-size:16px;'
                    f'font-weight:800;">KES {car["price"]:,}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div style="color:#94A3B8;font-size:12px;">'
                    f'{car["transmission"]} · {car["fuel_type"]} · '
                    f'{car["mileage"]:,} km · {car["location"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with col_actions:
                if st.button(
                    "Edit", key=f"edit_{car['id']}",
                    use_container_width=True
                ):
                    st.session_state.editing_car_id    = car['id']
                    st.session_state.confirm_delete_id = None
                    st.rerun()

                if st.session_state.confirm_delete_id == car['id']:
                    st.warning("Delete this car?")
                    cy, cn = st.columns(2)
                    with cy:
                        if st.button(
                            "Yes", key=f"confirm_del_{car['id']}",
                            use_container_width=True
                        ):
                            with st.spinner("Deleting..."):
                                delete_car(supabase, car['id'])
                            st.session_state.confirm_delete_id = None
                            st.success("Car deleted.")
                            st.rerun()
                    with cn:
                        if st.button(
                            "No", key=f"cancel_del_{car['id']}",
                            use_container_width=True
                        ):
                            st.session_state.confirm_delete_id = None
                            st.rerun()
                else:
                    if st.button(
                        "Delete", key=f"del_{car['id']}",
                        use_container_width=True
                    ):
                        st.session_state.confirm_delete_id = car['id']
                        st.session_state.editing_car_id    = None
                        st.rerun()

            st.markdown(
                '<hr style="border-color:#1e293b;margin:8px 0;">',
                unsafe_allow_html=True
            )
