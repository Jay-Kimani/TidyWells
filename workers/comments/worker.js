// Tidywells comments: Cloudflare Worker + D1 + Turnstile. Anonymous name + comment, published immediately (Turnstile and honeypot spam checks; delete from /admin if needed).
// Bindings/vars to set in the dashboard: DB (D1), TURNSTILE_SECRET (secret), ADMIN_KEY (secret),
// ALLOWED_ORIGINS (plain text, e.g. "https://tidywells.com,https://www.tidywells.com"), IP_SALT (secret, any random string).

const PAGE_RE = /^\/[A-Za-z0-9._\-\/]{1,200}$/;

function cors(req, env) {
  const allowed = (env.ALLOWED_ORIGINS || "https://tidywells.com").split(",").map((s) => s.trim());
  const o = req.headers.get("Origin") || "";
  const ok = allowed.includes(o) || /^https?:\/\/(www\.)?tidywells\.com$/.test(o);
  return {
    "Access-Control-Allow-Origin": ok ? o : allowed[0],
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Admin-Key",
    Vary: "Origin",
  };
}
const json = (data, status, h) =>
  new Response(JSON.stringify(data), { status: status || 200, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...h } });

async function sha(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}
function sameKey(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
const clean = (s, n) => String(s || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").trim().slice(0, n);

export async function handle(req, env, fetchFn = fetch) {
  const h = cors(req, env);
  const url = new URL(req.url);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });

  if (url.pathname === "/comments" && req.method === "GET") {
    const page = url.searchParams.get("page") || "";
    if (!PAGE_RE.test(page)) return json({ error: "bad page" }, 400, h);
    const r = await env.DB.prepare("SELECT id,name,body,created FROM comments WHERE page=? AND approved=1 ORDER BY created ASC LIMIT 200").bind(page).all();
    return json({ comments: r.results || [] }, 200, h);
  }

  if (url.pathname === "/comments" && req.method === "POST") {
    let d;
    try { d = await req.json(); } catch { return json({ error: "bad json" }, 400, h); }
    if (d.website) return json({ ok: true }, 200, h); // honeypot: pretend success
    const page = String(d.page || ""), name = clean(d.name, 60), body = clean(d.body, 2000);
    if (!PAGE_RE.test(page) || name.length < 1 || body.length < 2) return json({ error: "Please enter a name and a comment." }, 400, h);
    if (/https?:\/\/|www\./i.test(name)) return json({ error: "Please don't put links in the name." }, 400, h);
    const ip = req.headers.get("CF-Connecting-IP") || "";
    const ts = await fetchFn("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ secret: env.TURNSTILE_SECRET || "", response: String(d.token || ""), remoteip: ip }),
    }).then((r) => r.json()).catch(() => ({ success: false }));
    if (!ts.success) return json({ error: "Spam check failed. Please try again." }, 403, h);
    const ipHash = await sha((env.IP_SALT || "") + ip);
    const recent = await env.DB.prepare("SELECT COUNT(*) AS n FROM comments WHERE ip_hash=? AND created>?").bind(ipHash, Date.now() - 3600000).first();
    if (recent && recent.n >= 5) return json({ error: "Too many comments. Please try again later." }, 429, h);
    const links = (body.match(/https?:\/\//gi) || []).length;
    if (links > 2) return json({ error: "Please limit links to two." }, 400, h);
    await env.DB.prepare("INSERT INTO comments (page,name,body,created,approved,ip_hash) VALUES (?,?,?,?,1,?)").bind(page, name, body, Date.now(), ipHash).run();
    return json({ ok: true }, 200, h);
  }

  if (url.pathname.startsWith("/admin")) {
    if (url.pathname === "/admin" && req.method === "GET") return new Response(ADMIN_HTML, { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } });
    if (!sameKey(req.headers.get("X-Admin-Key") || "", env.ADMIN_KEY || "")) return json({ error: "unauthorized" }, 401, h);
    if (url.pathname === "/admin/pending") {
      const r = await env.DB.prepare("SELECT id,page,name,body,created,approved FROM comments ORDER BY approved ASC, created DESC LIMIT 200").all();
      return json({ comments: r.results || [] }, 200, h);
    }
    if (req.method === "POST" && (url.pathname === "/admin/approve" || url.pathname === "/admin/delete")) {
      const d = await req.json().catch(() => ({}));
      const id = parseInt(d.id, 10);
      if (!id) return json({ error: "bad id" }, 400, h);
      if (url.pathname === "/admin/approve") await env.DB.prepare("UPDATE comments SET approved=1 WHERE id=?").bind(id).run();
      else await env.DB.prepare("DELETE FROM comments WHERE id=?").bind(id).run();
      return json({ ok: true }, 200, h);
    }
  }
  return json({ error: "not found" }, 404, h);
}

export default { fetch: (req, env) => handle(req, env) };

const ADMIN_HTML = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Comments admin</title>
<style>body{font:15px system-ui;max-width:760px;margin:20px auto;padding:0 14px;background:#0a0f16;color:#e8edf6}input,button{font:inherit;padding:7px 10px;border-radius:8px;border:1px solid #445;background:#1a2230;color:inherit}
.c{border:1px solid #334;border-radius:10px;padding:10px 12px;margin:10px 0}.p{border-color:#ff1f3d}small{color:#97a6bb}button.g{background:#0b5ed7}button.r{background:#a3182b}pre{white-space:pre-wrap;margin:6px 0;font:inherit}</style></head>
<body><h2>Comments admin</h2><p><input id="k" type="password" placeholder="Admin key"> <button id="go">Load</button></p><div id="o"></div>
<script>
const o=document.getElementById("o"),k=document.getElementById("k");
async function api(p,b){const r=await fetch(p,{method:b?"POST":"GET",headers:{"X-Admin-Key":k.value,"Content-Type":"application/json"},body:b?JSON.stringify(b):undefined});if(!r.ok)throw new Error(r.status);return r.json()}
async function load(){o.textContent="";try{const d=await api("/admin/pending");if(!d.comments.length)o.textContent="No comments yet.";
for(const c of d.comments){const e=document.createElement("div");e.className="c"+(c.approved?"":" p");
const m=document.createElement("small");m.textContent=(c.approved?"approved":"PENDING")+" · "+c.page+" · "+new Date(c.created).toLocaleString();
const n=document.createElement("b");n.textContent=c.name;const t=document.createElement("pre");t.textContent=c.body;e.append(m,document.createElement("br"),n,t);
if(!c.approved){const a=document.createElement("button");a.className="g";a.textContent="Approve";a.onclick=async()=>{await api("/admin/approve",{id:c.id});load()};e.append(a," ")}
const x=document.createElement("button");x.className="r";x.textContent="Delete";x.onclick=async()=>{if(confirm("Delete this comment?")){await api("/admin/delete",{id:c.id});load()}};e.append(x);o.append(e)}}catch(e){o.textContent="Could not load (wrong key?)"}}
document.getElementById("go").onclick=load;
</script></body></html>`;
