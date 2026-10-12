from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("events", views.EventViewSet, basename="event")
router.register("guests", views.GuestViewSet, basename="guest")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("schedule", views.ScheduleViewSet, basename="schedule")
router.register("expenses", views.ExpenseViewSet, basename="expense")
router.register("venues", views.VenueViewSet, basename="venue")
router.register("vendors", views.VendorViewSet, basename="vendor")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("admin/users", views.UserAdminViewSet, basename="admin-user")

urlpatterns = [
    path("auth/register/", views.register), path("auth/login/", views.login), path("auth/me/", views.me),
    path("chat/", views.chat), path("ratings/", views.rate),
    path("rsvp/<uuid:token>/", views.rsvp), path("rsvp/<uuid:token>/feedback/", views.feedback),
    path("qr/<uuid:token>/", views.qr), path("admin/analytics/", views.analytics),
    path("", include(router.urls)),
]
