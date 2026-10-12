from django.conf import settings
from django.core.mail import send_mail

from ..models import Notification


def notify(user, message, event=None, kind="info", email=True):
    Notification.objects.create(user=user, event=event, message=message, kind=kind)
    if email and user.email:
        send_mail("Event Planner", message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
