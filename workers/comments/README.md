# Tidywells comments (Cloudflare Worker + D1 + Turnstile)

Anonymous name + comment, published immediately. Free on Cloudflare's free tier.

## Dashboard setup (no command line)
1. **D1 database:** Cloudflare dashboard > Storage & databases > D1 > Create database, name it `tidywells-comments`.
   Open it > Console, paste the contents of `schema.sql`, run.
2. **Turnstile:** Turnstile > Add widget. Name `Tidywells`, hostname `tidywells.com` (and `www.tidywells.com`), mode Managed.
   Copy the **Site key** (public) and **Secret key** (private).
3. **Worker:** Workers & Pages > Create > Create Worker, name `tidywells-comments`, Deploy, then Edit code,
   replace everything with `worker.js`, Deploy.
4. **Bindings and variables** (Worker > Settings):
   - Bindings > Add > D1 database, variable name `DB`, pick `tidywells-comments`.
   - Variables and secrets: `TURNSTILE_SECRET` (secret, the Turnstile secret key), `ADMIN_KEY` (secret, a long random
     passphrase you choose), `IP_SALT` (secret, any random string), `ALLOWED_ORIGINS` (text: `https://tidywells.com,https://www.tidywells.com`).
5. Copy the Worker URL (like `https://tidywells-comments.YOURNAME.workers.dev`) and the Turnstile **site key** into
   `docs/config.js` as `TIDYWELLS_COMMENTS_API` and `TIDYWELLS_TURNSTILE_SITEKEY`. Push.

## Moderating
Open `<worker URL>/admin`, enter your admin key, press Load. Delete anything you do not want shown. New comments publish immediately.
Bookmark it. (There are no email notifications; check it when you publish a post.)

## Notes
- The admin key is never stored in the repo. Never put the Turnstile secret or admin key in `config.js`.
- Local test: `node workers/comments/test.mjs`.
