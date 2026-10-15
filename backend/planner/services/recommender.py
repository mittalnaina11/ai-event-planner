"""Content-based venue/vendor recommender (TF-IDF + cosine similarity) with a user-rating feedback loop."""
from ..models import Rating, Vendor, Venue
from . import ai
from .online_discovery import discover_places

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # graceful fallback so the app still runs without scikit-learn
    TfidfVectorizer = None

VENDOR_CATS = {"wedding": ["Catering", "Decor", "Photography", "Entertainment", "Makeup"],
               "birthday": ["Catering", "Decor", "Entertainment", "Photography"],
               "corporate": ["Catering", "AV & Tech", "Photography"],
               "college_fest": ["Catering", "AV & Tech", "Entertainment", "Decor"],
               "conference": ["Catering", "AV & Tech", "Photography"]}


def _similarity(query, docs):
    if not docs:
        return []
    if TfidfVectorizer is None:
        q = set(query.lower().split())
        return [len(q & set(d.lower().split())) / (len(q) or 1) for d in docs]
    m = TfidfVectorizer().fit_transform([query] + docs)
    return list(cosine_similarity(m[0:1], m[1:])[0])


def _user_avg(kind):
    from django.db.models import Avg
    return {r["object_id"]: r["a"] for r in Rating.objects.filter(kind=kind).values("object_id").annotate(a=Avg("score"))}


def _blend(sim, rating, fit, user_avg):
    score = 0.5 * sim + 0.2 * (rating / 5) + 0.2 * fit
    score += 0.1 * (user_avg / 5 if user_avg else rating / 5)
    return score


def recommend(event, user=None, limit=5):
    query = f"{event.event_type} {event.theme} {event.description} {'outdoor garden' if event.is_outdoor else 'indoor hall ac'}"
    budget = float(event.budget)
    my = {(r.kind, r.object_id): r.score for r in Rating.objects.filter(user=user)} if user else {}

    venues = list(Venue.objects.filter(capacity__gte=max(event.guest_count, 1)))
    online_places = discover_places(event.city, limit=15)
    online_places = ai.rank_online_places(event, online_places)
    sims = _similarity(query, [f"{v.tags} {'outdoor garden' if v.outdoor else 'indoor hall ac'}" for v in venues])
    uavg = _user_avg("venue")
    out_v = []
    for v, s in zip(venues, sims):
        fit = 1.0 if not budget or v.price <= budget * 0.4 else max(0, 1 - (v.price - budget * 0.4) / (budget or 1))
        score = _blend(s, v.rating, fit, uavg.get(v.id)) + (0.25 if v.city.lower() == event.city.lower() else 0)
        why = [f"Fits {event.guest_count} guests (capacity {v.capacity})"]
        if v.city.lower() == event.city.lower():
            why.append("In your city")
        if budget and v.price <= budget * 0.4:
            why.append("Within a healthy share of your budget")
        out_v.append({"id": v.id, "name": v.name, "city": v.city, "price": v.price, "rating": v.rating, "capacity": v.capacity,
                      "tags": v.tags, "outdoor": v.outdoor, "lat": v.lat, "lng": v.lng, "score": score, "why": why,
                      "my_rating": my.get(("venue", v.id))})
    out_v.sort(key=lambda x: -x["score"])

    wanted = VENDOR_CATS.get(event.event_type, ["Catering", "Decor", "Entertainment"])
    vendors = list(Vendor.objects.filter(category__in=wanted))
    sims = _similarity(query, [f"{v.category} {v.tags}" for v in vendors])
    uavg = _user_avg("vendor")
    out_d = []
    for v, s in zip(vendors, sims):
        fit = 1.0 if not budget or v.price_from <= budget * 0.3 else 0.4
        score = _blend(s, v.rating, fit, uavg.get(v.id)) + (0.25 if v.city.lower() == event.city.lower() else 0)
        out_d.append({"id": v.id, "name": v.name, "category": v.category, "city": v.city, "price": v.price_from,
                      "rating": v.rating, "tags": v.tags, "score": score, "contact": v.contact,
                      "why": ["In your city"] if v.city.lower() == event.city.lower() else [],
                      "my_rating": my.get(("vendor", v.id))})
    out_d.sort(key=lambda x: -x["score"])

    top = max([x["score"] for x in out_v + out_d] or [1])
    for x in out_v + out_d:
        x["score"] = round(x["score"] / top * 100)
    # keep the best few per vendor category so the list is diverse
    per_cat, diverse = {}, []
    for x in out_d:
        per_cat[x["category"]] = per_cat.get(x["category"], 0) + 1
        if per_cat[x["category"]] <= 2:
            diverse.append(x)
        online_results = []
    for p in online_places:
        online_results.append({
            "id": None,
            "name": p["name"],
            "city": p["city"],
            "price": None,
            "rating": None,
            "capacity": None,
            "tags": p["category"],
            "outdoor": False,
            "lat": p["lat"],
            "lng": p["lng"],
            "score": 0,
            "why": ["Discovered online via OpenStreetMap; details need verification"],
            "my_rating": None,
            "source": p["source"],
            "source_url": p["source_url"],
            "website": p["website"],
            "address": p["address"],
            "online": True,
        })

    return {
        "venues": out_v[:limit],
        "online_places": online_results[:limit],
        "vendors": diverse[:limit * 2],
    }
