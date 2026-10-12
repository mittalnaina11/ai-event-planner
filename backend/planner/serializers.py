from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (Event, Expense, Feedback, Guest, Notification, ScheduleItem, Task, Vendor, Venue)


class EventSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    venue_detail = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["owner", "created_at"]

    def get_role(self, obj):
        user = self.context["request"].user
        if obj.owner_id == user.id:
            return "owner"
        c = obj.collaborators.filter(user=user).first()
        return c.role if c else None

    def get_venue_detail(self, obj):
        v = obj.venue
        return {"id": v.id, "name": v.name, "lat": v.lat, "lng": v.lng} if v else None

    def validate_date(self, value):
        if self.instance is None and value < date.today():
            raise serializers.ValidationError("Event date cannot be earlier than today.")
        return value

    def validate(self, data):
        if data.get("guest_count") is not None and data["guest_count"] < 1:
            raise serializers.ValidationError("Guest count must be at least 1.")
        return data


class GuestSerializer(serializers.ModelSerializer):
    rsvp_url = serializers.SerializerMethodField()

    class Meta:
        model = Guest
        fields = "__all__"
        read_only_fields = ["token", "checked_in", "checked_in_at"]

    def get_rsvp_url(self, obj):
        return f"{settings.FRONTEND_URL}/rsvp/{obj.token}"


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.username", read_only=True, default=None)

    class Meta:
        model = Task
        fields = "__all__"


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleItem
        fields = "__all__"


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source="guest.name", read_only=True, default="Anonymous")

    class Meta:
        model = Feedback
        fields = "__all__"


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = "__all__"


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
        read_only_fields = ["owner"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class UserAdminSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True, default="user")

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active", "is_staff", "date_joined", "role"]
