import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, saveAuth } from "../api";

export default function Auth() {
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ username: "", email: "", password: "", role: "user" });
  const [err, setErr] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try { saveAuth(await api(`/auth/${mode}/`, { method: "POST", body: f, auth: false })); nav("/"); }
    catch (x) { setErr(x.message); }
  };
  return (
    <div className="center">
      <form className="card" onSubmit={submit}>
        <h1>🎉 AI Event Planner</h1>
        <p className="muted">{mode === "login" ? "Welcome back! Log in to plan your events." : "Create your account."}</p>
        {err && <div className="err">{err}</div>}
        <label>Username</label><input value={f.username} onChange={set("username")} required />
        {mode === "register" && <><label style={{ marginTop: 10 }}>Email</label><input type="email" value={f.email} onChange={set("email")} />
          <label style={{ marginTop: 10 }}>I am a</label>
          <select value={f.role} onChange={set("role")}><option value="user">Event organizer</option><option value="vendor">Vendor / service provider</option></select></>}
        <label style={{ marginTop: 10 }}>Password</label><input type="password" value={f.password} onChange={set("password")} required />
        <button className="btn" style={{ width: "100%", marginTop: 16 }}>{mode === "login" ? "Log in" : "Sign up"}</button>
        <p className="muted" style={{ textAlign: "center" }}>
          {mode === "login" ? "New here? " : "Already registered? "}
          <a href="#" onClick={(e) => { e.preventDefault(); setMode(mode === "login" ? "register" : "login"); setErr(""); }}>{mode === "login" ? "Sign up" : "Log in"}</a>
        </p>
        <p className="muted">Demo: demo / demo12345</p>
      </form>
    </div>
  );
}
