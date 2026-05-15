def _comparison_page(comparison_cars):
    """Render the comparison view for selected cars."""
    if not comparison_cars:
        return
    
    st.markdown("### 🔍 Car Comparison")
    st.markdown(f"Comparing {len(comparison_cars)} vehicles")
    
    # Create comparison data as strings to avoid Arrow errors
    compare_data = []
    attributes = ["Make", "Model", "Year", "Price (KSh)", "Mileage (km)", 
                  "Fuel Type", "Transmission", "Body Type", "Color", "Condition", "Location"]
    
    for car in comparison_cars:
        row = {
            "Make": car["make"],
            "Model": car["model"],
            "Year": str(car["year"]),
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
    
    # Transpose and convert to DataFrame with string columns
    import pandas as pd
    compare_df = pd.DataFrame(compare_data).T
    compare_df.columns = [f"{c['make']} {c['model']} ({c['year']})" for c in comparison_cars]
    # Ensure all data is string
    compare_df = compare_df.astype(str)
    st.dataframe(compare_df, use_container_width=True)
    
    if st.button("Clear Comparison", use_container_width=True):
        st.session_state.car_comparison = []
        st.rerun()
