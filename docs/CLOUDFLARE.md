# Cloudflare (Free) in front of Sotooh — optional, NOT required for launch

Current architecture works fine without Cloudflare:

```
REG.RU DNS  →  RUVDS VPS (194.135.33.29)  →  Caddy (auto-HTTPS)
```

## When to add Cloudflare

Consider it later for DDoS protection, caching static assets, and hiding the
server IP. Do NOT add it before the current stack is stable.

## How to add (later)

1. Create a free account at cloudflare.com → "Add a site" → `sotoohsolar.com`.
2. Choose the **Free** plan. Cloudflare scans and imports existing DNS records.
3. Verify the imported records match:
   - `A  @    194.135.33.29  (Proxied: optional — start with DNS-only)`
   - `A  www  194.135.33.29  (Proxied: optional)`
4. REG.RU → DNS-серверы → replace nameservers with the two Cloudflare NS
   (e.g. `xxx.ns.cloudflare.com`, `yyy.ns.cloudflare.com`). NS propagation
   can take up to 24–48 h.
5. SSL/TLS mode: set **Full (strict)** — Caddy already has a valid Let's
   Encrypt cert, so strict mode works.
6. Only after everything resolves correctly, switch records from
   "DNS only" (grey cloud) to "Proxied" (orange cloud).

## Important caveats

- With Proxied mode, Let's Encrypt HTTP-01 renewal still works (CF passes
  `/.well-known/acme-challenge` through), but if you ever enable "Always Use
  HTTPS" + strict redirects loops, double-check Caddy's auto-HTTPS.
- Real client IPs: Caddy will see Cloudflare IPs. To restore client IPs add
  `trusted_proxies` with Cloudflare IP ranges (see cloudflare.com/ips) to the
  Caddyfile site block.
- Keep a DNS-only (grey) record for direct SSH diagnostics — SSH is not
  proxied anyway.
