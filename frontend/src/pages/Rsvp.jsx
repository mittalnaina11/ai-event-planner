import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export default function Rsvp() {
  const { token } = useParams();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [fb, setFb] = useState({ rating: 5, comment: "" });
  const [thanks, setThanks] = useState(false);
  useEffect(() => { api(`/rsvp/${token}/`, { auth: false }).then(setD).catch((e) => setErr(e.message)); }, [token]);
  const reply = async (rsvp) => setD(await api(`/rsvp/${token}/`, { method: "POST", body: { rsvp }, auth: false }));
  const sendFb = async () => { await api(`/rsvp/${token}/feedback/`, { method: "POST", body: fb, auth: false }); setThanks(true); };
  if (err) return <div className="center"><div className="card err">{err}</div></div>;
  if (!d) return <div className="center">Loading…</div>;
  const e = d.event;
  return (
    <div className="center">
      <div className="card">
        <h1>🎉 {e.title}</h1>
        <p>Hi <b>{d.guest}</b>, you're invited!</p>
        <p className="muted">📅 {new Date(e.date).toDateString()} at {e.time}<br />📍 {e.venue || e.city}{e.theme && <><br />🎨 Theme: {e.theme}</>}</p>
        {!e.past && (<>
          <p>Will you attend? Current reply: <span className={`badge b-${d.rsvp}`}>{d.rsvp}</span></p>
          <div className="row">{["yes", "maybe", "no"].map((x) => <button key={x} className={`btn ${d.rsvp === x ? "" : "sec"}`} onClick={() => reply(x)}>{x === "yes" ? "✅ Yes" : x === "no" ? "❌ No" : "🤔 Maybe"}</button>)}</div>
        </>)}
        {d.rsvp === "yes" && !e.past && (
          <div style={{ textAlign: "center", marginTop: 16 }}>
            <p className="muted">Show this QR code at the entrance</p>
            <img src={`/api/qr/${d.token}/`} alt="Entry QR code" width="180" />
          </div>
        )}
        {e.past && !d.feedback_given && !thanks && (<>
          <h3>How was the event?</h3>
          <label>Rating (1–5)</label><input type="number" min="1" max="5" value={fb.rating} onChange={(x) => setFb({ ...fb, rating: x.target.value })} />
          <label style={{ marginTop: 8 }}>Comments</label><textarea rows="3" value={fb.comment} onChange={(x) => setFb({ ...fb, comment: x.target.value })} />
          <button className="btn" style={{ marginTop: 10 }} onClick={sendFb}>Send feedback</button>
        </>)}
        {(thanks || d.feedback_given) && <div className="okmsg">Thank you for your feedback! 💜</div>}
      </div>
    </div>
  );
}
