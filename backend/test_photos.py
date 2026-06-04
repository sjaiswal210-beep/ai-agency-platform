import httpx
key = "AIzaSyDGWuYorS9soTfFbP0OrwzFTCpvQubsLhk"

# Search for a business
url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=Royal+Fitness+Gym+Malkapur&key={key}"
r = httpx.get(url, timeout=15)
results = r.json().get("results", [])

if results:
    place_id = results[0]["place_id"]
    print(f"Found: {results[0]['name']}")
    
    # Get photos
    detail_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photos&key={key}"
    dr = httpx.get(detail_url, timeout=15)
    photos = dr.json().get("result", {}).get("photos", [])
    print(f"Photos available: {len(photos)}")
    
    for p in photos[:3]:
        ref = p["photo_reference"]
        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photo_reference={ref}&key={key}"
        print(f"Photo URL: {photo_url}")
else:
    print("No results found")
