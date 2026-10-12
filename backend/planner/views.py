import uuid
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import (Collaborator, Event, Expense, Feedback, Guest, Notification, Profile, Rating,
                     ScheduleItem, Task, Vendor, Venue)
from .serializers import (EventSerializer, ExpenseSerializer, FeedbackSerializer, GuestSerializer,
                          NotificationSerializer, ScheduleSerializer, TaskSerializer, UserAdminSerializer,
                          VendorSerializer, VenueSerializer)
from .services import ai, budget, checklist, readiness, recommender, reports, weather
from .services.notify import notify


# ---------- helpers ----------
def accessible_events(user):
    return Event.objects.filter(Q(owner=user) | Q(collaborators__user=user)).distinct()


def can_write(user, event):
    return event.owner_id == user.id or Collaborator.objects.filter(event=event, user=user, role="editor").exists()


def guest_stats(event):
    gs = list(event.guests.all())
    return {"total": len(gs), **{k: sum(g.rsvp == k for g in gs) for k in ("yes", "no", "maybe", "pending")},
            "checked_in": sum(g.checked_in for g in gs)}


def event_context(event):
    return {"title": event.title, "type": event.event_type, "date": event.date, "city": event.city,
            "weather": weather.forecast_for(event.city, event.date, event.is_outdoor), "budget": budget.summary(event),
            "guests": guest_stats(event), "pending_tasks": [t.title for t in event.tasks.filter(done=False)]}


def auth_payload(user):
    token, _ = Token.objects.get_or_create(user=user)
    profile, _ = Profile.objects.get_or_create(user=user)
    return {"token": token.key, "username": user.username, "role": profile.role, "is_admin": user.is_staff}


# ---------- auth ----------
@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def register(request):
    d = request.data
    username, password = (d.get("username") or "").strip(), d.get("password") or ""
    if not username or len(password) < 6:
        return Response({"detail": "Username and a password of at least 6 characters are required."}, 400)
    if User.objects.filter(username=username).exists():
        return Response({"detail": "That username is already taken."}, 400)
    user = User.objects.create_user(username=username, email=d.get("email", ""), password=password)
    Profile.objects.create(user=user, role=d.get("role") if d.get("role") in ("user", "vendor") else "user")
    return Response(auth_payload(user), 201)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def login(request):
    user = authenticate(username=request.data.get("username"), password=request.data.get("password"))
    if not user:
        return Response({"detail": "Invalid username or password."}, 400)
    return Response(auth_payload(user))


@api_view(["GET"])
def me(request):
    return Response(auth_payload(request.user))


# ---------- events ----------
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer

    def get_queryset(self):
        return accessible_events(self.request.user).order_by("date")

    def perform_create(self, serializer):
        ev = serializer.save(owner=self.request.user)
        checklist.populate(ev)
        notify(self.request.user, f'Event "{ev.title}" created. We generated a checklist, schedule and budget split for you.',
               ev, "event")

    def update(self, request, *args, **kwargs):
        if not can_write(request.user, self.get_object()):
            raise PermissionDenied("You have view-only access to this event.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if self.get_object().owner_id != request.user.id:
            raise PermissionDenied("Only the owner can delete an event.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True)
    def weather(self, request, pk=None):
        ev = self.get_object()
        return Response(weather.forecast_for(ev.city, ev.date, ev.is_outdoor))

    @action(detail=True)
    def readiness(self, request, pk=None):
        return Response(readiness.compute(self.get_object()))

    @action(detail=True)
    def recommendations(self, request, pk=None):
        return Response(recommender.recommend(self.get_object(), request.user))

    @action(detail=True)
    def budget_summary(self, request, pk=None):
        return Response(budget.summary(self.get_object()))

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        ev = self.get_object()
        if not can_write(request.user, ev):
            raise PermissionDenied()
        what = request.data.get("what", "all")
        checklist.populate(ev, ("tasks", "schedule", "budget") if what == "all" else (what,))
        return Response({"ok": True})

    @action(detail=True, methods=["post"])
    def invitation(self, request, pk=None):
        ev = self.get_object()
        return Response({"text": ai.write_invitation(ev, request.data.get("tone", "formal"), request.data.get("lang", "en"))})

    @action(detail=True, methods=["post"])
    def send_invites(self, request, pk=None):
        ev = self.get_object()
        if not can_write(request.user, ev):
            raise PermissionDenied()
        text = request.data.get("message") or ai.write_invitation(ev)
        sent = 0
        for g in ev.guests.exclude(email=""):
            send_mail(f"You're invited: {ev.title}", f"Hi {g.name},\n\n{text}\n\nRSVP here: {settings.FRONTEND_URL}/rsvp/{g.token}",
                      settings.DEFAULT_FROM_EMAIL, [g.email], fail_silently=True)
            sent += 1
        return Response({"sent": sent})

    @action(detail=True, methods=["get", "post"])
    def collaborators(self, request, pk=None):
        ev = self.get_object()
        if request.method == "POST":
            if ev.owner_id != request.user.id:
                raise PermissionDenied("Only the owner can add collaborators.")
            ident = (request.data.get("username") or "").strip()
            user = User.objects.filter(Q(username=ident) | Q(email=ident)).first()
            if not user or user.id == ev.owner_id:
                return Response({"detail": "No other user found with that username or email."}, 400)
            Collaborator.objects.update_or_create(event=ev, user=user, defaults={"role": request.data.get("role", "editor")})
            notify(user, f'{request.user.username} added you to the event "{ev.title}".', ev, "team")
        data = [{"id": ev.owner_id, "username": ev.owner.username, "role": "owner"}] + [
            {"id": c.user_id, "username": c.user.username, "role": c.role} for c in ev.collaborators.select_related("user")]
        return Response(data)

    @action(detail=True)
    def ics(self, request, pk=None):
        ev = self.get_object()
        res = HttpResponse(reports.build_ics(ev), content_type="text/calendar")
        res["Content-Disposition"] = f'attachment; filename="event-{ev.id}.ics"'
        return res

    @action(detail=True)
    def report(self, request, pk=None):
        ev = self.get_object()
        try:
            pdf = reports.build_pdf(ev)
        except ImportError:
            return Response({"detail": "PDF export needs 'reportlab' (pip install reportlab)."}, 501)
        res = HttpResponse(pdf, content_type="application/pdf")
        res["Content-Disposition"] = f'attachment; filename="event-{ev.id}-summary.pdf"'
        return res

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk=None):
        ev = self.get_object()
        try:
            guest = ev.guests.filter(token=uuid.UUID(str(request.data.get("token", "")).strip())).first()
        except ValueError:
            guest = None
        if not guest:
            return Response({"detail": "Invalid ticket for this event."}, 400)
        if guest.checked_in:
            return Response({"detail": f"{guest.name} was already checked in.", "guest": guest.name, "already": True}, 200)
        guest.checked_in, guest.checked_in_at = True, timezone.now()
        guest.save()
        return Response({"detail": f"Welcome, {guest.name}!", "guest": guest.name, **guest_stats(ev)})

    @action(detail=True)
    def feedback_summary(self, request, pk=None):
        ev = self.get_object()
        fb = list(ev.feedback.select_related("guest"))
        return Response({"count": len(fb), "average": round(sum(f.rating for f in fb) / len(fb), 1) if fb else None,
                         "sentiment": {s: sum(f.sentiment == s for f in fb) for s in ("positive", "neutral", "negative")},
                         "items": FeedbackSerializer(fb, many=True).data, "guests": guest_stats(ev)})


class ChildViewSet(viewsets.ModelViewSet):
    """Base for objects that belong to an event (guests, tasks, expenses, schedule)."""
    model = None

    def get_queryset(self):
        qs = self.model.objects.filter(event__in=accessible_events(self.request.user))
        ev = self.request.query_params.get("event")
        return qs.filter(event_id=ev) if ev else qs

    def perform_create(self, serializer):
        if not can_write(self.request.user, serializer.validated_data["event"]):
            raise PermissionDenied("You don't have edit access to this event.")
        serializer.save()

    def perform_update(self, serializer):
        if not can_write(self.request.user, serializer.instance.event):
            raise PermissionDenied("You don't have edit access to this event.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_write(self.request.user, instance.event):
            raise PermissionDenied("You don't have edit access to this event.")
        instance.delete()


class GuestViewSet(ChildViewSet):
    model, serializer_class = Guest, GuestSerializer


class TaskViewSet(ChildViewSet):
    model, serializer_class = Task, TaskSerializer


class ScheduleViewSet(ChildViewSet):
    model, serializer_class = ScheduleItem, ScheduleSerializer


class ExpenseViewSet(ChildViewSet):
    model, serializer_class = Expense, ExpenseSerializer


# ---------- catalogue ----------
class VenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset, serializer_class = Venue.objects.all(), VenueSerializer


class VendorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or getattr(getattr(request.user, "profile", None), "role", "") == "vendor"

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff or obj.owner_id == request.user.id


class VendorViewSet(viewsets.ModelViewSet):
    queryset, serializer_class, permission_classes = Vendor.objects.all(), VendorSerializer, [VendorPermission]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@api_view(["POST"])
def rate(request):
    kind, oid, score = request.data.get("kind"), request.data.get("object_id"), int(request.data.get("score", 0))
    if kind not in ("venue", "vendor") or not 1 <= score <= 5:
        return Response({"detail": "Invalid rating."}, 400)
    Rating.objects.update_or_create(user=request.user, kind=kind, object_id=oid, defaults={"score": score})
    return Response({"ok": True})


# ---------- notifications ----------
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"ok": True})


# ---------- chat-to-event ----------
@api_view(["POST"])
def chat(request):
    message, event_id = (request.data.get("message") or "").strip(), request.data.get("event_id")
    if not message:
        return Response({"detail": "Say something first."}, 400)
    if event_id:
        ev = accessible_events(request.user).filter(pk=event_id).first()
        if not ev:
            return Response({"detail": "Event not found."}, 404)
        return Response({"reply": ai.answer(ev, message, event_context(ev))})
    parsed = ai.parse_event_text(message)
    try:
        day = date.fromisoformat(parsed.get("date") or "")
    except ValueError:
        day = None
    missing = [k for k, v in (("a date", day), ("a city", parsed.get("city"))) if not v]
    if missing:
        return Response({"reply": "I understood: " + f"{parsed.get('event_type')}, {parsed.get('guest_count')} guests. "
                         f"Please also tell me {' and '.join(missing)} (e.g. 'on 25 Dec in Pune').", "event": None})
    if day < date.today():
        return Response({"reply": "That date is in the past. Please give a future date.", "event": None})
    ev = Event.objects.create(
        owner=request.user, title=parsed.get("title") or "My Event", event_type=parsed.get("event_type") or "other", date=day,
        city=parsed["city"], guest_count=int(parsed.get("guest_count") or 50), budget=parsed.get("budget") or 0,
        is_outdoor=bool(parsed.get("is_outdoor")), theme=parsed.get("theme") or "")
    checklist.populate(ev)
    notify(request.user, f'Event "{ev.title}" created from chat.', ev, "event", email=False)
    return Response({"reply": f'Done! I created "{ev.title}" on {ev.date:%d %b %Y} in {ev.city} for {ev.guest_count} guests with a budget of '
                              f'₹{float(ev.budget):,.0f}. A checklist, schedule and budget split are ready.', "event": EventSerializer(ev, context={"request": request}).data})


# ---------- public RSVP / feedback ----------
def _guest(token):
    return Guest.objects.select_related("event").filter(token=token).first()


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def rsvp(request, token):
    g = _guest(token)
    if not g:
        return Response({"detail": "Invalid RSVP link."}, 404)
    if request.method == "POST":
        choice = request.data.get("rsvp")
        if choice not in ("yes", "no", "maybe"):
            return Response({"detail": "Choose yes, no or maybe."}, 400)
        g.rsvp = choice
        g.save()
        notify(g.event.owner, f"{g.name} replied '{choice}' for {g.event.title}.", g.event, "rsvp", email=False)
    e = g.event
    return Response({"guest": g.name, "rsvp": g.rsvp, "token": str(g.token), "event": {
        "title": e.title, "date": e.date, "time": e.start_time.strftime("%H:%M"), "city": e.city,
        "venue": e.venue_name or (e.venue.name if e.venue else ""), "theme": e.theme, "past": e.date < date.today()},
        "feedback_given": Feedback.objects.filter(guest=g).exists()})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def feedback(request, token):
    g = _guest(token)
    if not g:
        return Response({"detail": "Invalid link."}, 404)
    comment = request.data.get("comment", "")
    Feedback.objects.update_or_create(guest=g, defaults={"event": g.event, "comment": comment,
                                                         "rating": max(1, min(5, int(request.data.get("rating", 5)))),
                                                         "sentiment": ai.sentiment(comment)})
    return Response({"ok": True})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def qr(request, token):
    if not _guest(token):
        return Response({"detail": "Invalid ticket."}, 404)
    try:
        return HttpResponse(reports.qr_png(str(token)), content_type="image/png")
    except ImportError:
        return Response({"detail": "QR codes need 'qrcode[pil]'."}, 501)


# ---------- admin ----------
@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def analytics(request):
    gs = Guest.objects
    return Response({
        "users": User.objects.count(), "events": Event.objects.count(), "guests": gs.count(),
        "upcoming": Event.objects.filter(date__gte=date.today()).count(),
        "by_type": list(Event.objects.values("event_type").annotate(n=Count("id")).order_by("-n")),
        "by_month": [{"month": f"{d:%b %Y}", "n": Event.objects.filter(created_at__year=d.year, created_at__month=d.month).count()}
                     for d in [(date.today().replace(day=1) - timedelta(days=30 * i)) for i in range(5, -1, -1)]],
        "rsvp": {k: gs.filter(rsvp=k).count() for k in ("yes", "no", "maybe", "pending")},
        "top_vendors": list(Vendor.objects.order_by("-rating").values("name", "category", "rating")[:5]),
        "avg_feedback": Feedback.objects.aggregate(a=Avg("rating"))["a"],
    })


class UserAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
