"""python manage.py seed_data  - loads demo venues/vendors and demo accounts."""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from planner.models import Profile, Vendor, Venue

VENUES = [
    ("Royal Lawns", "Pune", 600, 180000, "wedding garden lawn reception outdoor", 4.6, True, 18.52, 73.86),
    ("Grand Orchid Banquet", "Pune", 400, 120000, "wedding banquet ac hall reception indoor", 4.4, False, 18.56, 73.91),
    ("Skyline Terrace", "Pune", 120, 45000, "birthday party terrace rooftop dj", 4.3, True, 18.53, 73.84),
    ("Tech Park Convention Hall", "Pune", 500, 90000, "conference corporate seminar projector ac", 4.2, False, 18.59, 73.74),
    ("Taj Heritage Hall", "Mumbai", 800, 400000, "wedding luxury banquet ac hall", 4.8, False, 18.92, 72.83),
    ("Marine Drive Lounge", "Mumbai", 150, 95000, "party birthday lounge sea view", 4.5, False, 18.94, 72.82),
    ("Beachside Gardens", "Goa", 300, 220000, "wedding beach outdoor party", 4.7, True, 15.49, 73.82),
    ("Lotus Convention Centre", "Delhi", 700, 250000, "wedding conference banquet ac hall", 4.5, False, 28.61, 77.21),
    ("Green Meadows Farm", "Delhi", 250, 110000, "birthday party farmhouse garden outdoor", 4.3, True, 28.52, 77.1),
    ("Silicon Hub Auditorium", "Bangalore", 450, 100000, "conference corporate college fest auditorium stage", 4.4, False, 12.97, 77.59),
    ("Palace Grounds Annexe", "Bangalore", 900, 300000, "wedding lawn reception outdoor", 4.6, True, 13.0, 77.58),
    ("Marina Banquet", "Chennai", 350, 130000, "wedding banquet ac hall reception", 4.4, False, 13.05, 80.28),
    ("Campus Open Air Theatre", "Shirpur", 1000, 25000, "college fest stage outdoor cultural", 4.1, True, 21.35, 74.88),
    ("Shirpur Community Hall", "Shirpur", 300, 30000, "wedding birthday party hall indoor", 4.0, False, 21.35, 74.88),
]
VENDORS = [
    ("Spice Route Caterers", "Catering", "Pune", 35000, "wedding birthday party veg non-veg jain buffet", 4.6),
    ("Annapurna Catering", "Catering", "Mumbai", 60000, "wedding corporate veg vegan buffet", 4.5),
    ("Delhi Darbar Caterers", "Catering", "Delhi", 50000, "wedding party north indian buffet", 4.4),
    ("Shirpur Food Court Services", "Catering", "Shirpur", 15000, "college fest party snacks", 4.0),
    ("Petal & Co Decor", "Decor", "Pune", 25000, "wedding floral theme stage decor", 4.5),
    ("Dream Decorators", "Decor", "Mumbai", 40000, "birthday party balloon theme decor", 4.3),
    ("Stagecraft Events", "AV & Tech", "Pune", 30000, "conference corporate stage led sound lighting college fest", 4.4),
    ("SoundWave AV", "AV & Tech", "Bangalore", 35000, "conference corporate college fest sound projector", 4.3),
    ("Lens Stories Photography", "Photography", "Pune", 30000, "wedding birthday candid cinematic", 4.7),
    ("Frame Perfect Studio", "Photography", "Mumbai", 45000, "wedding corporate candid drone", 4.5),
    ("DJ Pulse", "Entertainment", "Pune", 20000, "party birthday wedding dj dance music", 4.4),
    ("Rhythm Band Live", "Entertainment", "Delhi", 40000, "wedding party live band music", 4.5),
    ("Glow Makeovers", "Makeup", "Pune", 15000, "wedding bridal makeup", 4.4),
    ("Campus Beats", "Entertainment", "Shirpur", 10000, "college fest dj music dance", 4.1),
]


class Command(BaseCommand):
    def handle(self, *args, **opts):
        if not Venue.objects.exists():
            for n, c, cap, p, t, r, o, la, ln in VENUES:
                Venue.objects.create(name=n, city=c, capacity=cap, price=p, tags=t, rating=r, outdoor=o, lat=la, lng=ln)
            for n, cat, c, p, t, r in VENDORS:
                Vendor.objects.create(name=n, category=cat, city=c, price_from=p, tags=t, rating=r)
        for name, pw, staff, role in (("admin", "admin12345", True, "user"), ("demo", "demo12345", False, "user"),
                                      ("vendor1", "vendor12345", False, "vendor")):
            u, created = User.objects.get_or_create(username=name, defaults={"email": f"{name}@example.com", "is_staff": staff, "is_superuser": staff})
            if created:
                u.set_password(pw)
                u.save()
            Profile.objects.get_or_create(user=u, defaults={"role": role})
        self.stdout.write(self.style.SUCCESS("Seeded. Logins: admin/admin12345, demo/demo12345, vendor1/vendor12345"))
