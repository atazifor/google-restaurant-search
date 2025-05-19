import os
import requests
import csv
import time
from collections import defaultdict

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
INPUT_FILE = "yaounde_restaurant_ids.txt"
OUTPUT_FILE = "restaurants_yaounde_verified.csv"
REQUEST_DELAY = 0.2  # seconds

# Field Mapping (API Fields → CSV Headers)
FIELD_MAPPING = {
    "name": ("Name", ""),
    "formatted_address": ("Address", ""),
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

def get_place_details(place_id):
    """Fetch detailed information for a single place"""
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "key": API_KEY,
                "fields": ",".join(FIELD_MAPPING.keys()) + ",geometry",
                "language": "en"
            }
        )
        result = response.json()
        
        if "result" not in result:
            print(f"❌ No details for {place_id} (status: {result.get('status')})")
            return None
            
        return result["result"]
        
    except Exception as e:
        print(f"❌ Error fetching {place_id}: {str(e)}")
        return None

def main():
    # Read place IDs from file
    with open(INPUT_FILE) as f:
        place_ids = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Found {len(place_ids)} place IDs to process")
    
    # Prepare output file
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Write headers (SR, SKU + mapped fields)
        headers = ["SR", "SKU"] + [v[0] for v in FIELD_MAPPING.values()] + ["Latitude", "Longitude"]
        writer.writerow(headers)
        
        processed_count = 0
        type_counter = defaultdict(int)
        
        for i, place_id in enumerate(place_ids, 1):
            # Get place details
            details = get_place_details(place_id)
            if not details:
                continue
                
            # Build CSV row
            row = [i, ""]  # SR and SKU columns
            
            for api_field, (header, default) in FIELD_MAPPING.items():
                value = details.get(api_field, default)
                
                # Special formatting for types array
                if api_field == "types":
                    value = "\n".join(f"- {t}" for t in value) if value else ""
                    for t in details.get("types", []):
                        type_counter[t] += 1
                row.append(value)

            # Add latitude and longitude after processing all other fields    
            geometry = details.get("geometry", {})
            location = geometry.get("location", {})
            row.append(location.get("lat", 0.0))  # Latitude
            row.append(location.get("lng", 0.0))
                
                
            
            writer.writerow(row)
            processed_count += 1
            
            # Progress update every 10 records
            if i % 10 == 0:
                remaining = len(place_ids) - i
                eta = remaining * REQUEST_DELAY / 60  # minutes
                print(f"✅ Processed {i}/{len(place_ids)} (ETA: {eta:.1f}min) - Last: {details.get('name', place_id)}")
            
            # Respect API rate limits
            time.sleep(REQUEST_DELAY)  # 200ms between requests
    
    # Print summary
    print(f"\n🎉 Successfully processed {processed_count}/{len(place_ids)} places")
    print(f"📄 Output saved to {OUTPUT_FILE}")
    
    # Print type distribution
    print("\n🔍 Type Distribution (Top 10):")
    for t, count in sorted(type_counter.items(), key=lambda x: -x[1])[:10]:
        print(f"- {t}: {count}")

if __name__ == "__main__":
    main()