import { useEffect, useState } from "react";
import { api } from "../api";

export default function Admin() {
  const [a, setA] = useState(null);
  const [users, setUsers] = useState([]);
  const [err, setErr] = useState("");
  const load = () => {
    api("/admin/analytics/").then(setA).catch((e) => setErr(e.message));
    api("/admin/users/").then(setUsers).catch(() => {});
  };
  useEffect(load, []);
  const del = async (u) => { if (confirm(`Delete user ${u.username}?`)) { await api(`/admin/users/${u.id}/`, { method: "DELETE" }); load(); } };
  const toggle = async (u) => { await api(`/admin/users/${u.id}/`, { method: "PATCH", body: { is_active: !u.is_active } }); load(); };
  if (err) return <div className="err">{err} (admin access required)</div>;
  if (!a) return <p>Loading…</p>;
  const max = Math.max(1, ...a.by_type.map((t) => t.n));
  const maxM = Math.max(1, ...a.by_month.map((m) => m.n));
  return (
    <>
      <h1>Admin dashboard</h1>
      <div className="grid g3">
        {[["Users", a.users], ["Events", a.events], ["Upcoming", a.upcoming], ["Guests", a.guests], ["Avg feedback", a.avg_feedback ? a.avg_feedback.toFixed(1) + "/5" : "–"]].map(([k, v]) =>
          <div className="card stat" key={k}><b>{v}</b><span className="muted">{k}</span></div>)}
      </div>
      <div className="grid g2">
        <div className="card"><h2>Popular event types</h2>
          {a.by_type.map((t) => <div key={t.event_type} style={{ marginBottom: 8 }}>{t.event_type.replace("_", " ")} ({t.n})<div className="bar"><i style={{ width: `${(t.n / max) * 100}%` }} /></div></div>)}
        </div>
        <div className="card"><h2>Events created (6 months)</h2>
          {a.by_month.map((m) => <div key={m.month} style={{ marginBottom: 8 }}>{m.month} ({m.n})<div className="bar"><i style={{ width: `${(m.n / maxM) * 100}%` }} /></div></div>)}
        </div>
        <div className="card"><h2>Top vendors</h2>
          {a.top_vendors.map((v) => <p key={v.name} style={{ margin: "6px 0" }}>⭐ {v.rating} · {v.name} <span className="muted">({v.category})</span></p>)}
        </div>
        <div className="card"><h2>RSVP overview</h2>
          {Object.entries(a.rsvp).map(([k, v]) => <p key={k} style={{ margin: "6px 0" }}><span className={`badge b-${k}`}>{k}</span> {v}</p>)}
        </div>
      </div>
      <div className="card"><h2>Users</h2>
        <table><thead><tr><th>Username</th><th>Email</th><th>Role</th><th>Active</th><th></th></tr></thead>
          <tbody>{users.map((u) => <tr key={u.id}><td>{u.username}{u.is_staff && " 🛡️"}</td><td>{u.email}</td><td>{u.role}</td>
            <td><button className="btn sm sec" onClick={() => toggle(u)}>{u.is_active ? "Active" : "Disabled"}</button></td>
            <td><button className="btn sm danger" onClick={() => del(u)}>Delete</button></td></tr>)}</tbody></table>
      </div>
    </>
  );
}
