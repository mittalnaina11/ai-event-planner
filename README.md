# AI-Based Event Planning System

Django REST + React project for the NMIMS Shirpur mini project (Naina Mittal, Sneha Bhavsar).
It plans an event end to end and adapts to real-world conditions: **weather, budget and guest responses**.

## Features
| # | Feature | Where |
|---|---|---|
| 1 | Auth with roles (User, Vendor, Admin) and co-organizer access (Editor/Viewer) | `views.py`, Team tab |
| 2 | Event templates (wedding, birthday, corporate, college fest, conference, party) | `services/checklist.py` |
| 3 | Guest management: groups, diet, CSV import, email invitations | Guests tab |
| 4 | Notifications: in-app + email; scheduled reminders | `send_reminders` command |
| 5 | Admin panel: users, analytics, Django admin for data | `/admin` page, `/admin/` |
| 6 | **AI chat planner** (chat-to-event + event Q&A) | Dashboard, Assistant tab |
| 7 | Venue/vendor recommender (TF-IDF + rating feedback loop) | Discover tab |
| 8 | Smart budget allocator and optimizer | Budget tab |
| 9 | Auto checklist and schedule with clash detection | Plan tab |
| 10 | AI invitation writer (English/Hindi; formal/fun/warm) | Invitation tab |
| 11 | **Weather-aware planning**: forecast, risk, Plan B, daily weather alerts | Overview tab |
| 12 | Map link (OpenStreetMap) | Overview tab |
| 13 | RSVP link + QR ticket + check-in | Guests tab, `/rsvp/<token>` |
| 14 | Post-event feedback with sentiment analysis | RSVP page, Feedback tab |
| 15 | Task assignment to co-organizers | Plan tab |
| 16 | **Event Readiness Score** (0-100) | Overview tab |
| 17 | PDF summary, admin analytics | Overview, Admin |
| 18 | Calendar export (.ics) | Overview tab |

## Run it (Windows / Linux / macOS)

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations planner
python manage.py migrate
python manage.py seed_data          # demo venues, vendors, accounts
python manage.py runserver          # http://127.0.0.1:8000
```
Demo logins: `admin / admin12345`, `demo / demo12345`, `vendor1 / vendor12345`.

### 2. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```
Vite proxies `/api` to Django, so no extra configuration is needed.

### 3. Optional
| What | How |
|---|---|
| Real LLM for chat and invitations | `set GEMINI_API_KEY=...` (free key from Google AI Studio) before `runserver`. Without it, built-in rule-based AI is used. |
| Real emails | set `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (otherwise emails print in the Django console) |
| PostgreSQL / MySQL | set `DB_ENGINE=postgres` (or `mysql`), `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` |
| Daily reminders and weather alerts | schedule `python manage.py send_reminders` (cron or Windows Task Scheduler). Run it by hand for the demo. |
| Production URL for RSVP links | set `FRONTEND_URL=https://your-site` |

## Demo script (5 minutes)
1. Log in as `demo`. Type in the chat box: *"Birthday party for 60 guests in Pune, ₹80,000, next Saturday, outdoor garden"*.
2. **Overview**: show the Readiness Score, the weather card and Plan B (forecast works for dates within 16 days).
3. **Budget**: set a big "actual" cost, see the warning and the optimizer's suggestions.
4. **Discover**: rate a venue, reload, and watch the ranking change; select a venue.
5. **Guests**: add guests, copy an RSVP link, open it in a private window, reply "yes", and show the QR. Paste the ticket code into check-in.
6. **Invitation**: generate in Hindi. **Assistant**: ask "Will it rain?".
7. Log in as `admin` and show the analytics dashboard.

## API summary (all under `/api/`, token auth: `Authorization: Token <key>`)
`auth/register|login|me` · `events/` (+ `weather`, `readiness`, `recommendations`, `budget_summary`, `regenerate`, `invitation`, `send_invites`, `collaborators`, `ics`, `report`, `checkin`, `feedback_summary`) · `guests/ tasks/ schedule/ expenses/` (filter `?event=ID`) · `venues/ vendors/` · `ratings/` · `chat/` · `notifications/` · public: `rsvp/<token>/`, `rsvp/<token>/feedback/`, `qr/<token>/` · admin: `admin/analytics/`, `admin/users/`

## Project structure
```
backend/config/            Django settings and root URLs
backend/planner/models.py  Event, Guest, Task, Expense, Venue, Vendor, Rating, Feedback, Notification ...
backend/planner/views.py   REST endpoints
backend/planner/services/  weather, budget, checklist, recommender, ai, readiness, reports, notify
backend/planner/management/commands/   seed_data, send_reminders
frontend/src/pages/        Auth, Dashboard, EventDetail (9 tabs), Rsvp, Admin
```

## Known limitations (list these honestly in your report)
- Camera-based QR scanning is not built in; check-in takes the ticket code (any phone QR scanner can read the code).
- Weather forecasts exist only within 16 days of the event (Open-Meteo limit). Beyond that, the app says so and re-checks later.
- Google login, WhatsApp/SMS and vendor booking requests are not implemented (future scope).
- Venue/vendor data is demo data; replace it with real data through the Django admin (`/admin/`).
- The recommender is content-based and rule-blended, trained on a small catalogue; quality grows as users rate.
