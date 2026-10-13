const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "") + "/api";
export const getToken = () => localStorage.getItem("token");
export const getUser = () => JSON.parse(localStorage.getItem("user") || "null");
export const saveAuth = (d) => { localStorage.setItem("token", d.token); localStorage.setItem("user", JSON.stringify(d)); };
export const logout = () => { localStorage.removeItem("token"); localStorage.removeItem("user"); };

function formatErrors(data) {
  if (!data || typeof data !== "object") return "Something went wrong.";
  if (typeof data.detail === "string") return data.detail;
  return Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(" ")}`).join(" | ");
}

export async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && getToken()) headers.Authorization = "Token " + getToken();
  const res = await fetch(BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatErrors(data));
  return data;
}

export async function download(path, filename) {
  const res = await fetch(BASE + path, { headers: { Authorization: "Token " + getToken() } });
  if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(formatErrors(d)); }
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

export const inr = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const TYPES = [["wedding", "Wedding"], ["birthday", "Birthday"], ["corporate", "Corporate"], ["college_fest", "College Fest"],
  ["conference", "Conference"], ["party", "Party"], ["other", "Other"]];
