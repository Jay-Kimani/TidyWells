// Tidywells comments: Cloudflare Worker + D1 + Turnstile. Anonymous name + comment, published immediately (Turnstile and honeypot spam checks; every comment is shown).
// Bindings/vars to set in the dashboard: DB (D1), TURNSTILE_SECRET (secret),
// ALLOWED_ORIGINS (plain text, e.g. "https://tidywells.com,https://www.tidywells.com"), IP_SALT (secret, any random string).

const PAGE_RE = /^\/[A-Za-z0-9._\-\/]{1,200}$/;

function cors(req, env) {
  const allowed = (env.ALLOWED_ORIGINS || "https://tidywells.com").split(",").map((s) => s.trim());
  const o = req.headers.get("Origin") || "";
  const ok = allowed.includes(o) || /^https?:\/\/(www\.)?tidywells\.com$/.test(o);
  return {
    "Access-Control-Allow-Origin": ok ? o : allowed[0],
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
  };
}
const json = (data, status, h) =>
  new Response(JSON.stringify(data), { status: status || 200, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...h } });

async function sha(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}
const clean = (s, n) => String(s || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").trim().slice(0, n);

export async function handle(req, env, fetchFn = fetch) {
  const h = cors(req, env);
  const url = new URL(req.url);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });

  if (url.pathname === "/comments" && req.method === "GET") {
    const page = url.searchParams.get("page") || "";
    if (!PAGE_RE.test(page)) return json({ error: "bad page" }, 400, h);
    const r = await env.DB.prepare("SELECT id,name,body,created FROM comments WHERE page=? ORDER BY created ASC LIMIT 200").bind(page).all();
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

  return json({ error: "not found" }, 404, h);
}

export default { fetch: (req, env) => handle(req, env) };
