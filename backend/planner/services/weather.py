"""Weather-aware planning using the free Open-Meteo API (no API key needed)."""
import json
import time
import urllib.parse
import urllib.request
from datetime import date

CODES = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
         51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain",
         65: "Heavy rain", 71: "Snow", 80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
         95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"}
_cache = {}


def _get(url):
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    with urllib.request.urlopen(url, timeout=6) as r:
        data = json.load(r)
    _cache[url] = (time.time(), data)
    return data


def forecast_for(city, day, outdoor=False):
    """Returns a dict describing the forecast, risk level, tips and Plan B suggestions."""
    try:
        geo = _get("https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({"name": city, "count": 1}))
        res = geo.get("results")
        if not res:
            return {"available": False, "message": f'Could not find location "{city}".'}
        lat, lon, place = res[0]["latitude"], res[0]["longitude"], res[0].get("name", city)
        days_away = (day - date.today()).days
        base = {"lat": lat, "lon": lon, "location": place}
        if days_away < 0:
            return {**base, "available": False, "message": "This event date is in the past."}
        if days_away > 15:
            return {**base, "available": False,
                    "message": "Forecast is available within 16 days of the event. We'll re-check as the date gets closer."}
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "timezone": "auto", "start_date": day.isoformat(), "end_date": day.isoformat(),
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"})
        d = _get("https://api.open-meteo.com/v1/forecast?" + q)["daily"]
        code, tmax, tmin = d["weathercode"][0], d["temperature_2m_max"][0], d["temperature_2m_min"][0]
        rain, wind = d["precipitation_probability_max"][0] or 0, d["wind_speed_10m_max"][0] or 0
    except Exception as exc:  # network down, API change, etc.
        return {"available": False, "message": f"Weather service unavailable right now ({type(exc).__name__})."}

    tips, plan_b, level = [], [], "low"
    if rain >= 60 or code in (65, 82, 95, 96, 99):
        level = "high"
        tips.append(f"High chance of rain ({rain}%).")
        plan_b += ["Book a tent / canopy or shift to an indoor hall", "Keep a backup indoor venue on hold",
                   "Arrange umbrellas and covered walkways", "Consider rescheduling if guests travel far"]
    elif rain >= 30:
        level = "medium"
        tips.append(f"Some chance of rain ({rain}%). Keep a covered area ready.")
        plan_b += ["Keep tents or an indoor fallback on standby"]
    if tmax >= 36:
        level = "high" if tmax >= 40 else max(level, "medium", key=["low", "medium", "high"].index)
        tips.append(f"Very hot ({tmax}°C): arrange shade, fans/coolers and plenty of drinking water.")
        plan_b += ["Move the main programme to the evening"]
    elif tmax <= 12:
        level = max(level, "medium", key=["low", "medium", "high"].index)
        tips.append(f"Cold weather ({tmin}°C at night): arrange heaters and warm drinks.")
    if wind >= 40:
        level = max(level, "medium", key=["low", "medium", "high"].index)
        tips.append(f"Strong winds ({wind} km/h): secure decor, banners and lighting.")
    if not tips:
        tips.append("Conditions look good for the event.")
    effective = level if outdoor else ("low" if level != "high" or rain < 60 else "medium")
    return {**base, "available": True, "summary": CODES.get(code, "Mixed conditions"), "temp_max": tmax, "temp_min": tmin,
            "rain_chance": rain, "wind": wind, "risk": effective, "tips": tips,
            "plan_b": plan_b if outdoor else [], "outdoor": outdoor}
