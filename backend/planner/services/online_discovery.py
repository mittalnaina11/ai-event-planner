
"""Discover real-world venues and event-related places via OpenStreetMap."""

import json
import urllib.parse
import urllib.request
from urllib.parse import quote, urlparse



OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]



def get_place_photo_url(tags):
    """Return a mapped photo URL when one is available."""
    tags = tags or {}

    image = tags.get("image") or tags.get("image:0")
    if image:
        parsed = urlparse(image)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return image

    commons = tags.get("wikimedia_commons", "")
    if commons.startswith("File:"):
        filename = commons[5:].strip()
        if filename:
            return (
                "https://commons.wikimedia.org/wiki/Special:FilePath/"
                + quote(filename, safe="")
            )

    return None


def _geocode_city(city_name):
    """Look up a city centre via Nominatim (used when OSM has no admin-boundary area)."""
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": f"{city_name}, India", "format": "json", "limit": 1, "countrycodes": "in"}
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "AIEventPlanner/1.0 (event venue discovery)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.load(response)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        print(f"Nominatim geocoding failed for {city_name}: {exc}", flush=True)
    return None


def _build_query(escaped_city, center=None, radius=8000):
    selectors = [
        '["leisure"="event_venue"]',
        '["amenity"="events_venue"]',
        '["amenity"="banquet_hall"]',
        '["building"="civic"]',
        '["amenity"="community_centre"]',
        '["tourism"="hotel"]',
        '["amenity"="restaurant"]',
    ]
    if center:
        scope = f"(around:{radius},{center[0]},{center[1]})"
        header = ""
    else:
        scope = "(area.searchArea)"
        header = (
            f'area["name"="{escaped_city}"]["boundary"="administrative"]->.searchArea;\n'
        )
    body = "\n".join(f"      nwr{sel}{scope};" for sel in selectors)
    return f"[out:json][timeout:25];\n{header}(\n{body}\n);\nout center tags;"


def _run_overpass(query, city_name):
    for endpoint in OVERPASS_URLS:
        request = urllib.request.Request(
            endpoint,
            data=urllib.parse.urlencode({"data": query}).encode(),
            headers={
                "User-Agent": "AIEventPlanner/1.0 (event venue discovery)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            found = payload.get("elements", [])
            if found:
                print(f"OpenStreetMap found {len(found)} elements for {city_name} using {endpoint}", flush=True)
                return found
            print(f"Overpass returned no matching elements for {city_name}: {endpoint}", flush=True)
        except Exception as exc:
            print(f"Overpass server failed for {city_name} ({endpoint}): {exc}", flush=True)
    return []


def discover_places(city, limit=15):
    """Return real, publicly mapped places for an event-planning city."""
    if not city or not city.strip():
        return []

    city_name = city.strip()
    escaped_city = city_name.replace("\\", "\\\\").replace('"', '\\"')

    # 1) Try the city's administrative boundary.
    elements = _run_overpass(_build_query(escaped_city), city_name)

    # 2) Small towns often have no boundary area in OSM: search around the city centre.
    if not elements:
        center = _geocode_city(city_name)
        if center:
            elements = _run_overpass(_build_query(escaped_city, center=center), city_name)

    if not elements:
        print(f"No OpenStreetMap places found for {city_name} after trying all servers.", flush=True)
        return []

    places = []

    for item in elements:
        tags = item.get("tags", {})
        name = tags.get("name")

        if not name:
            continue

        center = item.get("center", {})
        lat = item.get("lat", center.get("lat"))
        lon = item.get("lon", center.get("lon"))

        places.append({
            "name": name,
            "city": city_name,
            "category": (
                tags.get("leisure")
                or tags.get("amenity")
                or tags.get("tourism")
                or "place"
            ),
            "address": ", ".join(filter(None, [
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:postcode"),
            ])),
            "lat": lat,
            "lng": lon,
            "website": tags.get("website", ""),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "photo_url": get_place_photo_url(tags),
            "source": "OpenStreetMap",
            "source_url": (
                f"https://www.openstreetmap.org/"
                f"{item['type']}/{item['id']}"
            ),
        })

    return places[:limit]
