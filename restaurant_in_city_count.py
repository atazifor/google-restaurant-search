import os
import requests
import time
from collections import defaultdict

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
LOCATION = "Yaounde, Cameroon"
MAX_UNIQUE_RESULTS = 500  # Target number of unique places

# Enhanced search configuration
SEARCH_TERMS = [
    "restaurant", "cafe", "bar", "bistro", "food",
    "eat", "dining", "local food", "cameroonian food",
    "african restaurant", "fast food", "pizza",
    "burger", "chicken", "seafood", "bakery"
]

PLACE_TYPES = [
    "restaurant", "cafe", "bar", "bakery",
    "food", "meal_delivery", "meal_takeaway"
]

# Yaoundé bounding box coordinates
LAT_RANGE = [3.80, 3.90]  # North-South bounds
LNG_RANGE = [11.45, 11.55]  # East-West bounds
GRID_STEPS = 3  # 3x3 search grid

def generate_search_points():
    """Generate geographic grid points across Yaoundé"""
    lat_step = (LAT_RANGE[1] - LAT_RANGE[0]) / GRID_STEPS
    lng_step = (LNG_RANGE[1] - LNG_RANGE[0]) / GRID_STEPS
    
    for i in range(GRID_STEPS):
        for j in range(GRID_STEPS):
            yield (
                LAT_RANGE[0] + i * lat_step,
                LNG_RANGE[0] + j * lng_step
            )

def search_places(params):
    """Execute search with pagination"""
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    unique_places = set()
    session_results = []
    
    while len(unique_places) < 60:  # Max per search variant
        try:
            response = requests.get(endpoint, params=params)
            result = response.json()
            
            if result.get("status") != "OK":
                break
                
            new_places = result.get("results", [])
            new_ids = {p["place_id"] for p in new_places}
            
            unique_places.update(new_ids)
            session_results.extend(new_places)
            
            if "next_page_token" not in result:
                break
                
            params["pagetoken"] = result["next_page_token"]
            time.sleep(3)  # Critical for token activation
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            break
    
    return session_results

def main():
    all_places = []
    seen_ids = set()
    search_count = 0
    
    print(f"🚀 Beginning comprehensive search in {LOCATION}...\n")
    
    # Strategy 1: Text searches across geographic grid
    for lat, lng in generate_search_points():
        for term in SEARCH_TERMS:
            params = {
                "query": term,
                "location": f"{lat},{lng}",
                "radius": 3000,  # 3km radius
                "key": API_KEY,
                "region": "cm"
            }
            results = search_places(params)
            new_places = [p for p in results if p["place_id"] not in seen_ids]
            seen_ids.update(p["place_id"] for p in new_places)
            all_places.extend(new_places)
            search_count += 1
            print(f"🔍 [{search_count}] {term} @ {lat:.3f},{lng:.3f}: "
                  f"+{len(new_places)} new (Total: {len(seen_ids)})")
            
            if len(seen_ids) >= MAX_UNIQUE_RESULTS:
                break
        if len(seen_ids) >= MAX_UNIQUE_RESULTS:
            break
    
    # Strategy 2: Type-specific searches
    type_counts = defaultdict(int)
    for place_type in PLACE_TYPES:
        params = {
            "type": place_type,
            "location": "3.8480,11.5021",  # Yaoundé center
            "radius": 15000,  # 15km radius
            "key": API_KEY
        }
        results = search_places(params)
        new_places = [p for p in results if p["place_id"] not in seen_ids]
        type_counts[place_type] = len(new_places)
        seen_ids.update(p["place_id"] for p in new_places)
        all_places.extend(new_places)
        search_count += 1
        print(f"🔍 [{search_count}] Type:{place_type}: "
              f"+{len(new_places)} new (Total: {len(seen_ids)})")
        
        if len(seen_ids) >= MAX_UNIQUE_RESULTS:
            break
    
    # Results analysis
    print("\n📊 Final Results Analysis")
    print(f"Total unique places found: {len(seen_ids)}")
    print(f"Total API calls made: {search_count}")
    
    # Type breakdown
    print("\n🔎 Type distribution:")
    type_dist = defaultdict(int)
    for place in all_places:
        for t in place.get("types", []):
            type_dist[t] += 1
    for t, count in sorted(type_dist.items(), key=lambda x: -x[1])[:15]:
        print(f"- {t}: {count}")
    
    # Save raw IDs
    with open("yaounde_restaurant_ids.txt", "w") as f:
        f.write("\n".join(seen_ids))
    print(f"\n✅ Saved {len(seen_ids)} place IDs to yaounde_restaurant_ids.txt")

if __name__ == "__main__":
    main()