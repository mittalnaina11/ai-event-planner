from django.contrib import admin
from . import models

for m in (models.Profile, models.Venue, models.Vendor, models.Event, models.Guest,
          models.Task, models.Expense, models.Feedback, models.Notification):
    admin.site.register(m)
