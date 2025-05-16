import os
import requests
import time
from collections import defaultdict

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
LOCATION = "Yaounde, Cameroon"
MAX_RESULTS = 300  # Target number of unique places

# Expanded list of search terms
SEARCH_TERMS = [
    "restaurant", "restaurants", 
    "cafe", "cafes",
    "bar", "bars",
    "bistro", "food",
    "eat", "dining",
    "place to eat", "local food",
    "cameroonian food", "african restaurant",
    "fast food", "pizza",
    "burger", "chicken",
    "seafood", "bakery"
]

def fetch_places(search_term):
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{search_term} in {LOCATION}",
        "key": API_KEY,
        "region": "cm"
    }
    
    unique_places = set()
    session_places = []
    
    while len(unique_places) < MAX_RESULTS:
        try:
            response = requests.get(endpoint, params=params)
            result = response.json()
            
            if result.get("status") != "OK":
                print(f"⚠️ [{search_term}] API Error: {result.get('status')}")
                break
                
            new_places = result.get("results", [])
            new_ids = [p["place_id"] for p in new_places]
            
            # Track duplicates within this search term
            duplicates = sum(1 for pid in new_ids if pid in unique_places)
            unique_places.update(new_ids)
            session_places.extend(new_places)
            
            print(f"🔍 [{search_term}] Page {len(session_places)//20 + 1}: "
                  f"+{len(new_places)} ({duplicates} dup) | "
                  f"Total: {len(unique_places)}")
            
            if "next_page_token" not in result:
                break
                
            params["pagetoken"] = result["next_page_token"]
            time.sleep(3)  # Increased delay for token activation
            
        except Exception as e:
            print(f"❌ [{search_term}] Failed: {str(e)}")
            break
    
    return session_places

def analyze_results(all_places):
    # Count by type
    type_counter = defaultdict(int)
    for place in all_places:
        for t in place.get("types", []):
            type_counter[t] += 1
    
    print("\n📊 Results Analysis:")
    print(f"Total unique places: {len({p['place_id'] for p in all_places})}")
    print(f"Total raw results: {len(all_places)}")
    print("\nMost common place types:")
    for t, count in sorted(type_counter.items(), key=lambda x: -x[1])[:10]:
        print(f"- {t}: {count}")

def main():
    all_places = []
    seen_ids = set()
    
    for term in SEARCH_TERMS:
        print(f"\n🚀 Searching: '{term}'")
        places = fetch_places(term)
        
        # Deduplicate while preserving order
        new_places = [p for p in places if p["place_id"] not in seen_ids]
        seen_ids.update(p["place_id"] for p in new_places)
        all_places.extend(new_places)
        
        if len(seen_ids) >= MAX_RESULTS:
            break
    
    analyze_results(all_places)
    
    # Save just the IDs for verification
    with open("place_ids.txt", "w") as f:
        f.write("\n".join(p["place_id"] for p in all_places))
    
    print(f"\n✅ Saved {len(all_places)} place IDs to place_ids.txt")

if __name__ == "__main__":
    main()