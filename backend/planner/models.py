import datetime
import uuid
from django.contrib.auth.models import User
from django.db import models

EVENT_TYPES = [("wedding", "Wedding"), ("birthday", "Birthday"), ("corporate", "Corporate"),
               ("college_fest", "College Fest"), ("conference", "Conference"),
               ("party", "Party"), ("other", "Other")]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=[("user", "User"), ("vendor", "Vendor")], default="user")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Venue(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=60)
    address = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=100)
    price = models.PositiveIntegerField(default=50000, help_text="Approx. price per event (INR)")
    tags = models.CharField(max_length=200, blank=True, help_text="comma separated: wedding, garden, ac, ...")
    rating = models.FloatField(default=4.0)
    outdoor = models.BooleanField(default=False)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Vendor(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=40)
    city = models.CharField(max_length=60)
    price_from = models.PositiveIntegerField(default=10000)
    tags = models.CharField(max_length=200, blank=True)
    rating = models.FloatField(default=4.0)
    contact = models.CharField(max_length=120, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="vendor_profiles")

    def __str__(self):
        return f"{self.name} ({self.category})"


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=150)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default="party")
    date = models.DateField()
    start_time = models.TimeField(default=datetime.time(18, 0))
    city = models.CharField(max_length=60)
    venue = models.ForeignKey(Venue, null=True, blank=True, on_delete=models.SET_NULL)
    venue_name = models.CharField(max_length=150, blank=True)
    is_outdoor = models.BooleanField(default=False)
    guest_count = models.PositiveIntegerField(default=50)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    theme = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Collaborator(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="collaborators")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[("editor", "Editor"), ("viewer", "Viewer")], default="editor")

    class Meta:
        unique_together = ("event", "user")


class Guest(models.Model):
    RSVP = [("pending", "Pending"), ("yes", "Yes"), ("no", "No"), ("maybe", "Maybe")]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="guests")
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    group = models.CharField(max_length=40, blank=True, help_text="family, friends, VIP ...")
    diet = models.CharField(max_length=40, blank=True, help_text="veg, vegan, jain, allergies ...")
    rsvp = models.CharField(max_length=10, choices=RSVP, default="pending")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)


class Task(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False)
    auto = models.BooleanField(default=False)
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["done", "due_date"]


class ScheduleItem(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="schedule")
    start_time = models.TimeField()
    title = models.CharField(max_length=150)
    duration_min = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["start_time"]


class Expense(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=60)
    estimated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=200, blank=True)


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=[("venue", "venue"), ("vendor", "vendor")])
    object_id = models.PositiveIntegerField()
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("user", "kind", "object_id")


class Feedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="feedback")
    guest = models.OneToOneField(Guest, null=True, on_delete=models.SET_NULL)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    sentiment = models.CharField(max_length=10, default="neutral")
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=300)
    kind = models.CharField(max_length=20, default="info")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
