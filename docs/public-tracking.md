# Public Tracking — Architecture & Security

Customer-facing repair tracker (LBC/Shopee-style), **no account needed**.

**Live URL:** `https://trinly01.github.io/EasyPC/`

## Customer experience

1. Customer opens the tracker (link shared at intake, or QR on the printed form — planned)
2. Enters **work order number** + **registered mobile number** (full `0917 123 4567` or last 4 digits)
3. Sees: current status badge, journey timeline, activity log, unit/store, dates, warranty, services with prices, and a **Join call** button when a Jitsi link exists

The printed `tracking_token` still works as the key — backward compatible with anything already issued.

## API contract

```
POST https://likha-playground.zyberlab.com/flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70
Content-Type: application/json

{ "wo": "WO-2026-0001", "key": "09171234567" }
```

`key` classification inside the `validate` op:

- **Digits only (4–15 chars)** → phone match: `right(normalized contact_no, len(key)) = key` — suffix match, so last-4 and full number both work; `+63`/`63` prefixes normalize to trunk `0`
- **Alnum 8–32 chars** → legacy `tracking_token` exact match
- Legacy body field `token` is still accepted (`key || token`)

Response (200 always for well-formed input):

```json
{ "found": true,
  "work_order": {
    "number": "WO-2026-0001", "status": "testing",
    "received": "2026-10-17 06:12:33", "released_at": null,
    "service_warranty_until": null,
    "video_call_link": "https://meet.jit.si/easypc-wo-2026-0001-xxxxxxxx",
    "unit_type": "desktop", "unit": "...", "test_result": null,
    "store": { "name": "Gilmore HQ", "code": "GIL" },
    "services": [{"name": "Cleaning", "charged_price": 500}],
    "updates": [{"milestone": "testing", "message": "...", "date_created": "..."}]
  } }
```

`{ "found": false }` on any mismatch — identical response whether the WO doesn't exist or the key is wrong (no oracle).

## Security model

- **Zero public collection permissions.** Unauthenticated `GET /items/easypc_work_orders` → `403`. The webhook flow is the *only* public surface and runs server-side with full permissions via `likha_sql`.
- **Two-factor lookup:** WO number (sequential/guessable) alone returns nothing — needs the customer's phone or the unguessable token.
- **PII-safe response:** no customer name, contact, email, receiver ID, internal notes, technician identity. Timestamps `::text`-cast.
- **Token never exposed:** `tracking_token` is hidden/readonly, absent from every public field list.
- Verified: valid pair → payload; wrong phone → `found:false`; another customer's phone → `found:false`; enumeration → `403`.

### Hardening backlog

- [ ] Rate-limit the webhook (last-4 phone = 10k keyspace per WO — brute-forceable without throttling)
- [ ] `public_message` field on updates to curate what's shown (raw `message` can carry internals/Jitsi links)
- [ ] QR code on the printed form pointing at the tracker URL

## Frontend (`tracker/`)

- **Stack:** Vite 6 + React 19 + Tailwind 4 + shadcn-style components (`cn`, cva variants — `npx shadcn add` compatible)
- **Theme:** dark-first, EasyPC vivid green primary, "TECH IT EASY" tagline
- **Routes:** `/` lookup → `/track/:wo/:key` result. `?wo=<number>` query param on `/` pre-fills the WO field — used by the printed QR code (`tracking_url/?wo=WO-…`), so scanning lands the customer with only their mobile number left to type
- **Deploy:** `.github/workflows/deploy-pages.yml` → GitHub Pages on push to `main` touching `tracker/**`. Pages source = "GitHub Actions". `basename="/EasyPC"`.
- **SPA fallback:** `public/404.html` copies `index.html` with a path-preserving redirect so clean URLs survive refresh.

## CORS

The Pages origin `https://trinly01.github.io` must be allowed in Directus `CORS_ORIGIN` (or `CORS_ENABLED=true` with matching origin) for the browser `fetch` to reach the webhook.
