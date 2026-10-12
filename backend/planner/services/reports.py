"""ICS calendar export, PDF summary report and QR codes."""
import io
from datetime import datetime, timedelta

from . import budget


def build_ics(event):
    start = datetime.combine(event.date, event.start_time)
    end = start + timedelta(hours=4)
    fmt = "%Y%m%dT%H%M%S"
    esc = lambda s: (s or "").replace("\n", "\\n").replace(",", "\\,")
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AI Event Planner//EN", "BEGIN:VEVENT",
                        f"UID:event-{event.id}@eventplanner", f"DTSTAMP:{datetime.utcnow().strftime(fmt)}Z",
                        f"DTSTART:{start.strftime(fmt)}", f"DTEND:{end.strftime(fmt)}", f"SUMMARY:{esc(event.title)}",
                        f"LOCATION:{esc(event.venue_name or event.city)}", f"DESCRIPTION:{esc(event.description)}",
                        "END:VEVENT", "END:VCALENDAR"])


def build_pdf(event):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = [h - 50]

    def line(text, size=10, bold=False, gap=15):
        if y[0] < 60:
            c.showPage()
            y[0] = h - 50
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(50, y[0], str(text)[:100])
        y[0] -= gap

    line(event.title, 20, True, 28)
    line(f"{event.get_event_type_display()}  |  {event.date:%d %b %Y}, {event.start_time:%I:%M %p}  |  {event.venue_name or event.city}")
    line(f"Expected guests: {event.guest_count}", gap=25)
    b = budget.summary(event)
    line("Budget", 13, True)
    line(f"Total budget: Rs {b['budget']:,.0f}   Projected: Rs {b['projected']:,.0f}   Remaining: Rs {b['remaining']:,.0f}", gap=18)
    for e in event.expenses.all():
        line(f"  {e.category}: estimated Rs {e.estimated:,.0f}, actual Rs {e.actual:,.0f}")
    y[0] -= 10
    guests = list(event.guests.all())
    line("Guests", 13, True)
    line(f"Total {len(guests)}  |  Yes {sum(g.rsvp == 'yes' for g in guests)}  |  No {sum(g.rsvp == 'no' for g in guests)}  |  "
         f"Maybe {sum(g.rsvp == 'maybe' for g in guests)}  |  Checked in {sum(g.checked_in for g in guests)}", gap=22)
    line("Schedule", 13, True)
    for s in event.schedule.all():
        line(f"  {s.start_time:%I:%M %p}  {s.title} ({s.duration_min} min)")
    y[0] -= 10
    line("Tasks", 13, True)
    for t in event.tasks.all():
        line(f"  [{'x' if t.done else ' '}] {t.title}  (due {t.due_date})")
    c.save()
    return buf.getvalue()


def qr_png(text):
    import qrcode
    buf = io.BytesIO()
    qrcode.make(text).save(buf, format="PNG")
    return buf.getvalue()
