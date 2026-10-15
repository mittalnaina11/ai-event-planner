
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


def discover_places(city, limit=15):
    """Return real, publicly mapped places for an event-planning city."""
    if not city or not city.strip():
        return []

    city_name = city.strip()
    escaped_city = city_name.replace("\\", "\\\\").replace('"', '\\"')

    query = f"""
    [out:json][timeout:25];
    area["name"="{escaped_city}"]["boundary"="administrative"]->.searchArea;
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

    elements = []

    # Try alternate public Overpass servers if one fails or returns no matches.
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
                elements = found
                print(
                    f"OpenStreetMap found {len(elements)} elements "
                    f"for {city_name} using {endpoint}",
                    flush=True,
                )
                break

            print(
                f"Overpass returned no matching elements for {city_name}: "
                f"{endpoint}",
                flush=True,
            )

        except Exception as exc:
            print(
                f"Overpass server failed for {city_name} "
                f"({endpoint}): {exc}",
                flush=True,
            )

    if not elements:
        print(
            f"No OpenStreetMap places found for {city_name} "
            "after trying all servers.",
            flush=True,
        )
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
