# services/cars_service.py
"""
Car marketplace data service - mock implementation
Replace the mock data with your actual database calls when ready.
"""
import pandas as pd
from datetime import datetime
import random

# ============================================================
# 1. MOCK DATA GENERATION (realistic Kenya market data)
# ============================================================

def _generate_mock_cars():
    """Generate a rich set of mock car listings."""
    cars = []
    
    makes_models = {
        "Toyota": ["Fielder", "Axio", "Rav4", "Harrier", "Prado", "Hilux", "Vitz", "Premio", "Allion", "Corolla"],
        "Honda": ["Fit", "Vezel", "Accord", "CR-V", "Civic", "Grace", "Stepwgn"],
        "Nissan": ["Note", "X-Trail", "Dualis", "Wingroad", "Sunny", "Qashqai", "Navara"],
        "Mazda": ["Atenza", "Axela", "CX-5", "Demio", "BT-50", "Premacy"],
        "Subaru": ["Impreza", "Forester", "Outback", "Legacy", "XV", "Levorg"],
        "Volkswagen": ["Polo", "Golf", "Tiguan", "Passat", "Touareg", "Caddy"],
        "Mercedes": ["C-Class", "E-Class", "GLA", "GLE", "S-Class", "A-Class"],
        "BMW": ["X3", "X5", "3 Series", "5 Series", "1 Series", "X1"],
        "Isuzu": ["D-Max", "MU-X", "NPR", "FRR"],
        "Mitsubishi": ["Outlander", "Pajero", "L200", "ASX", "Lancer"],
        "Hyundai": ["i10", "i20", "Tucson", "Santa Fe", "Grand i10", "Elantra"],
        "Kia": ["Sportage", "Seltos", "Picanto", "Sorento", "Cerato"],
        "Ford": ["Ranger", "Everest", "Focus", "Fiesta", "EcoSport"],
        "Suzuki": ["Swift", "Jimny", "Vitara", "Celerio", "Ertiga"],
        "Audi": ["Q5", "A4", "A6", "Q7", "A3"],
    }
    
    body_types = ["Sedan", "SUV", "Hatchback", "Pickup", "Wagon", "MPV", "Coupe", "Convertible"]
    fuel_types = ["Petrol", "Diesel", "Hybrid", "Electric"]
    transmissions = ["Automatic", "Manual", "CVT"]
    conditions = ["Excellent", "Very Good", "Good", "Fair"]
    colors = ["White", "Black", "Silver", "Blue", "Red", "Grey", "Green", "Brown", "Gold", "Orange"]
    locations = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi", "Naivasha"]
    sellers = ["Private Seller", "Dealership", "Certified Pre-owned"]
    
    current_year = datetime.now().year
    
    for i in range(1, 51):  # 50 cars for rich demo
        make = random.choice(list(makes_models.keys()))
        model = random.choice(makes_models[make])
        
        year = random.randint(2015, current_year)
        price = random.choice([
            random.randint(400000, 800000),   # budget
            random.randint(800000, 1500000),  # mid-range
            random.randint(1500000, 3000000), # premium
            random.randint(3000000, 7000000)  # luxury
        ])
        
        mileage = random.randint(10000, 200000)
        if year >= 2022:
            mileage = random.randint(5000, 40000)
        elif year >= 2020:
            mileage = random.randint(20000, 80000)
        elif year >= 2017:
            mileage = random.randint(50000, 150000)
        else:
            mileage = random.randint(80000, 250000)
        
        car = {
            "id": i,
            "make": make,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "fuel_type": random.choice(fuel_types),
            "transmission": random.choice(transmissions),
            "body_type": random.choice(body_types),
            "color": random.choice(colors),
            "engine_size": random.choice(["1.3L", "1.5L", "1.8L", "2.0L", "2.5L", "3.0L"]),
            "condition": random.choice(conditions),
            "location": random.choice(locations),
            "seller_type": random.choice(sellers),
            "description": f"This {year} {make} {model} is in {random.choice(conditions)} condition with only {mileage:,} km. "
                          f"Features include {random.choice(['Air conditioning', 'Bluetooth', 'Reverse camera', 'Alloy wheels', 'Sunroof', 'Leather seats', 'Navigation', 'Keyless entry'])}, "
                          f"{random.choice(['ABS brakes', 'Airbags', 'ESP', 'Traction control'])} and much more.",
            "image_url": f"https://picsum.photos/id/{100 + i}/400/250",  # placeholder images
            "views": random.randint(10, 500),
            "featured": random.choice([True, False]),
            "created_at": datetime.now().isoformat(),
        }
        cars.append(car)
    
    # Mark some as featured
    for car in cars:
        car["featured"] = car["id"] in [3, 7, 12, 18, 24, 31, 39, 45]
    
    return cars

# Global cache for cars
_CARS_CACHE = None

def get_all_cars():
    """Return all car listings (cached)."""
    global _CARS_CACHE
    if _CARS_CACHE is None:
        _CARS_CACHE = _generate_mock_cars()
    return _CARS_CACHE

def get_car_by_id(car_id):
    """Return a single car by its ID."""
    cars = get_all_cars()
    for car in cars:
        if car["id"] == car_id:
            return car
    return None

def get_featured_cars(limit=6):
    """Return featured car listings."""
    cars = get_all_cars()
    featured = [c for c in cars if c.get("featured", False)]
    return featured[:limit]

def get_filtered_cars(filters):
    """
    Filter cars based on search criteria.
    Filters dict can contain: make, min_price, max_price, min_year, max_year,
    fuel_type, transmission, body_type, min_mileage, max_mileage, search_term
    """
    cars = get_all_cars()
    
    if not filters:
        return cars
    
    filtered = cars.copy()
    
    # Text search (make/model)
    if filters.get("search_term"):
        term = filters["search_term"].lower()
        filtered = [c for c in filtered 
                   if term in c["make"].lower() or term in c["model"].lower()]
    
    # Make filter
    if filters.get("make"):
        filtered = [c for c in filtered if c["make"] == filters["make"]]
    
    # Price range
    if filters.get("min_price"):
        filtered = [c for c in filtered if c["price"] >= filters["min_price"]]
    if filters.get("max_price"):
        filtered = [c for c in filtered if c["price"] <= filters["max_price"]]
    
    # Year range
    if filters.get("min_year"):
        filtered = [c for c in filtered if c["year"] >= filters["min_year"]]
    if filters.get("max_year"):
        filtered = [c for c in filtered if c["year"] <= filters["max_year"]]
    
    # Mileage range
    if filters.get("min_mileage"):
        filtered = [c for c in filtered if c["mileage"] >= filters["min_mileage"]]
    if filters.get("max_mileage"):
        filtered = [c for c in filtered if c["mileage"] <= filters["max_mileage"]]
    
    # Fuel type
    if filters.get("fuel_type"):
        filtered = [c for c in filtered if c["fuel_type"] == filters["fuel_type"]]
    
    # Transmission
    if filters.get("transmission"):
        filtered = [c for c in filtered if c["transmission"] == filters["transmission"]]
    
    # Body type
    if filters.get("body_type"):
        filtered = [c for c in filtered if c["body_type"] == filters["body_type"]]
    
    return filtered

def get_unique_makes():
    """Return sorted list of unique car makes."""
    cars = get_all_cars()
    makes = sorted(set(c["make"] for c in cars))
    return makes

def get_price_range():
    """Return min and max price across all cars."""
    cars = get_all_cars()
    prices = [c["price"] for c in cars]
    return min(prices), max(prices)

def get_year_range():
    """Return min and max year across all cars."""
    cars = get_all_cars()
    years = [c["year"] for c in cars]
    return min(years), max(years)

def estimate_value(car):
    """Simple valuation calculator based on year, mileage, and condition."""
    base_price = car["price"]
    current_year = datetime.now().year
    age = current_year - car["year"]
    
    # Depreciation: ~15% per year
    depreciation = 1 - (0.15 * age)
    if depreciation < 0.3:
        depreciation = 0.3
    
    # Mileage adjustment: lose 1% per 5,000 km over 30,000
    mileage_over = max(0, (car["mileage"] - 30000) / 5000)
    mileage_penalty = 1 - (mileage_over * 0.01)
    if mileage_penalty < 0.6:
        mileage_penalty = 0.6
    
    # Condition multiplier
    condition_multiplier = {
        "Excellent": 1.05,
        "Very Good": 1.00,
        "Good": 0.95,
        "Fair": 0.85
    }.get(car["condition"], 0.95)
    
    estimated = base_price * depreciation * mileage_penalty * condition_multiplier
    return int(estimated)
