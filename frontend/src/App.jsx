
import { useEffect, useState } from "react";
import {
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useLocation,
} from "react-router-dom";

import { api, getToken, getUser, logout } from "./api";
import Auth from "./pages/Auth.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import EventDetail from "./pages/EventDetail.jsx";
import Rsvp from "./pages/Rsvp.jsx";
import Admin from "./pages/Admin.jsx";

function Layout({ children }) {
  const nav = useNavigate();
  const location = useLocation();
  const user = getUser();

  const [notes, setNotes] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api("/notifications/")
      .then(setNotes)
      .catch(() => {});
  }, []);

  const unread = notes.filter((n) => !n.read).length;

  const toggle = async () => {
    const willOpen = !open;
    setOpen(willOpen);

    if (willOpen && unread) {
      try {
        await api("/notifications/read_all/", { method: "POST" });
        setNotes((previous) =>
          previous.map((n) => ({ ...n, read: true }))
        );
      } catch {
        // Keep the notification panel usable if marking read fails.
      }
    }
  };

  const isDashboard = location.pathname === "/";
  const isAdmin = location.pathname === "/admin";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="sidebar-brand">
          <span className="sidebar-logo">🎉</span>
          <span>
            <strong>AI Event</strong>
            <small>PLANNER</small>
          </span>
        </Link>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          <Link
            to="/"
            className={`sidebar-link ${isDashboard ? "active" : ""}`}
          >
            <span>▦</span>
            Dashboard
          </Link>

          <a href="/#events" className="sidebar-link">
            <span>◷</span>
            My Events
          </a>

          <a href="/#ai-planner" className="sidebar-link">
            <span>✧</span>
            AI Planner
          </a>

          <a href="/#new-event" className="sidebar-link">
            <span>＋</span>
            Create Event
          </a>

          <a href="/#calendar" className="sidebar-link">
            <span>▦</span>
            Calendar
          </a>

          {user?.is_admin && (
            <Link
              to="/admin"
              className={`sidebar-link ${isAdmin ? "active" : ""}`}
            >
              <span>⚙</span>
              Admin Panel
            </Link>
          )}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-avatar">
            {(user?.username || "U").charAt(0).toUpperCase()}
          </div>
          <div className="sidebar-user">
            <strong>{user?.username || "User"}</strong>
            <small>{user?.is_admin ? "Administrator" : "Event Planner"}</small>
          </div>
          <button
            className="sidebar-logout"
            title="Logout"
            onClick={() => {
              logout();
              nav("/login");
            }}
          >
            ↪
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div>
            <div className="topbar-title">
              {isDashboard
                ? "Dashboard"
                : isAdmin
                ? "Admin Panel"
                : location.pathname.startsWith("/events/")
                ? "Event Details"
                : "AI Event Planner"}
            </div>
            <div className="topbar-subtitle">
              Plan memorable events, effortlessly.
            </div>
          </div>

          <div className="topbar-actions">
            <button className="notification-button" onClick={toggle}>
              🔔
              {unread > 0 && <span className="notification-count">{unread}</span>}
            </button>
            <span className="topbar-username">{user?.username}</span>
          </div>
        </header>

        {open && (
          <div className="notification-panel">
            <div className="notification-heading">
              <h3>Notifications</h3>
              <button onClick={() => setOpen(false)}>✕</button>
            </div>

            {notes.length === 0 ? (
              <p className="muted">Nothing yet.</p>
            ) : (
              notes.map((n) => (
                <div className="notification-item" key={n.id}>
                  <p>{n.message}</p>
                  <small>{new Date(n.created_at).toLocaleString()}</small>
                </div>
              ))
            )}
          </div>
        )}

        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}

const Protected = ({ children }) =>
  getToken() ? <Layout>{children}</Layout> : <Navigate to="/login" />;

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth />} />
      <Route path="/rsvp/:token" element={<Rsvp />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/events/:id" element={<Protected><EventDetail /></Protected>} />
      <Route path="/admin" element={<Protected><Admin /></Protected>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
