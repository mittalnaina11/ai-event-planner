import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, download, inr } from "../api";

const TABS = ["Overview", "Guests", "Budget", "Plan", "Discover", "Invitation", "Assistant", "Team", "Feedback"];

export default function EventDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [ev, setEv] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [err, setErr] = useState("");
  const reload = useCallback(() => api(`/events/${id}/`).then(setEv).catch((e) => setErr(e.message)), [id]);
  useEffect(() => { reload(); }, [reload]);
  if (err) return <div className="err">{err}</div>;
  if (!ev) return <p>Loading…</p>;
  const del = async () => { if (confirm("Delete this event permanently?")) { await api(`/events/${id}/`, { method: "DELETE" }); nav("/"); } };
  const P = { ev, reload };
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        <div><h1 style={{ marginBottom: 2 }}>{ev.title}</h1>
          <span className="muted">{ev.event_type.replace("_", " ")} · {new Date(ev.date).toDateString()} · {ev.city}{ev.venue_name && ` · ${ev.venue_name}`}{ev.is_outdoor && " · outdoor"}</span></div>
        {ev.role === "owner" && <button className="btn danger auto" onClick={del}>Delete</button>}
      </div>
      <div className="tabs">{TABS.map((t) => <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>{t}</button>)}</div>
      {tab === "Overview" && <Overview {...P} />}
      {tab === "Guests" && <Guests {...P} />}
      {tab === "Budget" && <Budget {...P} />}
      {tab === "Plan" && <Plan {...P} />}
      {tab === "Discover" && <Discover {...P} />}
      {tab === "Invitation" && <Invitation {...P} />}
      {tab === "Assistant" && <Assistant {...P} />}
      {tab === "Team" && <Team {...P} />}
      {tab === "Feedback" && <Feedback {...P} />}
    </>
  );
}

/* ---------------- Overview: readiness score + weather ---------------- */
function Overview({ ev }) {
  const [r, setR] = useState(null);
  const [msg, setMsg] = useState("");
  useEffect(() => { api(`/events/${ev.id}/readiness/`).then(setR).catch((e) => setMsg(e.message)); }, [ev.id]);
  if (!r) return <p>{msg || "Calculating readiness…"}</p>;
  const w = r.weather;
  const color = r.score >= 85 ? "#16a34a" : r.score >= 65 ? "#5b4bdb" : r.score >= 40 ? "#d97706" : "#dc2626";
  const lat = w.lat ?? ev.venue_detail?.lat, lon = w.lon ?? ev.venue_detail?.lng;
  const map = lat ? `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=14/${lat}/${lon}` : `https://www.openstreetmap.org/search?query=${encodeURIComponent(ev.venue_name || ev.city)}`;
  const tryDownload = (p, f) => download(p, f).catch((e) => setMsg(e.message));
  return (
    <>
      {msg && <div className="err">{msg}</div>}
      <div className="grid g2">
        <div className="card">
          <h2>Event Readiness Score</h2>
          <div className="gauge" style={{ background: `conic-gradient(${color} ${r.score * 3.6}deg, var(--line) 0)` }}>
            <div><span>{r.score}<small>{r.label}</small></span></div>
          </div>
          <div style={{ marginTop: 14 }}>
            {Object.entries(r.breakdown).map(([k, v]) => (
              <div key={k} style={{ marginBottom: 8 }}><div className="muted">{k}: {v.points}/{v.max}</div><div className="bar"><i style={{ width: `${(v.points / v.max) * 100}%` }} /></div></div>
            ))}
          </div>
          {r.fixes.length > 0 && <><h3>To improve your score</h3><ul>{r.fixes.map((f) => <li key={f}>{f}</li>)}</ul></>}
        </div>
        <div className="card">
          <h2>🌤️ Weather on event day</h2>
          {!w.available ? <p className="muted">{w.message}</p> : (<>
            <p style={{ fontSize: 18, margin: "4px 0" }}><b>{w.summary}</b> · {w.temp_min}–{w.temp_max}°C</p>
            <p className="muted">Rain chance {w.rain_chance}% · Wind {w.wind} km/h · Weather risk: <span className={`badge b-${w.risk}`}>{w.risk}</span></p>
            <ul>{w.tips.map((t) => <li key={t}>{t}</li>)}</ul>
            {w.plan_b.length > 0 && <div className="warn"><b>Plan B suggestions</b><ul style={{ margin: "6px 0 0" }}>{w.plan_b.map((t) => <li key={t}>{t}</li>)}</ul></div>}
          </>)}
          <p><a href={map} target="_blank" rel="noreferrer">📍 View location on map</a></p>
        </div>
      </div>
      <div className="card">
        <h2>Export</h2>
        <div className="row">
          <button className="btn sec auto" onClick={() => tryDownload(`/events/${ev.id}/ics/`, `event-${ev.id}.ics`)}>📅 Add to calendar (.ics)</button>
          <button className="btn sec auto" onClick={() => tryDownload(`/events/${ev.id}/report/`, `event-${ev.id}-summary.pdf`)}>📄 PDF summary</button>
        </div>
      </div>
    </>
  );
}

/* ---------------- Guests, RSVP, QR check-in ---------------- */
function Guests({ ev }) {
  const [gs, setGs] = useState([]);
  const [f, setF] = useState({ name: "", email: "", phone: "", group: "", diet: "" });
  const [csv, setCsv] = useState("");
  const [ticket, setTicket] = useState("");
  const [msg, setMsg] = useState(null);
  const load = () => api(`/guests/?event=${ev.id}`).then(setGs);
  useEffect(() => { load(); }, [ev.id]);
  const run = async (fn) => { try { setMsg(null); await fn(); await load(); } catch (e) { setMsg({ bad: e.message }); } };
  const add = (e) => { e.preventDefault(); run(async () => { await api("/guests/", { method: "POST", body: { ...f, event: ev.id } }); setF({ name: "", email: "", phone: "", group: "", diet: "" }); }); };
  const importCsv = () => run(async () => {
    for (const line of csv.split("\n").map((l) => l.trim()).filter(Boolean)) {
      const [name, email = "", phone = "", group = "", diet = ""] = line.split(",").map((x) => x.trim());
      if (name.toLowerCase() !== "name") await api("/guests/", { method: "POST", body: { name, email, phone, group, diet, event: ev.id } });
    }
    setCsv(""); setMsg({ ok: "Guests imported." });
  });
  const checkin = () => run(async () => { const r = await api(`/events/${ev.id}/checkin/`, { method: "POST", body: { token: ticket } }); setTicket(""); setMsg({ ok: r.detail }); });
  const sendAll = () => run(async () => { const r = await api(`/events/${ev.id}/send_invites/`, { method: "POST", body: {} }); setMsg({ ok: `Invitations sent to ${r.sent} guest(s) (check the Django console if SMTP isn't configured).` }); });
  const c = (k) => gs.filter((g) => g.rsvp === k).length;
  return (
    <>
      {msg?.bad && <div className="err">{msg.bad}</div>}{msg?.ok && <div className="okmsg">{msg.ok}</div>}
      <div className="grid g3">
        {[["Invited", gs.length], ["Yes", c("yes")], ["Maybe", c("maybe")], ["No", c("no")], ["Pending", c("pending")], ["Checked in", gs.filter((g) => g.checked_in).length]].map(([k, v]) =>
          <div className="card stat" key={k}><b>{v}</b><span className="muted">{k}</span></div>)}
      </div>
      <form className="card" onSubmit={add}>
        <h2>Add guest</h2>
        <div className="row">{["name", "email", "phone", "group", "diet"].map((k) => <div key={k}><label>{k === "diet" ? "diet (veg/vegan/jain…)" : k === "group" ? "group (family/VIP…)" : k}</label>
          <input value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} required={k === "name"} /></div>)}
          <button className="btn auto">Add</button></div>
      </form>
      <div className="card">
        <h2>Bulk import (CSV)</h2>
        <p className="muted">One guest per line: name, email, phone, group, diet</p>
        <textarea rows="3" value={csv} onChange={(e) => setCsv(e.target.value)} placeholder="Asha Rao, asha@example.com, 9999999999, family, veg" />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn sec auto" onClick={importCsv} disabled={!csv}>Import</button>
          <button className="btn auto" onClick={sendAll}>✉️ Email invitations to all</button>
        </div>
      </div>
      <div className="card">
        <h2>🎫 QR check-in</h2>
        <p className="muted">Guests who RSVP "yes" get a QR ticket. Paste the scanned ticket code here (any QR scanner app reads it) and press Check in.</p>
        <div className="row"><input value={ticket} onChange={(e) => setTicket(e.target.value)} placeholder="ticket code" /><button className="btn auto" onClick={checkin} disabled={!ticket}>Check in</button></div>
      </div>
      <div className="card" style={{ overflowX: "auto" }}>
        <h2>Guest list</h2>
        <table><thead><tr><th>Name</th><th>Group</th><th>Diet</th><th>RSVP</th><th>In</th><th>Links</th><th></th></tr></thead>
          <tbody>{gs.map((g) => (
            <tr key={g.id}><td>{g.name}<div className="muted">{g.email}</div></td><td>{g.group}</td><td>{g.diet}</td>
              <td><span className={`badge b-${g.rsvp}`}>{g.rsvp}</span></td><td>{g.checked_in ? "✅" : ""}</td>
              <td><button className="btn sm sec" onClick={() => navigator.clipboard.writeText(g.rsvp_url)}>Copy RSVP link</button>{" "}
                <a href={`/api/qr/${g.token}/`} target="_blank" rel="noreferrer">QR</a>{" "}<span className="muted" title="Ticket code">{g.token.slice(0, 8)}…</span>
                <button className="btn sm sec" style={{ marginLeft: 6 }} onClick={() => navigator.clipboard.writeText(g.token)}>Copy code</button></td>
              <td><button className="btn sm danger" onClick={() => run(() => api(`/guests/${g.id}/`, { method: "DELETE" }))}>✕</button></td></tr>))}
          </tbody></table>
      </div>
    </>
  );
}

/* ---------------- Budget ---------------- */
function Budget({ ev }) {
  const [s, setS] = useState(null);
  const [ex, setEx] = useState([]);
  const [n, setN] = useState({ category: "", estimated: "" });
  const load = async () => { setS(await api(`/events/${ev.id}/budget_summary/`)); setEx(await api(`/expenses/?event=${ev.id}`)); };
  useEffect(() => { load(); }, [ev.id]);
  if (!s) return <p>Loading…</p>;
  const save = (e, field, v) => api(`/expenses/${e.id}/`, { method: "PATCH", body: { [field]: v || 0 } }).then(load);
  const pct = Math.min(100, s.budget ? (s.projected / s.budget) * 100 : 0);
  return (
    <>
      {s.warning && <div className="warn">⚠️ {s.warning}</div>}
      <div className="grid g3">
        {[["Budget", inr(s.budget)], ["Projected", inr(s.projected)], ["Remaining", inr(s.remaining)], ["Per guest", inr(s.per_guest)]].map(([k, v]) => <div className="card stat" key={k}><b>{v}</b><span className="muted">{k}</span></div>)}
      </div>
      <div className="card"><div className="bar"><i style={{ width: `${pct}%`, background: s.warning ? "#dc2626" : undefined }} /></div>
        <h3 style={{ marginTop: 14 }}>💡 Smart suggestions</h3><ul>{s.tips.map((t) => <li key={t}>{t}</li>)}</ul></div>
      <div className="card" style={{ overflowX: "auto" }}>
        <div className="row"><h2 style={{ flex: 3 }}>Expenses</h2><button className="btn sec auto" onClick={() => api(`/events/${ev.id}/regenerate/`, { method: "POST", body: { what: "budget" } }).then(load)}>♻️ Re-split my budget</button></div>
        <table><thead><tr><th>Category</th><th>Estimated (₹)</th><th>Actual (₹)</th><th></th></tr></thead>
          <tbody>{ex.map((e) => (
            <tr key={e.id}><td>{e.category}</td>
              <td><input type="number" defaultValue={e.estimated} onBlur={(x) => save(e, "estimated", x.target.value)} /></td>
              <td><input type="number" defaultValue={e.actual} onBlur={(x) => save(e, "actual", x.target.value)} /></td>
              <td><button className="btn sm danger" onClick={() => api(`/expenses/${e.id}/`, { method: "DELETE" }).then(load)}>✕</button></td></tr>))}
          </tbody></table>
        <div className="row" style={{ marginTop: 12 }}>
          <input placeholder="New category" value={n.category} onChange={(e) => setN({ ...n, category: e.target.value })} />
          <input type="number" placeholder="Estimated ₹" value={n.estimated} onChange={(e) => setN({ ...n, estimated: e.target.value })} />
          <button className="btn auto" disabled={!n.category} onClick={() => api("/expenses/", { method: "POST", body: { ...n, estimated: n.estimated || 0, event: ev.id } }).then(() => { setN({ category: "", estimated: "" }); load(); })}>Add</button>
        </div>
      </div>
    </>
  );
}

/* ---------------- Tasks + schedule ---------------- */
function Plan({ ev }) {
  const [tasks, setTasks] = useState([]);
  const [sched, setSched] = useState([]);
  const [team, setTeam] = useState([]);
  const [t, setT] = useState({ title: "", due_date: "" });
  const [s, setS] = useState({ title: "", start_time: "", duration_min: 30 });
  const [err, setErr] = useState("");
  const load = async () => {
    setTasks(await api(`/tasks/?event=${ev.id}`)); setSched(await api(`/schedule/?event=${ev.id}`)); setTeam(await api(`/events/${ev.id}/collaborators/`));
  };
  useEffect(() => { load(); }, [ev.id]);
  const run = (p) => p.then(load).catch((e) => setErr(e.message));
  // detect overlapping schedule items
  const clash = new Set();
  const toMin = (x) => { const [h, m] = x.split(":"); return +h * 60 + +m; };
  sched.forEach((a, i) => sched.forEach((b, j) => { if (i < j && toMin(a.start_time) < toMin(b.start_time) + b.duration_min && toMin(b.start_time) < toMin(a.start_time) + a.duration_min) { clash.add(a.id); clash.add(b.id); } }));
  const done = tasks.filter((x) => x.done).length;
  return (
    <>
      {err && <div className="err">{err}</div>}
      <div className="grid g2">
        <div className="card">
          <div className="row"><h2 style={{ flex: 3 }}>✅ Checklist ({done}/{tasks.length})</h2>
            <button className="btn sec sm auto" onClick={() => run(api(`/events/${ev.id}/regenerate/`, { method: "POST", body: { what: "tasks" } }))}>♻️ Regenerate</button></div>
          <div className="bar" style={{ margin: "8px 0" }}><i style={{ width: `${tasks.length ? (done / tasks.length) * 100 : 0}%` }} /></div>
          {tasks.map((x) => (
            <div key={x.id} className="row" style={{ alignItems: "center", margin: "6px 0" }}>
              <label className="auto" style={{ margin: 0 }}><input type="checkbox" style={{ width: 18 }} checked={x.done} onChange={() => run(api(`/tasks/${x.id}/`, { method: "PATCH", body: { done: !x.done } }))} /></label>
              <span style={{ flex: 3, textDecoration: x.done ? "line-through" : "none" }}>{x.title}<div className="muted">due {x.due_date || "–"}</div></span>
              <select style={{ flex: 1 }} value={x.assignee || ""} onChange={(e) => run(api(`/tasks/${x.id}/`, { method: "PATCH", body: { assignee: e.target.value || null } }))}>
                <option value="">Unassigned</option>{team.map((m) => <option key={m.id} value={m.id}>{m.username}</option>)}</select>
              <button className="btn sm danger auto" onClick={() => run(api(`/tasks/${x.id}/`, { method: "DELETE" }))}>✕</button>
            </div>))}
          <div className="row" style={{ marginTop: 10 }}>
            <input placeholder="New task" value={t.title} onChange={(e) => setT({ ...t, title: e.target.value })} />
            <input type="date" value={t.due_date} onChange={(e) => setT({ ...t, due_date: e.target.value })} />
            <button className="btn auto" disabled={!t.title} onClick={() => run(api("/tasks/", { method: "POST", body: { ...t, due_date: t.due_date || null, event: ev.id } }).then(() => setT({ title: "", due_date: "" })))}>Add</button>
          </div>
        </div>
        <div className="card">
          <div className="row"><h2 style={{ flex: 3 }}>🕒 Event-day schedule</h2>
            <button className="btn sec sm auto" onClick={() => run(api(`/events/${ev.id}/regenerate/`, { method: "POST", body: { what: "schedule" } }))}>♻️ Regenerate</button></div>
          {clash.size > 0 && <div className="warn">⚠️ Some items overlap. Adjust the highlighted times.</div>}
          {sched.map((x) => (
            <div key={x.id} className="row" style={{ alignItems: "center", margin: "6px 0", background: clash.has(x.id) ? "#fef3c7" : "transparent", padding: 4, borderRadius: 8 }}>
              <input type="time" style={{ flex: 1 }} defaultValue={x.start_time.slice(0, 5)} onBlur={(e) => e.target.value && run(api(`/schedule/${x.id}/`, { method: "PATCH", body: { start_time: e.target.value } }))} />
              <span style={{ flex: 3 }}>{x.title}</span>
              <input type="number" style={{ flex: 1 }} defaultValue={x.duration_min} title="minutes" onBlur={(e) => run(api(`/schedule/${x.id}/`, { method: "PATCH", body: { duration_min: e.target.value } }))} />
              <button className="btn sm danger auto" onClick={() => run(api(`/schedule/${x.id}/`, { method: "DELETE" }))}>✕</button>
            </div>))}
          <div className="row" style={{ marginTop: 10 }}>
            <input type="time" value={s.start_time} onChange={(e) => setS({ ...s, start_time: e.target.value })} />
            <input placeholder="Activity" value={s.title} onChange={(e) => setS({ ...s, title: e.target.value })} />
            <button className="btn auto" disabled={!s.title || !s.start_time} onClick={() => run(api("/schedule/", { method: "POST", body: { ...s, event: ev.id } }).then(() => setS({ title: "", start_time: "", duration_min: 30 })))}>Add</button>
          </div>
        </div>
      </div>
    </>
  );
}

/* ---------------- Venue & vendor recommendations ---------------- */
function Stars({ value, onRate }) {
  return <span>{[1, 2, 3, 4, 5].map((n) => <span key={n} className={`star ${n <= (value || 0) ? "on" : ""}`} onClick={() => onRate(n)}>★</span>)}</span>;
}

function Discover({ ev, reload }) {
  const [r, setR] = useState(null);
  const [placeFilter, setPlaceFilter] = useState("all");
  const [placeSearch, setPlaceSearch] = useState("");

  const load = () =>
    api(`/events/${ev.id}/recommendations/`).then(setR);

  useEffect(() => {
    load();
  }, [ev.id]);

  const rate = (kind, id, score) =>
    api("/ratings/", {
      method: "POST",
      body: { kind, object_id: id, score },
    }).then(load);

  const pick = (v) =>
    api(`/events/${ev.id}/`, {
      method: "PATCH",
      body: { venue: v.id, venue_name: v.name },
    }).then(reload);

  if (!r) return <p>Finding the best matches…</p>;

  const onlinePlaces = r.online_places || [];
  const searchText = placeSearch.trim().toLowerCase();

  const filteredPlaces = onlinePlaces.filter((p) => {
    const categoryMatches =
      placeFilter === "all" || p.category === placeFilter;

    const searchMatches = (p.name || "")
      .toLowerCase()
      .includes(searchText);

    return categoryMatches && searchMatches;
  });

  return (
    <>
      {/* Recommended venues */}
      <div className="card">
        <h2>🏛️ Recommended venues</h2>

        <p className="muted">
          Ranked by similarity to your event, capacity, budget fit,
          rating and your feedback. Rate suggestions to teach the recommender.
        </p>

        <div className="grid g2">
          {r.venues.map((v) => (
            <div className="card" style={{ margin: 0 }} key={v.id}>
              <div className="row">
                <h3 style={{ flex: 3 }}>{v.name}</h3>
                <span className="badge b-low auto">
                  {v.score}% match
                </span>
              </div>

              <p className="muted" style={{ margin: "4px 0" }}>
                {v.city} · up to {v.capacity} guests ·{" "}
                {v.outdoor ? "outdoor" : "indoor"} · ⭐ {v.rating}
              </p>

              <p style={{ margin: "4px 0" }}>
                From {inr(v.price)}
              </p>

              <ul className="muted" style={{ margin: "4px 0 8px" }}>
                {v.why.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>

              <div className="row" style={{ alignItems: "center" }}>
                <Stars
                  value={v.my_rating}
                  onRate={(n) => rate("venue", v.id, n)}
                />

                <button
                  className={`btn sm auto ${ev.venue === v.id ? "" : "sec"}`}
                  onClick={() => pick(v)}
                >
                  {ev.venue === v.id ? "✓ Selected" : "Select venue"}
                </button>
              </div>
            </div>
          ))}

          {r.venues.length === 0 && (
            <p className="muted">
              No venue matches your guest count yet. Ask the admin to add more venues.
            </p>
          )}
        </div>
      </div>

      {/* Online places */}
      <div className="card">
        <h2>🌐 Places discovered online</h2>

        <p className="muted">
          Places discovered from OpenStreetMap or Google Search. Check each business’s
          existence, event suitability, capacity, pricing and availability before booking.
        </p>

        <div className="row" style={{ margin: "10px 0" }}>
          {["all", "hotel", "restaurant"].map((category) => (
            <button
              key={category}
              className={`btn sm ${placeFilter === category ? "" : "sec"}`}
              onClick={() => setPlaceFilter(category)}
            >
              {category === "all"
                ? "All places"
                : category === "hotel"
                ? "Hotels"
                : "Restaurants"}
            </button>
          ))}
        </div>

        <input
          value={placeSearch}
          onChange={(e) => setPlaceSearch(e.target.value)}
          placeholder="🔍 Search hotels or restaurants..."
          style={{ marginBottom: 12 }}
        />

        {onlinePlaces.length === 0 ? (
          <p className="muted">
            No online places found for this city. Try again later.
          </p>
        ) : filteredPlaces.length === 0 ? (
          <p className="muted">
            No places match your search or selected category.
            Clear the search or select All places.
          </p>
        ) : (
          <div className="grid g2">
            {filteredPlaces.map((p, i) => (
              <div
                className="card"
                style={{ margin: 0 }}
                key={p.source_url || `${p.name}-${i}`}
              >
                <h3>{p.name}</h3>

                {p.source === "Gemini + Google Search" && (
                  <p className="badge" style={{ display: "inline-block", margin: "0 0 8px" }}>
                    ✨ AI suggestion · Google Search
                  </p>
                )}

                {p.verification_note && (
                  <p className="muted" style={{ margin: "4px 0 8px" }}>
                    ⚠️ {p.verification_note}
                  </p>
                )}

                {p.photo_url && (
                  <img
                    src={p.photo_url}
                    alt={p.name}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                    }}
                    style={{
                      width: "100%",
                      height: 180,
                      objectFit: "cover",
                      borderRadius: 12,
                      marginBottom: 10,
                    }}
                  />
                )}

                {p.ai_score != null && (
                  <p className="muted">
                    ✨ AI relevance: {p.ai_score}/100
                  </p>
                )}

                {p.ai_reason && (
                  <p className="muted">✨ {p.ai_reason}</p>
                )}

                                
                
                {(() => {
                  const type = (ev.event_type || "").toLowerCase();
                  const category = (p.category || "").toLowerCase();

                  let suggestion = "Verify event suitability with the business.";

                  if (category === "hotel") {
                    suggestion =
                      ev.guest_count > 100
                        ? "Potential option for a larger gathering; confirm event facilities."
                        : "Potential option for a small gathering; confirm event facilities.";
                  } else if (category === "restaurant") {
                    suggestion =
                      type.includes("birthday") || type.includes("party")
                        ? "Potential birthday or party dining option; confirm group bookings."
                        : "Potential dining option; confirm group bookings.";
                  }

                  return (
                    <p className="muted" style={{ margin: "4px 0 8px" }}>
                      💡 {suggestion}
                    </p>
                  );
                })()}



                <p className="muted">
                  {p.city} · {p.category}
                </p>

                {p.address && <p>{p.address}</p>}

                {p.phone && (
                  <p>
                    📞 <a href={`tel:${p.phone}`}>{p.phone}</a>
                  </p>
                )}

                {p.estimated_price_range && (
                  <p className="muted">
                    💰 Estimated price: {p.estimated_price_range} (AI estimate; confirm with the venue)
                  </p>
                )}

                <p className="muted">
                  Capacity, price and rating not verified
                </p>

                {p.website && (
                  <p>
                    <a
                      href={p.website}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Business website
                    </a>
                  </p>
                )}

                {p.source_url && (
                  <p>
                    <a
                      href={p.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {p.source === "Gemini + Google Search" ? "View source" : "View OpenStreetMap source"}
                    </a>
                  </p>
                )}

                
                {p.lat != null && p.lng != null && (
                  <p>
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      📍 Get Directions on Google Maps
                    </a>
                  </p>
                )}

              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended vendors */}
      <div className="card">
        <h2>🧑‍🍳 Recommended vendors</h2>

        <div className="grid g2">
          {r.vendors.map((v) => (
            <div className="card" style={{ margin: 0 }} key={v.id}>
              <div className="row">
                <h3 style={{ flex: 3 }}>{v.name}</h3>
                <span className="badge b-low auto">
                  {v.score}% match
                </span>
              </div>

              <p className="muted" style={{ margin: "4px 0" }}>
                {v.category} · {v.city} · ⭐ {v.rating} · from {inr(v.price)}
              </p>

              {v.contact && (
                <p className="muted" style={{ margin: "4px 0" }}>
                  {v.contact}
                </p>
              )}

              <Stars
                value={v.my_rating}
                onRate={(n) => rate("vendor", v.id, n)}
              />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}


/* ---------------- Invitation writer ---------------- */
function Invitation({ ev }) {
  const [o, setO] = useState({ tone: "formal", lang: "en" });
  const [text, setText] = useState("");
  const [msg, setMsg] = useState("");
  const gen = async () => setText((await api(`/events/${ev.id}/invitation/`, { method: "POST", body: o })).text);
  const send = async () => { const r = await api(`/events/${ev.id}/send_invites/`, { method: "POST", body: { message: text } }); setMsg(`Sent to ${r.sent} guest(s).`); };
  return (
    <div className="card">
      <h2>✉️ Invitation writer</h2>
      <div className="row">
        <div><label>Tone</label><select value={o.tone} onChange={(e) => setO({ ...o, tone: e.target.value })}><option value="formal">Formal</option><option value="fun">Fun</option><option value="warm">Warm</option></select></div>
        <div><label>Language</label><select value={o.lang} onChange={(e) => setO({ ...o, lang: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option></select></div>
        <button className="btn auto" onClick={gen}>Generate</button>
      </div>
      {text && <><textarea rows="9" style={{ marginTop: 12 }} value={text} onChange={(e) => setText(e.target.value)} />
        <div className="row" style={{ marginTop: 10 }}><button className="btn sec auto" onClick={() => navigator.clipboard.writeText(text)}>Copy</button>
          <button className="btn auto" onClick={send}>Email to all guests with RSVP link</button></div></>}
      {msg && <div className="okmsg" style={{ marginTop: 10 }}>{msg}</div>}
    </div>
  );
}

/* ---------------- Assistant chat ---------------- */
function Assistant({ ev }) {
  const [log, setLog] = useState([{ who: "ai", text: "Hi! Ask me about this event: weather, budget, guests, or what to do next." }]);
  const [q, setQ] = useState("");
  const ask = async (e) => {
    e.preventDefault();
    const text = q; setQ(""); setLog((l) => [...l, { who: "me", text }]);
    try { const r = await api("/chat/", { method: "POST", body: { message: text, event_id: ev.id } }); setLog((l) => [...l, { who: "ai", text: r.reply }]); }
    catch (x) { setLog((l) => [...l, { who: "ai", text: x.message }]); }
  };
  return (
    <div className="card"><h2>🤖 Planning assistant</h2>
      <div className="chat">{log.map((m, i) => <div key={i} className={`msg ${m.who}`}>{m.text}</div>)}</div>
      <form className="row" onSubmit={ask}><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Will it rain? Am I over budget? What should I do next?" required /><button className="btn auto">Send</button></form>
    </div>
  );
}

/* ---------------- Co-organizers ---------------- */
function Team({ ev }) {
  const [team, setTeam] = useState([]);
  const [f, setF] = useState({ username: "", role: "editor" });
  const [err, setErr] = useState("");
  const load = () => api(`/events/${ev.id}/collaborators/`).then(setTeam);
  useEffect(() => { load(); }, [ev.id]);
  const add = async (e) => { e.preventDefault(); try { setErr(""); setTeam(await api(`/events/${ev.id}/collaborators/`, { method: "POST", body: f })); setF({ ...f, username: "" }); } catch (x) { setErr(x.message); } };
  return (
    <div className="card"><h2>👥 Co-organizers</h2>
      {team.map((m) => <p key={m.id} style={{ margin: "6px 0" }}>{m.username} <span className="badge">{m.role}</span></p>)}
      {ev.role === "owner" && <form className="row" style={{ marginTop: 12 }} onSubmit={add}>
        <div><label>Username or email</label><input value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} required /></div>
        <div><label>Access</label><select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="editor">Editor</option><option value="viewer">Viewer</option></select></div>
        <button className="btn auto">Add</button></form>}
      {err && <div className="err" style={{ marginTop: 10 }}>{err}</div>}
    </div>
  );
}

/* ---------------- Post-event feedback ---------------- */
function Feedback({ ev }) {
  const [d, setD] = useState(null);
  useEffect(() => { api(`/events/${ev.id}/feedback_summary/`).then(setD); }, [ev.id]);
  if (!d) return <p>Loading…</p>;
  const g = d.guests;
  return (
    <>
      <div className="grid g3">
        <div className="card stat"><b>{d.average ?? "–"}</b><span className="muted">Average rating ({d.count} responses)</span></div>
        <div className="card stat"><b>{g.yes ? Math.round((g.checked_in / g.yes) * 100) : 0}%</b><span className="muted">Attendance vs. yes RSVPs</span></div>
        <div className="card stat"><b>{d.sentiment.positive}👍 {d.sentiment.negative}👎</b><span className="muted">Sentiment</span></div>
      </div>
      <div className="card"><h2>Guest comments</h2>
        <p className="muted">Guests can leave feedback on their personal RSVP link after the event date has passed.</p>
        {d.items.length === 0 && <p className="muted">No feedback yet.</p>}
        {d.items.map((f) => <p key={f.id} style={{ margin: "8px 0" }}><span className={`badge b-${f.sentiment}`}>{f.sentiment}</span> ⭐{f.rating} <b>{f.guest_name}</b>: {f.comment}</p>)}
      </div>
    </>
  );
}
