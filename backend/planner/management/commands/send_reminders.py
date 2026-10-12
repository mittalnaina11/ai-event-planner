"""Run daily (cron / Task Scheduler):  python manage.py send_reminders
Creates in-app notifications and emails for upcoming events, due tasks and weather risk changes."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from planner.models import Event, Notification
from planner.services import weather
from planner.services.notify import notify


class Command(BaseCommand):
    help = "Send event reminders, task-due alerts and weather warnings"

    def handle(self, *args, **opts):
        today, sent = date.today(), 0

        def once(user, msg, ev, kind):
            nonlocal sent
            if not Notification.objects.filter(user=user, message=msg, created_at__date=today).exists():
                notify(user, msg, ev, kind)
                sent += 1

        for ev in Event.objects.filter(date__gte=today, date__lte=today + timedelta(days=16)).select_related("owner"):
            days = (ev.date - today).days
            if days in (7, 3, 1, 0):
                once(ev.owner, f'"{ev.title}" is {"today" if days == 0 else f"in {days} day(s)"}!', ev, "reminder")
            for t in ev.tasks.filter(done=False, due_date__lte=today + timedelta(days=2)):
                once(ev.owner, f'Task due soon for "{ev.title}": {t.title} ({t.due_date})', ev, "task")
            w = weather.forecast_for(ev.city, ev.date, ev.is_outdoor)
            if w.get("available") and w["risk"] == "high":
                once(ev.owner, f'Weather alert for "{ev.title}": {w["summary"]}, rain chance {w["rain_chance"]}%. '
                               f'Plan B: {w["plan_b"][0] if w["plan_b"] else "review your arrangements"}.', ev, "weather")
        self.stdout.write(self.style.SUCCESS(f"{sent} notification(s) sent."))
