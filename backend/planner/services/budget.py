"""Smart budget allocation and optimisation (rule-based, easily replaced by an ML model)."""
SPLITS = {
    "wedding": {"Venue": .28, "Catering": .35, "Decor": .12, "Photography": .08, "Entertainment": .08, "Misc": .09},
    "birthday": {"Venue": .20, "Catering": .35, "Decor": .15, "Entertainment": .15, "Cake & Gifts": .10, "Misc": .05},
    "corporate": {"Venue": .30, "Catering": .30, "AV & Tech": .15, "Marketing": .10, "Speakers": .10, "Misc": .05},
    "college_fest": {"Venue": .15, "Stage & AV": .25, "Catering": .20, "Marketing": .15, "Prizes": .15, "Misc": .10},
    "conference": {"Venue": .30, "Catering": .25, "AV & Tech": .20, "Speakers": .15, "Marketing": .05, "Misc": .05},
    "party": {"Venue": .25, "Catering": .35, "Decor": .12, "Entertainment": .20, "Misc": .08},
    "other": {"Venue": .30, "Catering": .35, "Decor": .10, "Entertainment": .10, "Misc": .15},
}
# how "cuttable" each category is (higher = easier to trim)
FLEX = {"Decor": .35, "Entertainment": .35, "Photography": .2, "Marketing": .3, "Prizes": .25, "Misc": .3,
        "Cake & Gifts": .2, "Catering": .1, "Venue": .05, "AV & Tech": .1, "Stage & AV": .1, "Speakers": .1}


def allocate(event):
    split = SPLITS.get(event.event_type, SPLITS["other"])
    return {cat: round(float(event.budget) * share) for cat, share in split.items()}


def summary(event):
    exp = list(event.expenses.all())
    est = sum(float(e.estimated) for e in exp)
    act = sum(float(e.actual) for e in exp)
    projected = sum(float(e.actual) if e.actual else float(e.estimated) for e in exp)
    budget = float(event.budget)
    out = {"budget": budget, "estimated": est, "actual": act, "projected": projected,
           "remaining": budget - projected, "per_guest": round(projected / event.guest_count) if event.guest_count else 0,
           "warning": None, "tips": []}
    if projected > budget:
        over = projected - budget
        out["warning"] = f"Projected spending exceeds your budget by ₹{over:,.0f}."
        weights = {e.category: float(e.actual or e.estimated) * FLEX.get(e.category, .15) for e in exp}
        total_w = sum(weights.values()) or 1
        for e in exp:
            cut = over * weights[e.category] / total_w
            base = float(e.actual or e.estimated)
            if cut >= 500 and base:
                out["tips"].append(f"Trim {e.category} by about ₹{cut:,.0f} ({cut / base * 100:.0f}%).")
        cat = next((e for e in exp if e.category == "Catering"), None)
        if cat and event.guest_count:
            pg = float(cat.estimated) / event.guest_count
            out["tips"].append(f"Each guest costs about ₹{pg:,.0f} in catering; trimming 10 guests saves about ₹{pg * 10:,.0f}.")
    else:
        out["tips"].append(f"You are within budget with ₹{budget - projected:,.0f} to spare.")
    return out
