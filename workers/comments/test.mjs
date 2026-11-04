import { handle } from "./worker.js";
const rows = [];
const DB = { prepare(sql) { return { _a: [], bind(...a) { this._a = a; return this; },
  async all() { const [p] = this._a; return { results: rows.filter((r) => r.page === p && r.approved === 1) }; },
  async first() { return { n: rows.filter((r) => r.ip_hash === this._a[0]).length }; },
  async run() { if (sql.startsWith("INSERT")) { const [page, name, body, created, ip_hash] = this._a; rows.push({ id: rows.length + 1, page, name, body, created, approved: 0, ip_hash }); }
    if (sql.startsWith("UPDATE")) rows.find((r) => r.id === this._a[0]).approved = 1; } }; } };
const env = { DB, ADMIN_KEY: "k3y", TURNSTILE_SECRET: "s", IP_SALT: "x", ALLOWED_ORIGINS: "https://tidywells.com" };
const ok = async () => ({ json: async () => ({ success: true }) }), bad = async () => ({ json: async () => ({ success: false }) });
const post = (b) => new Request("https://w/comments", { method: "POST", body: JSON.stringify(b), headers: { Origin: "https://tidywells.com", "CF-Connecting-IP": "1.2.3.4" } });
const a = (c, m) => { if (!c) { console.log("FAIL", m); process.exit(1); } };
a((await handle(post({ page: "/posts/a.html", name: "Sam", body: "Nice post", token: "t" }), env, ok)).status === 200, "post ok");
a(rows.length === 1 && rows[0].approved === 0, "held for approval");
a((await handle(post({ page: "/posts/a.html", name: "Sam", body: "Nice", token: "t" }), env, bad)).status === 403, "turnstile fail");
a((await handle(post({ page: "../x", name: "Sam", body: "Nice", token: "t" }), env, ok)).status === 400, "bad page");
a((await handle(post({ page: "/p.html", name: "http://spam.com", body: "Nice", token: "t" }), env, ok)).status === 400, "link in name");
a(rows.length === 1, "honeypot/blocked not stored");
let r = await handle(new Request("https://w/comments?page=/posts/a.html"), env); a((await r.json()).comments.length === 0, "pending hidden");
a((await handle(new Request("https://w/admin/pending"), env)).status === 401, "admin needs key");
r = await handle(new Request("https://w/admin/approve", { method: "POST", body: JSON.stringify({ id: 1 }), headers: { "X-Admin-Key": "k3y" } }), env); a(r.status === 200, "approve");
r = await handle(new Request("https://w/comments?page=/posts/a.html"), env); a((await r.json()).comments.length === 1, "approved shown");
console.log("worker tests passed");
const pre = await handle(new Request("https://w/comments", { method: "OPTIONS", headers: { Origin: "http://www.tidywells.com" } }), env);
if (pre.headers.get("Access-Control-Allow-Origin") !== "http://www.tidywells.com") { console.log("FAIL cors http www"); process.exit(1); }
const bad2 = await handle(new Request("https://w/comments", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
if (bad2.headers.get("Access-Control-Allow-Origin") === "https://evil.example") { console.log("FAIL cors evil"); process.exit(1); }
console.log("cors tests passed");
