"""AI helpers. Uses Gemini when GEMINI_API_KEY is set, otherwise smart rule-based fallbacks (works offline)."""
import json
import re
import urllib.request
from datetime import date, timedelta

from django.conf import settings

TYPE_WORDS = {"wedding": ["wedding", "marriage", "engagement", "reception"], "birthday": ["birthday", "bday"],
              "corporate": ["corporate", "office", "company", "team outing", "offsite"],
              "college_fest": ["fest", "college", "cultural"], "conference": ["conference", "seminar", "summit", "workshop"],
              "party": ["party", "get-together", "gathering", "anniversary"]}
CITIES = ["pune", "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "shirpur",
          "jaipur", "ahmedabad", "goa", "nashik", "nagpur", "surat", "indore", "lucknow", "kochi"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def llm(prompt):
    key = settings.GEMINI_API_KEY
    if not key:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        req = urllib.request.Request(url, data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def _parse_date(t):
    t, today = t.lower(), date.today()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    if "tomorrow" in t:
        return today + timedelta(days=1)
    m = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", t)
    if m:
        ahead = (WEEKDAYS.index(m[1]) - today.weekday()) % 7 or 7
        return today + timedelta(days=ahead)
    pat = "(" + "|".join(MONTHS) + ")"
    for rx, order in ((rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+{pat}", "dm"), (rf"{pat}[a-z]*\s+(\d{{1,2}})", "md")):
        m = re.search(rx, t)
        if m:
            d, mo = (int(m[1]), MONTHS.index(m[2]) + 1) if order == "dm" else (int(m[2]), MONTHS.index(m[1]) + 1)
            try:
                res = date(today.year, mo, d)
                return res if res >= today else date(today.year + 1, mo, d)
            except ValueError:
                return None
    m = re.search(r"in (\d+) (day|week)s?", t)
    if m:
        return today + timedelta(days=int(m[1]) * (7 if m[2] == "week" else 1))
    return None


def _parse_budget(t):
    t = re.sub(r"\d+\s*(guests?|people|persons|pax|members)", " ", t, flags=re.I)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", " ", t)
    mon = "(?:" + "|".join(MONTHS) + ")[a-z]*"
    t = re.sub(rf"\d{{1,2}}(?:st|nd|rd|th)?\s+{mon}|{mon}\s+\d{{1,2}}", " ", t, flags=re.I)
    bare = None
    for m in re.finditer(r"(₹|rs\.?|inr)?\s*(\d[\d,]*\.?\d*)\s*(lakhs?|lacs?|crores?|cr|k|l)?\b", t, re.I):
        raw, unit = m[2].replace(",", "").rstrip("."), (m[3] or "").lower()
        if not raw:
            continue
        mult = {"k": 1e3, "l": 1e5, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5,
                "cr": 1e7, "crore": 1e7, "crores": 1e7}.get(unit, 1)
        if m[1] or unit:
            return float(raw) * mult
        if bare is None and float(raw) >= 1000:
            bare = float(raw)
    return bare


def parse_event_text(text):
    """Turn a free-text request into structured event fields."""
    out = None
    reply = llm('Extract event details from this request and answer ONLY with JSON having keys: title, event_type '
                '(wedding|birthday|corporate|college_fest|conference|party|other), date (YYYY-MM-DD or null), city, '
                f'guest_count (int), budget (number in INR), is_outdoor (bool), theme. Today is {date.today()}. Request: {text}')
    if reply:
        try:
            out = json.loads(re.sub(r"^```(?:json)?|```$", "", reply.strip(), flags=re.M).strip())
        except Exception:
            out = None
    if not out:
        low = text.lower()
        etype = next((k for k, ws in TYPE_WORDS.items() if any(w in low for w in ws)), "party")
        city = next((c for c in CITIES if re.search(rf"\b{c}\b", low)), None)
        if not city:
            m = re.search(r"\bin\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?)", text)
            city = m[1] if m else ""
        g = re.search(r"(\d+)\s*(?:guests?|people|persons|pax|members)", low)
        d = _parse_date(text)
        out = {"event_type": etype, "city": city.title(), "guest_count": int(g[1]) if g else 50, "budget": _parse_budget(text) or 0,
               "date": d.isoformat() if d else None,
               "is_outdoor": any(w in low for w in ["outdoor", "garden", "lawn", "beach", "open-air", "terrace"]),
               "theme": "", "title": f"{etype.replace('_', ' ').title()}" + (f" in {city.title()}" if city else "")}
    return out


def answer(event, message, context):
    """Answer a planning question inside an event. `context` is a dict of facts the caller prepared."""
    reply = llm(f"You are an event-planning assistant. Event facts: {json.dumps(context, default=str)}. "
                f"Answer briefly and practically. Question: {message}")
    if reply:
        return reply
    low = message.lower()
    if any(w in low for w in ["weather", "rain", "forecast", "temperature"]):
        w = context.get("weather", {})
        return (f"{w.get('summary')}, {w.get('temp_min')}–{w.get('temp_max')}°C, rain chance {w.get('rain_chance')}%. "
                + " ".join(w.get("tips", []))) if w.get("available") else w.get("message", "Weather is unavailable.")
    if any(w in low for w in ["budget", "cost", "money", "spend"]):
        b = context["budget"]
        return (f"Budget ₹{b['budget']:,.0f}, projected spend ₹{b['projected']:,.0f}. " + " ".join(b["tips"][:2]))
    if any(w in low for w in ["guest", "rsvp", "invite"]):
        g = context["guests"]
        return f"{g['total']} guests: {g['yes']} yes, {g['no']} no, {g['maybe']} maybe, {g['pending']} pending."
    if any(w in low for w in ["task", "todo", "do next", "pending"]):
        t = context["pending_tasks"]
        return "Next tasks: " + "; ".join(t[:5]) if t else "All tasks are complete. Nice work!"
    return ("I can help with weather, budget, guests/RSVPs and tasks for this event. "
            "Try: 'What's the weather?', 'Am I over budget?' or 'What should I do next?'")


def write_invitation(event, tone="formal", lang="en"):
    reply = llm(f"Write a short {tone} invitation in {'Hindi' if lang == 'hi' else 'English'} for a {event.event_type.replace('_', ' ')} "
                f"titled '{event.title}' on {event.date:%A, %d %B %Y} at {event.start_time:%I:%M %p} in {event.venue_name or event.city}. "
                f"Theme: {event.theme or 'none'}. Ask guests to RSVP. Keep it under 90 words.")
    if reply:
        return reply
    when = f"{event.date:%A, %d %B %Y} at {event.start_time:%I:%M %p}"
    place = event.venue_name or event.city
    if lang == "hi":
        return (f"आप सादर आमंत्रित हैं!\n\n{event.title} में हमारे साथ शामिल होइए।\nदिनांक/समय: {when}\nस्थान: {place}\n\n"
                "कृपया अपनी उपस्थिति की पुष्टि करें। आपका आना हमारे लिए सम्मान की बात होगी।")
    if tone == "fun":
        return (f"🎉 You're invited! 🎉\n\nGet ready for {event.title}! Good food, great company and loads of fun.\n"
                f"📅 {when}\n📍 {place}\n\nTap the link to RSVP so we can save you a spot. Can't wait to celebrate with you!")
    return (f"Dear Guest,\n\nWe cordially invite you to {event.title}, to be held on {when} at {place}.\n\n"
            "Your presence would be greatly appreciated. Kindly confirm your attendance using the RSVP link.\n\nWarm regards")


POS = {"great", "good", "amazing", "loved", "excellent", "fantastic", "wonderful", "awesome", "best", "fun", "nice", "perfect", "happy"}
NEG = {"bad", "poor", "terrible", "worst", "boring", "late", "disappointed", "awful", "dirty", "crowded", "slow", "rude", "cold"}


def sentiment(text):
    words = set(re.findall(r"[a-z']+", text.lower()))
    s = len(words & POS) - len(words & NEG)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"


def rank_online_places(event, places):
    """
    Rank real OpenStreetMap results using Gemini.
    If Gemini is unavailable, keep the original place list.
    """
    if not places:
        return places

    # Keep the prompt small and do not send unnecessary place data.
    candidates = []
    for place in places[:30]:
        candidates.append({
            "name": place.get("name", ""),
            "city": place.get("city", getattr(event, "city", "")),
            "category": place.get("category", ""),
            "address": place.get("address", ""),
            "source_url": place.get("source_url", ""),
        })

    prompt = f"""
You are helping plan a real event.

Event:
- Title: {getattr(event, "title", "Event")}
- Type: {getattr(event, "event_type", "other")}
- City: {getattr(event, "city", "")}
- Guests: {getattr(event, "guest_count", 0)}
- Budget in INR: {getattr(event, "budget", 0)}
- Outdoor event: {getattr(event, "is_outdoor", False)}
- Theme: {getattr(event, "theme", "")}

Here are places retrieved from OpenStreetMap:
{json.dumps(candidates, ensure_ascii=False)}

Rank places for likely relevance to this event. Use only the supplied
facts. Do not invent capacity, prices, ratings, availability, or facilities.
A place's category is only a clue, not proof it can host an event.

Return ONLY a valid JSON array, maximum 10 items, in this format:
[
  {{
    "source_url": "exact source_url from the supplied place",
    "score": 85,
    "reason": "Short explanation of why it may suit this event"
  }}
]
Use each supplied source_url exactly. Do not invent places or URLs.
"""

    try:
        raw = llm(prompt)
        if not raw:
            return places

        # Handle responses wrapped in Markdown code fences.
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3].strip()

        ranked = json.loads(raw)
        if not isinstance(ranked, list):
            return places

        by_source = {
            p.get("source_url"): p
            for p in places
            if p.get("source_url")
        }

        result = []
        seen = set()

        for item in ranked:
            if not isinstance(item, dict):
                continue

            source = item.get("source_url")
            place = by_source.get(source)

            # Accept only places that came from our actual OSM results.
            if not place or source in seen:
                continue

            seen.add(source)
            enriched = dict(place)

            try:
                score = int(item.get("score", 0))
            except (TypeError, ValueError):
                score = 0

            enriched["ai_score"] = max(0, min(100, score))
            enriched["ai_reason"] = str(item.get("reason", ""))[:300]
            result.append(enriched)

        # If Gemini returned unusable JSON, preserve existing results.
        if not result:
            return places

        # Preserve any places Gemini did not include, after ranked ones.
        for place in places:
            if place.get("source_url") not in seen:
                result.append(place)

        return result

    except Exception:
        # Recommendations must still work if Gemini fails.
        return places

