
"""Discover real-world venues and event-related places via OpenStreetMap."""
import json
import urllib.parse
import urllib.request


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def discover_places(city, limit=15):
    """Return publicly mapped places relevant to event planning in a city."""
    if not city or not city.strip():
        return []

    
    query = f"""
    [out:json][timeout:25];
    area["name"="{city.strip()}"]["boundary"="administrative"]->.searchArea;
    (
      nwr["leisure"="event_venue"](area.searchArea);
      nwr["amenity"="events_venue"](area.searchArea);
      nwr["amenity"="banquet_hall"](area.searchArea);
      nwr["building"="civic"](area.searchArea);
      nwr["amenity"="community_centre"](area.searchArea);
      nwr["tourism"="hotel"](area.searchArea);
      nwr["amenity"="restaurant"](area.searchArea);
    );
    out center tags;
    """


    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={
            "User-Agent": "AIEventPlanner/1.0 (event venue discovery)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.load(response)
    except Exception:
        return []

    places = []
    for item in data.get("elements", []):
        tags = item.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        center = item.get("center", {})
        lat = item.get("lat", center.get("lat"))
        lon = item.get("lon", center.get("lon"))

        places.append({
            "name": name,
            "city": city.strip(),
            "category": (
                tags.get("leisure")
                or tags.get("amenity")
                or tags.get("tourism")
                or "place"
            ),
            "address": ", ".join(
                filter(None, [
                    tags.get("addr:street"),
                    tags.get("addr:city"),
                    tags.get("addr:postcode"),
                ])
            ),
            "lat": lat,
            "lng": lon,
            "website": tags.get("website", ""),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "source": "OpenStreetMap",
            "source_url": (
                f"https://www.openstreetmap.org/{item['type']}/{item['id']}"
            ),
        })

    return places[:limit]
