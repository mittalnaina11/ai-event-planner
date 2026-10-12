

import { useEffect, useState } from "react";

import { Link, useNavigate } from "react-router-dom";

import { api, inr, TYPES } from "../api";



const blank = {

  title: "",

  event_type: "birthday",

  date: "",

  city: "",

  guest_count: 50,

  budget: 50000,

  is_outdoor: false,

  theme: "",

};



const palettes = [

  { bg: "#E8EBFF", color: "#4F46E5", label: "Upcoming" },

  { bg: "#DDF5ED", color: "#128568", label: "Planning" },

  { bg: "#FFF0D8", color: "#B97716", label: "Celebration" },

  { bg: "#F0E8FF", color: "#8054CC", label: "Special event" },

];



export default function Dashboard() {

  const nav = useNavigate();

  const [events, setEvents] = useState([]);

  const [form, setForm] = useState(blank);

  const [err, setErr] = useState("");

  const [chat, setChat] = useState("");

  const [reply, setReply] = useState("");

  const [busy, setBusy] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(null);









  const load = () =>

    api("/events/")

      .then(setEvents)

      .catch((e) => setErr(e.message));



  useEffect(() => {

    load();

  }, []);



  const set = (key) => (e) =>

    setForm({

      ...form,

      [key]:

        e.target.type === "checkbox"

          ? e.target.checked

          : e.target.value,

    });



  const create = async (e) => {

    e.preventDefault();

    setErr("");



    try {

      const ev = await api("/events/", {

        method: "POST",

        body: form,

      });

      nav(`/events/${ev.id}`);

    } catch (x) {

      setErr(x.message);

    }

  };



  const ask = async (e) => {

    e.preventDefault();

    setBusy(true);

    setErr("");



    try {

      const r = await api("/chat/", {

        method: "POST",

        body: { message: chat },

      });



      setReply(r.reply);



      if (r.event) {

        nav(`/events/${r.event.id}`);

      }

    } catch (x) {

      setReply(x.message);

    }



    setBusy(false);

  };



  const days = (date) =>

    Math.ceil(

      (new Date(date) - new Date(new Date().toDateString())) /

        864e5

    );

  const monthName = calendarMonth.toLocaleDateString("en-IN", {
  
    month: "long",
  
    year: "numeric",
  
  });
  
  
  
  const firstDay = new Date(
  
    calendarMonth.getFullYear(),
  
    calendarMonth.getMonth(),
  
    1
  
  ).getDay();
  
  
  
  const daysInMonth = new Date(
  
    calendarMonth.getFullYear(),
  
    calendarMonth.getMonth() + 1,
  
    0
  
  ).getDate();
  
  
  
  const calendarCells = [
  
    ...Array(firstDay).fill(null),
  
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  
  ];
  
  
  
  const eventDates = events.map((ev) => {
  
    const d = new Date(`${ev.date}T00:00:00`);
  
    return {
  
      ...ev,
  
      calendarDate: d,
  
      day: d.getDate(),
  
      month: d.getMonth(),
  
      year: d.getFullYear(),
  
    };
  
  });
  
  
  
  const monthEvents = eventDates
  
    .filter(
  
      (ev) =>
  
        ev.month === calendarMonth.getMonth() &&
  
        ev.year === calendarMonth.getFullYear()
  
    )
  
    .sort((a, b) => a.day - b.day);
  
  
  
  const upcomingEvents = eventDates
  
    .filter((ev) => days(ev.date) >= 0)
  
    .sort((a, b) => a.calendarDate - b.calendarDate)
  
    .slice(0, 4);

const upcoming = events.filter((ev) => days(ev.date) >= 0);

  const guestTotal = events.reduce(

    (sum, ev) => sum + Number(ev.guest_count || 0),

    0

  );

  const budgetTotal = events.reduce(

    (sum, ev) => sum + Number(ev.budget || 0),

    0

  );



  return (

    <div className="dashboard">

      <div className="dashboard-main">

      {/* Welcome banner */}

      <section className="dashboard-hero">

        <div className="hero-content">

          <span className="eyebrow">✦ YOUR EVENT COMMAND CENTER</span>



          <h1>

            Turn your ideas

            <br />

            into unforgettable events.

          </h1>



          <p>

            Plan smarter with AI, discover amazing venues, and

            bring every little detail together.

          </p>



          <div className="hero-actions">

            <button

              className="btn hero-primary"

              onClick={() =>

                document

                  .getElementById("new-event")

                  ?.scrollIntoView({ behavior: "smooth" })

              }

            >

              ＋ Create your event

            </button>



            <button

              className="btn hero-secondary"

              onClick={() => nav("/")}

            >

              ✨ Explore planner

            </button>

          </div>



          <div className="hero-footnote">

            <span>✦ Smart planning</span>

            <span>✦ Better celebrations</span>

            <span>✦ Less stress</span>

          </div>

        </div>



        <div className="hero-art" aria-hidden="true">

          <div className="hero-orbit orbit-one" />

          <div className="hero-orbit orbit-two" />

          <div className="hero-spark spark-one">✦</div>

          <div className="hero-spark spark-two">✧</div>



          <div className="hero-calendar">

            <div className="calendar-top">

              <span />

              <span />

            </div>

            <div className="calendar-symbol">✦</div>

            <div className="calendar-dots">

              <i />

              <i />

              <i />

              <i />

              <i />

              <i />

            </div>

          </div>



          <div className="floating-note note-top">

            <span>✧</span> Make it memorable

          </div>



          <div className="floating-note note-bottom">

            <span>✓</span> Every detail, organized

          </div>



          <div className="hero-confetti confetti-one">✳</div>

          <div className="hero-confetti confetti-two">✦</div>

          <div className="hero-confetti confetti-three">✳</div>

        </div>

      </section>



      {err && <div className="err">{err}</div>}



      {/* AI planning panel */}

      <section className="ai-planner-panel" id="ai-planner">
        <div className="ai-heading">

          <div className="ai-icon">✦</div>

          <div>

            <h2>Meet your AI event planner</h2>

            <p>Describe your dream event. Let AI help with the details.</p>

          </div>

        </div>



        <form className="ai-prompt-form" onSubmit={ask}>

          <input

            value={chat}

            onChange={(e) => setChat(e.target.value)}

            placeholder='Try "Outdoor birthday for 50 guests in Pune, ₹80,000..."'

            required

          />

          <button className="btn" disabled={busy}>

            {busy ? "Planning…" : "✦ Plan with AI →"}

          </button>

        </form>



        {reply && (

          <div className="ai-reply">

            <span>✦</span>

            <p>{reply}</p>

          </div>

        )}



        <div className="prompt-examples">

          <span>Need inspiration?</span>

          {["Birthday party", "College fest", "Outdoor celebration"].map(

            (example) => (

              <button

                type="button"

                key={example}

                onClick={() =>

                  setChat(

                    `${example} for 50 guests with venue suggestions`

                  )

                }

              >

                {example} ↗

              </button>

            )

          )}

        </div>

      </section>



      {/* Overview statistics */}

      <section className="dashboard-stats">

        <div className="dashboard-stat stat-indigo">

          <div className="stat-icon">▦</div>

          <div>

            <span>Upcoming events</span>

            <strong>{upcoming.length}</strong>

            <small>Ready for your next big moment</small>

          </div>

        </div>



        <div className="dashboard-stat stat-teal">

          <div className="stat-icon">♧</div>

          <div>

            <span>Total guests</span>

            <strong>{guestTotal.toLocaleString("en-IN")}</strong>

            <small>Across all your events</small>

          </div>

        </div>



        <div className="dashboard-stat stat-amber">

          <div className="stat-icon">₹</div>

          <div>

            <span>Planned budget</span>

            <strong>{inr(budgetTotal)}</strong>

            <small>Combined event budgets</small>

          </div>

        </div>



        <div className="dashboard-stat stat-purple">

          <div className="stat-icon">✧</div>

          <div>

            <span>Events created</span>

            <strong>{events.length}</strong>

            <small>Your celebrations, organized</small>

          </div>

        </div>

      </section>



      {/* Events list */}

      <section className="dashboard-section" id="events">
        <div className="section-heading">

          <div>

            <span className="section-kicker">YOUR PLANS</span>

            <h2>Upcoming events</h2>

            <p>Your celebrations, all in one place.</p>

          </div>



          <button

            className="btn sec"

            onClick={() =>

              document

                .getElementById("new-event")

                ?.scrollIntoView({ behavior: "smooth" })

            }

          >

            + New event

          </button>

        </div>



        {events.length === 0 ? (

          <div className="empty-events">

            <div className="empty-illustration">✦</div>

            <h3>Your next great event starts here</h3>

            <p>

              Create your first event and start turning your ideas

              into something special.

            </p>

            <button

              className="btn"

              onClick={() =>

                document

                  .getElementById("new-event")

                  ?.scrollIntoView({ behavior: "smooth" })

              }

            >

              Create your first event →

            </button>

          </div>

        ) : (

          <div className="dashboard-event-grid">

            {events.map((ev, index) => {

              const palette = palettes[index % palettes.length];

              const remaining = days(ev.date);



              return (

                <Link

                  to={`/events/${ev.id}`}

                  key={ev.id}

                  className="event-tile"

                  style={{ "--event-accent": palette.color }}

                >

                  <div

                    className="event-tile-banner"

                    style={{ background: palette.bg }}

                  >

                    <span className="event-type-chip">

                      {ev.event_type.replaceAll("_", " ")}

                    </span>

                    <span className="event-decoration">

                      {["✦", "✧", "✳", "❋"][index % 4]}

                    </span>

                  </div>



                  <div className="event-tile-body">

                    <h3>{ev.title}</h3>



                    <p className="event-location">

                      <span>⌖</span> {ev.city}

                    </p>



                    <div className="event-meta-row">

                      <span>▦ {new Date(ev.date).toLocaleDateString(

                        "en-IN",

                        {

                          day: "numeric",

                          month: "short",

                          year: "numeric",

                        }

                      )}</span>

                      <span>♧ {ev.guest_count} guests</span>

                    </div>



                    <div className="event-card-footer">

                      <strong>{inr(ev.budget)}</strong>

                      <span

                        className="event-countdown"

                        style={{

                          background: palette.bg,

                          color: palette.color,

                        }}

                      >

                        {remaining >= 0

                          ? remaining === 0

                            ? "Today!"

                            : `${remaining} days to go`

                          : "Completed"}

                      </span>

                    </div>



                    {ev.role !== "owner" && (

                      <span className="badge b-maybe">{ev.role}</span>

                    )}

                  </div>



                  <span className="event-open-arrow">↗</span>

                </Link>

              );

            })}

          </div>

        )}

      </section>



      {/* New event form */}

      <section className="create-event-section" id="new-event">

        <div className="create-event-heading">

          <div className="create-event-icon">＋</div>

          <div>

            <span className="section-kicker">LET'S GET STARTED</span>

            <h2>Create a new event</h2>

            <p>Give your event a name and we'll help you organize it.</p>

          </div>

        </div>



        <form onSubmit={create} className="event-form">

          <div className="form-section-label">

            <span className="form-step">01</span>

            Event details

          </div>



          <div className="event-form-grid">

            <div>

              <label>Event title</label>

              <input

                value={form.title}

                onChange={set("title")}

                placeholder="e.g. Birthday Celebration"

                required

              />

            </div>



            <div>

              <label>Event type</label>

              <select

                value={form.event_type}

                onChange={set("event_type")}

              >

                {TYPES.map(([value, label]) => (

                  <option key={value} value={value}>

                    {label}

                  </option>

                ))}

              </select>

            </div>



            <div>

              <label>Event date</label>

              <input

                type="date"

                value={form.date}

                onChange={set("date")}

                required

              />

            </div>



            <div>

              <label>City</label>

              <input

                value={form.city}

                onChange={set("city")}

                placeholder="Where is it happening?"

                required

              />

            </div>

          </div>



          <div className="form-section-label form-section-spaced">

            <span className="form-step step-teal">02</span>

            Guests and budget

          </div>



          <div className="event-form-grid">

            <div>

              <label>Number of guests</label>

              <input

                type="number"

                min="1"

                value={form.guest_count}

                onChange={set("guest_count")}

              />

            </div>



            <div>

              <label>Budget (₹)</label>

              <input

                type="number"

                min="0"

                value={form.budget}

                onChange={set("budget")}

              />

            </div>



            <div>

              <label>Theme (optional)</label>

              <input

                value={form.theme}

                onChange={set("theme")}

                placeholder="e.g. Garden, Minimal"

              />

            </div>



            <label className="outdoor-option">

              <input

                type="checkbox"

                checked={form.is_outdoor}

                onChange={set("is_outdoor")}

              />

              <span>

                <strong>Outdoor event</strong>

                <small>Garden, lawn, or open-air venue</small>

              </span>

            </label>

          </div>



          <div className="create-event-footer">

            <p>✦ You can manage all the details after creating your event.</p>

            <button className="btn create-submit">

              Create event →

            </button>

          </div>

        </form>



      </section>

      </div>



      <aside className="dashboard-rail" id="calendar">

        <section className="calendar-card">

          <div className="rail-heading">

            <div>

              <span className="section-kicker">YOUR SCHEDULE</span>

              <h2>Calendar</h2>

            </div>

            <span className="rail-calendar-icon">▦</span>

          </div>



          <div className="calendar-month-nav">

            <button

              type="button"

              aria-label="Previous month"

              onClick={() =>

                setCalendarMonth(

                  new Date(

                    calendarMonth.getFullYear(),

                    calendarMonth.getMonth() - 1,

                    1

                  )

                )

              }

            >

              ‹

            </button>



            <strong>{monthName}</strong>



            <button

              type="button"

              aria-label="Next month"

              onClick={() =>

                setCalendarMonth(

                  new Date(

                    calendarMonth.getFullYear(),

                    calendarMonth.getMonth() + 1,

                    1

                  )

                )

              }

            >

              ›

            </button>

          </div>



          <div className="calendar-grid calendar-weekdays">

            {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => (

              <span key={day}>{day}</span>

            ))}

          </div>



          <div className="calendar-grid calendar-dates">

            {calendarCells.map((day, index) => {

              const hasEvent =

                day !== null &&

                monthEvents.some((ev) => ev.day === day);



              const isToday =

                day !== null &&

                day === new Date().getDate() &&

                calendarMonth.getMonth() === new Date().getMonth() &&

                calendarMonth.getFullYear() === new Date().getFullYear();



              return (

                <button
                  type="button"
                  key={`${calendarMonth.getFullYear()}-${calendarMonth.getMonth()}-${index}`}
                  className={[
                    "calendar-day",
                    selectedDate === day ? "selected" : "",
                    isToday ? "today" : "",
                    hasEvent ? "has-event" : "",
                  ].filter(Boolean).join(" ")}
                  disabled={day === null}
                  onClick={() => setSelectedDate(day)}
                >
                  {day}
                  {hasEvent && <span className="calendar-event-dot" />}
                </button>
            

              );

            })}

          </div>



          <div className="calendar-legend">

            <span className="calendar-event-dot" />

            Event scheduled

          </div>
          <div className="selected-date-events">
            <h3>
              {selectedDate
                ? `Events on ${new Date(
                    calendarMonth.getFullYear(),
                    calendarMonth.getMonth(),
                    selectedDate
                  ).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                  })}`
                : "Select a date"}
            </h3>

            {selectedDate &&
              monthEvents.filter((ev) => ev.day === selectedDate).length === 0 && (
                <p className="muted">No events scheduled for this date.</p>
              )}

            {selectedDate &&
              monthEvents
                .filter((ev) => ev.day === selectedDate)
                .map((ev) => (
                  <Link
                    to={`/events/${ev.id}`}
                    key={ev.id}
                    className="calendar-event-item"
                  >
                    <span className="calendar-event-info">
                      <strong>{ev.title}</strong>
                      <small>{ev.city || "Location not set"}</small>
                    </span>
                    <span className="calendar-event-arrow">↗</span>
                  </Link>
                ))}
          </div>



          <div className="calendar-events">

            <h3>This month</h3>



            {monthEvents.length === 0 ? (

              <p className="muted">No events this month.</p>

            ) : (

              monthEvents.slice(0, 4).map((ev) => (

                <Link

                  to={`/events/${ev.id}`}

                  className="calendar-event-item"

                  key={ev.id}

                >

                  <span className="calendar-event-date">

                    {String(ev.day).padStart(2, "0")}

                  </span>

                  <span className="calendar-event-info">

                    <strong>{ev.title}</strong>

                    <small>{ev.city || "Location not set"}</small>

                  </span>

                  <span className="calendar-event-arrow">↗</span>

                </Link>

              ))

            )}

          </div>

        </section>



        <section className="upcoming-card">

          <div className="rail-heading">

            <div>

              <span className="section-kicker">DON'T MISS OUT</span>

              <h2>Coming up</h2>

            </div>

            <span className="upcoming-icon">✦</span>

          </div>



          {upcomingEvents.length === 0 ? (

            <p className="muted">

              No upcoming events yet. Create one to get started!

            </p>

          ) : (

            upcomingEvents.map((ev) => (

              <Link

                to={`/events/${ev.id}`}

                className="upcoming-event-item"

                key={ev.id}

              >

                <span className="upcoming-event-icon">✦</span>

                <span className="upcoming-event-info">

                  <strong>{ev.title}</strong>

                  <small>

                    {ev.calendarDate.toLocaleDateString("en-IN", {

                      day: "numeric",

                      month: "short",

                      year: "numeric",

                    })}

                  </small>

                </span>

                <span className="upcoming-event-arrow">›</span>

              </Link>

            ))

          )}



          <button

            className="btn upcoming-create"

            type="button"

            onClick={() =>

              document

                .getElementById("new-event")

                ?.scrollIntoView({ behavior: "smooth" })

            }

          >

            + Create event

          </button>

        </section>

      </aside>

    </div>

  );

}
