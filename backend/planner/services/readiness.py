"""Event Readiness Score (0-100): one number summarising how prepared the event is."""
from . import budget, weather


def compute(event):
    fixes, parts = [], {}

    tasks = list(event.tasks.all())
    done = sum(t.done for t in tasks)
    parts["Tasks"] = (round(30 * done / len(tasks)) if tasks else 0, 30)
    if tasks and done < len(tasks):
        fixes.append(f"Complete the remaining {len(tasks) - done} task(s).")

    b = budget.summary(event)
    if b["budget"] and b["projected"] <= b["budget"]:
        parts["Budget"] = (20, 20)
    elif b["budget"] and b["projected"]:
        parts["Budget"] = (round(20 * b["budget"] / b["projected"]), 20)
        fixes.append("Bring projected spending back within budget.")
    else:
        parts["Budget"] = (0, 20)
        fixes.append("Set a budget and expenses.")

    guests = list(event.guests.all())
    replied = sum(g.rsvp != "pending" for g in guests)
    parts["RSVPs"] = (round(20 * replied / len(guests)) if guests else 0, 20)
    if not guests:
        fixes.append("Add your guest list.")
    elif replied < len(guests):
        fixes.append(f"{len(guests) - replied} guest(s) haven't replied yet.")

    booked = 8 * bool(event.venue_id or event.venue_name) + 7 * any(e.actual > 0 for e in event.expenses.all())
    parts["Venue & vendors"] = (booked, 15)
    if not (event.venue_id or event.venue_name):
        fixes.append("Choose a venue.")
    if booked < 15:
        fixes.append("Record actual costs once vendors are booked.")

    w = weather.forecast_for(event.city, event.date, event.is_outdoor)
    if not w.get("available"):
        parts["Weather"] = (10, 15)
    else:
        parts["Weather"] = {"low": (15, 15), "medium": (8, 15), "high": (0, 15)}[w["risk"]]
        if w["risk"] != "low":
            fixes.append("Prepare a weather Plan B (see the weather card).")

    score = sum(p[0] for p in parts.values())
    label = "Excellent" if score >= 85 else "On track" if score >= 65 else "Needs attention" if score >= 40 else "Just getting started"
    return {"score": score, "label": label, "breakdown": {k: {"points": v[0], "max": v[1]} for k, v in parts.items()},
            "fixes": fixes, "weather": w}
