"""Generates the task checklist, event-day schedule and budget rows for a new event."""
from datetime import date, datetime, timedelta

from ..models import Expense, ScheduleItem, Task
from . import budget

COMMON = [("Finalize budget", 45), ("Book the venue", 40), ("Shortlist and book vendors", 30),
          ("Finalize guest list", 25), ("Send invitations", 21), ("Confirm menu and catering", 14),
          ("Check weather forecast and decide Plan B", 7), ("Follow up on RSVPs", 5),
          ("Final confirmation with all vendors", 3), ("Prepare event-day checklist", 1)]
EXTRA = {
    "wedding": [("Book photographer", 60), ("Plan rituals and ceremonies", 35), ("Arrange guest accommodation", 30)],
    "birthday": [("Order cake", 7), ("Plan games / entertainment", 14)],
    "corporate": [("Confirm speakers and agenda", 30), ("Test AV equipment", 3), ("Prepare name badges", 5)],
    "college_fest": [("Get permissions and approvals", 40), ("Arrange sponsors", 35), ("Publicize on social media", 21)],
    "conference": [("Open registrations", 45), ("Confirm speakers", 35), ("Prepare certificates", 5)],
}
SCHEDULES = {
    "wedding": [(0, "Guest arrival and welcome drinks", 45), (45, "Ceremony", 90), (135, "Photo session", 30),
                (165, "Dinner", 90), (255, "Music and dance", 90)],
    "birthday": [(0, "Guest arrival", 30), (30, "Games and activities", 45), (75, "Cake cutting", 20),
                 (95, "Dinner", 60), (155, "Music and dance", 60)],
    "corporate": [(0, "Registration and networking", 30), (30, "Opening address", 20), (50, "Main sessions", 90),
                  (140, "Lunch break", 45), (185, "Panel discussion", 60), (245, "Closing remarks", 15)],
    "college_fest": [(0, "Inauguration", 30), (30, "Competitions", 120), (150, "Lunch break", 45),
                     (195, "Cultural performances", 90), (285, "Prize distribution", 30)],
    "conference": [(0, "Registration", 30), (30, "Keynote", 45), (75, "Technical sessions", 120),
                   (195, "Lunch", 45), (240, "Workshops", 90), (330, "Closing and networking", 30)],
    "default": [(0, "Guest arrival", 30), (30, "Welcome and opening", 20), (50, "Main programme", 90),
                (140, "Dinner / refreshments", 60), (200, "Wrap-up and thanks", 20)],
}


def populate(event, what=("tasks", "schedule", "budget")):
    if "tasks" in what:
        Task.objects.filter(event=event, auto=True, done=False).delete()
        existing = set(Task.objects.filter(event=event).values_list("title", flat=True))
        for title, days in COMMON + EXTRA.get(event.event_type, []):
            if title in existing:
                continue
            due = max(event.date - timedelta(days=days), date.today())
            Task.objects.create(event=event, title=title, due_date=due, auto=True)
    if "schedule" in what:
        event.schedule.all().delete()
        start = datetime.combine(event.date, event.start_time)
        for offset, title, dur in SCHEDULES.get(event.event_type, SCHEDULES["default"]):
            ScheduleItem.objects.create(event=event, title=title, duration_min=dur,
                                        start_time=(start + timedelta(minutes=offset)).time())
    if "budget" in what and float(event.budget) > 0:
        for cat, amount in budget.allocate(event).items():
            Expense.objects.update_or_create(event=event, category=cat, defaults={"estimated": amount})
