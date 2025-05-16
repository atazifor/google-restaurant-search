"""
Main API
https://developers.google.com/maps/documentation/places/web-service/legacy/details
"""

import os
import requests
import json
import csv
import time

# Configuration
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
LOCATION = "Yaounde, Cameroon"
SEARCH_TERM = "restaurants"
MAX_RESULTS = 200  # Set higher limit for testing

# Field Mapping (API Fields → CSV Headers)
FIELD_MAPPING = {
    # API Field: (CSV Header, Default Value)
    "name": ("Name", ""),
    "formatted_address": ("Description", ""),
    "formatted_phone_number": ("Phone", ""),
    "types": ("Category", []),
    "url": ("URL", ""),
    "serves_beer": ("Serves Beer", False),
    "serves_breakfast": ("Serves Breakfast", False),
    "serves_brunch": ("Serves Brunch", False),
    "serves_dinner": ("Serves Dinner", False),
    "serves_lunch": ("Serves Lunch", False),
    "serves_vegetarian_food": ("Serves Vegetarian Food", False),
    "serves_wine": ("Serves Wine", False),
    "takeout": ("Takeout", False),
    "delivery": ("Delivery", False),
    "dine_in": ("Dine In", False),
    "business_status": ("Business Status", ""),
    "rating": ("Rating", 0),
    "user_ratings_total": ("User Ratings Total", 0)
}

def fetch_places():
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{SEARCH_TERM} in {LOCATION}",
        "key": API_KEY,
        "region": "cm"  # Country code bias for Cameroon
    }
    
    all_results = []
    retry_count = 0
    
    while len(all_results) < MAX_RESULTS:
        response = requests.get(endpoint, params=params)
        result = response.json()
        
        if result.get("status") != "OK":
            print(f"API Error: {result.get('status')}")
            break
            
        all_results.extend(result.get("results", []))
        
        if "next_page_token" not in result:
            break
            
        params["pagetoken"] = result["next_page_token"]
        time.sleep(5)  # Increased delay for token activation
        
        # Progress
        print(f"Fetched {len(all_results)} results...")
    
    return all_results[:MAX_RESULTS]

def get_place_details(place_id):
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "key": API_KEY,
                "fields": ",".join(FIELD_MAPPING.keys()),
                "language": "en"
            }
        )
        return response.json().get("result", {})
    except Exception as e:
        print(f"Error fetching {place_id}: {str(e)}")
        return None

# Main execution
print(f"Searching for {SEARCH_TERM} in {LOCATION}...")
places = fetch_places()

with open("restaurants_yaounde_full.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["SR", "SKU"] + [v[0] for v in FIELD_MAPPING.values()])
    
    for i, place in enumerate(places[:MAX_RESULTS], 1):
        details = get_place_details(place["place_id"])
        if not details:
            continue
            
        # Build row with proper error handling
        row = [i, ""]  # SR and SKU
        for api_field, (header, default) in FIELD_MAPPING.items():
            value = details.get(api_field, default)
            if api_field == "types":
                value = "\n".join(f"- {t}" for t in value) if value else ""
            row.append(value)
        
        writer.writerow(row)
        print(f"Processed {i}/{len(places)}: {details.get('name', 'Unknown')}")

print(f"\nCompleted! Found {len(places)} potential restaurants.")