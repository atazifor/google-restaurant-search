"""
Main API
https://developers.google.com/maps/documentation/places/web-service/legacy/details
"""

import os
import requests
import json
import csv
import time

# Set API key
api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
if not api_key:
    raise ValueError("API key not found in environment variables")

# Configuration
location = "Yaounde, Cameroon"
search_term = "restaurants"
endpoint_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

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

# Progress tracking
current_page = 0
total_places = 0
processed_place_ids = set()

print("Starting data extraction...\n")

with open("restaurants_yaounde.csv", "w", newline="", encoding="utf-8") as f:
    # Prepare CSV headers (SR and SKU first, then mapped headers)
    headers = ["SR", "SKU"] + [v[0] for v in FIELD_MAPPING.values()]
    writer = csv.writer(f)
    writer.writerow(headers)

    params = {"query": f"{search_term} in {location}", "key": api_key}

    while True:
        current_page += 1
        page_places = 0
        
        response = requests.get(endpoint_url, params=params)
        result = json.loads(response.text)
        
        print(f"📄 Processing Page {current_page}...")
        
        if "results" not in result:
            print("No more results found.")
            break
            
        for place in result["results"]:
            place_id = place["place_id"]
            
            if place_id in processed_place_ids:
                continue
                
            processed_place_ids.add(place_id)
            
            # Get place details
            detail_response = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "key": api_key,
                    "fields": ",".join(FIELD_MAPPING.keys())
                }
            )
            detail_result = detail_response.json()
            
            if "result" not in detail_result:
                print(f"   ❌ No details found for {place_id}")
                continue
                
            try:
                result_data = detail_result["result"]
                # Prepare row data
                row = [place_id, ""]  # SR and SKU first
                
                for api_field, (header, default) in FIELD_MAPPING.items():
                    value = result_data.get(api_field, default)
                    
                    # Special handling for types array
                    if api_field == "types":
                        value = "\n".join(f"- {item}" for item in value) if value else ""
                    
                    row.append(value)
                
                writer.writerow(row)
                page_places += 1
                total_places += 1
                print(f"   ✅ {result_data.get('name', place_id)}")
                
            except Exception as e:
                print(f"   ❌ Failed {place_id}: {str(e)}")
                continue

        print(f"✔ Page {current_page} complete: {page_places} places | Total: {total_places}\n")
        
        if "next_page_token" not in result:
            print("🏁 Reached end of results")
            break
            
        params["pagetoken"] = result["next_page_token"]
        time.sleep(2)  # Required by Google API

print(f"\n🎉 Success! Exported {total_places} restaurants to 'restaurants_yaounde.csv'")