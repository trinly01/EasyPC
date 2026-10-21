# Flows — Automation Reference

All EasyPC flows are prefixed `easypc_`. Flows run with `accountability: all` unless noted. Gating is done inside `exec` ops with `throw` — the `condition` op is unreliable on this build. Item writes that would re-trigger `items.update` listeners use `emitEvents: false` to stay loop-safe.

## `easypc_generate_wo_number` — numbering + tracking token

| | |
|---|---|
| Trigger | `event` → `items.create` on `easypc_work_orders` |
| ID | `44615a57-1342-406e-947e-653e964809f8` |

`count` (item-read: count WOs) → `format` (exec: build `WO-YYYY-NNNN` + random `tracking_token`) → `getset` (likha_sql: read `easypc_settings`) → `pick` (exec: flatten `getset.rows[0]`) → `setnum` (item-update: writes all fields, `emitEvents: false`) → `genqr` (exec: build qrserver URL for `track/<WO>/<token>`) → `qreq` (request: fetch QR SVG) → `b64` (exec: base64 → `data:image/svg+xml` URI) → `setqr` (item-update: write `tracking_qr`, `emitEvents: false`).

- `work_order_number` — `WO-2026-0001` style, count-based sequence
- `tracking_token` — 16-char random alnum, hidden readonly field; still accepted as a lookup key for the public tracker (backward compat for already-printed forms/links)
- `terms_version` / `terms_snapshot` / `waiver_snapshot` — legal text frozen onto the WO at intake from `easypc_settings`; printed forms always show what the customer actually agreed to, even if settings change later
- `settings` — M2O link to the singleton row; lets print/email contexts resolve **live** values (`tracking_url`, `support_email`, `video_base_url`) via `{{ settings.* }}`
- `tracking_qr` — QR as `data:image/svg+xml` URI, hidden readonly. Built because exec ops have **no `fetch`** (uses a `request` op instead) and CSP originally blocked external images. Since CSP now permits `http: https:` images, the print template renders the QR as a direct `api.qrserver.com` URL instead — `tracking_qr` remains a populated fallback; the `genqr → qreq → b64 → setqr` ops can be removed if direct-URL rendering is settled

## `easypc_appointment_options` — public booking form feed

| | |
|---|---|
| Trigger | `webhook` GET — `/flows/trigger/ed1c258e-54b1-4183-9a3a-492f4d054efc` |
| ID | `ed1c258e-54b1-4183-9a3a-492f4d054efc` |

`load` (likha_sql: active stores + booking config) → `loadsvc` (likha_sql: services) → `shape` (exec: sanitized {stores, services}). Public, PII-free — feeds the booking form.

## `easypc_appointment_slots` — Calendly-style slot feed

| | |
|---|---|
| Trigger | `webhook` GET — `/flows/trigger/dfc7c15a-ccaf-47f2-ba7d-bfafd4728e0f?store=<uuid>&date=YYYY-MM-DD` |
| ID | `dfc7c15a-ccaf-47f2-ba7d-bfafd4728e0f` |

`load` (likha_sql: store slot config) → `counts` (likha_sql: confirmed bookings grouped by `preferred_time` for the date) → `respond` (exec: generates slots from `open_time`→`close_time` stepping `slot_minutes`; each slot `{time, remaining, available}`; disables past slots on same-day in Asia/Manila time; returns `{closed: true}` on closed weekdays).

**Gotcha:** `likha_sql` returns `rows: null` for multi-statement SQL — one statement per op. `{{$trigger.query.x}}` interpolates fine in `sql`.

## `easypc_appointment_book` — instant-confirm booking

| | |
|---|---|
| Trigger | `webhook` POST |
| ID | `9bf3bc0a-1bb5-4613-be99-1f6dac87eee4` |

`validate` (exec: required fields incl. `preferred_time` `h:mm AM/PM`, mobile `63→0` normalize, email regex, quote-escape) → `capcheck` (likha_sql: store config + booked count for the **date and the slot**) → `gate` (exec: open-day / daily-capacity / **slot_capacity** / past / same-day-past-slot (Asia/Manila) / max-advance checks) → `findcust` (likha_sql: find-or-create by `contact_no`) → `mknum` → `mktoken` → `create` (item-create) → `confmail` → `respond`.

## `easypc_appointment_manage` — view / cancel / reschedule

| | |
|---|---|
| Trigger | `webhook` POST |
| ID | `671f175c-b048-4e87-88e9-2563e5a972db` |

`auth` (exec: `APPT-YYYY-NNNN` + mobile suffix normalize + action; reschedule requires `new_date` + `new_time` slot label) → `fetch` (likha_sql: appt + customer phone suffix-match) → `capcheck` (likha_sql: day + **slot** capacity for the reschedule target, excluding the appointment itself) → `decide` (exec: view→skip, cancel→armed, reschedule→slot-checked) → `apply` (likha_sql: armed-guarded UPDATE incl. `preferred_time`) → `respond` (exec: `booking` incl. `status` + `store_id` for the frontend slot grid).

## `easypc_appointment_checkin` — front-desk WO creation

| | |
|---|---|
| Trigger | `manual` — item-level on `easypc_appointments`, confirm prompt |
| ID | `6374c703-9835-4f1e-a534-46ef8f41306f` |

`pick` (exec: extract selected id) → `load` (likha_sql: appt + customer + service) → `guard` (exec: throw if cancelled/already checked in) → `mkwo` (item-create `easypc_work_orders` — **`emitEvents: true`** so numbering/token/QR flows fire; payload pre-fills customer/store/unit_type/concern) → `linkappt` (item-update: `status=arrived`, `work_order={{mkwo.0}}` — mkwo returns a keys **array**) → `respond`.

## `easypc_video_link` — Jitsi proof-of-work link

| | |
|---|---|
| Trigger | `event` → `items.update` on `easypc_work_orders` |
| ID | `4c437b57-02f1-4ede-9dc0-24fa072ded0c` |

`rd` (item-read: current WO) → `genlink` (exec: gate — only when status ∈ `in_repair` / `testing`; reuse existing link, else build `https://meet.jit.si/easypc-<wo>-<rand8>`) → `setlink` (item-update: write `video_call_link`, `emitEvents: false`) → `mkupdate` (item-create: `easypc_work_order_updates` row, `notify_customer: true`, milestone `in_repair`/`testing`, message contains the link).

- Link generated on **first** `in_repair`; **never regenerated** on rework loops (`testing → in_repair` reuses it — one stable room per WO)
- Customer messages: first repair / resumed repair / testing — each worded differently
- `testing` notification is owned by this flow (richer message); the generic milestone flow skips `testing` to avoid double-posting

## `easypc_status_milestone` — milestone updates

| | |
|---|---|
| Trigger | `event` → `items.update` on `easypc_work_orders` |
| ID | `9f9f86f7-58fa-432b-a56a-012c0c067f54` |

`check` (exec: did `status` change to a notifiable value?) → `gate` (condition, kept for reference — exec gate does the real work) → `mkupdate` (item-create: update row with milestone + message).

Notifiable statuses (verified against live op code): `awaiting_approval`, `ready_for_release`, `released`. `testing` intentionally excluded — owned by `easypc_video_link`.

## `easypc_notify_on_update` — customer email

| | |
|---|---|
| Trigger | `event` → `items.create` on `easypc_work_order_updates` |
| ID | `f35b531b-b194-4e0e-87e2-ce5845b60840` |

`check` (exec: `notify_customer` flag set?) → `readupd` (item-read: update + WO + customer) → `buildmail` (exec: subject/body) → `gate` → `sendmail` (mail op) → `stampsent` (item-update: `notification_sent_at`, `emitEvents: false`).

> ✅ Verified live (Oct 17) — server uses `EMAIL_TRANSPORT=smtp` via GoDaddy Titan (`smtpout.secureserver.net:465`, SSL). Note: the `mail` op logs errors but doesn't halt the chain — `notification_sent_at` stamps even if the send fails, so treat it as "attempted" not "delivered".

## `easypc_warranty_stamp` — release + warranty stamping

| | |
|---|---|
| Trigger | `event` → `items.update` on `easypc_work_orders` |
| ID | `9481eea4-dd6d-467c-a5e6-1c8bdae07dcb` |

`check` (exec: status payload == `released`? throws otherwise) → `stamp` (item-update: `released_at` = now, `service_warranty_until` = +30 days, `emitEvents: false`).

Per-part `warranty_until` (parts_used lines) is stamped from `released_at + warranty_days`.

## `easypc_track_lookup` — public tracking endpoint

| | |
|---|---|
| Trigger | `webhook` → `POST /flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70` |
| ID | `eedd97d4-5c26-4e47-a26f-040806686d70` |

`validate` (exec: `wo` format + `key` classification) → `fetch` (likha_sql: WO + store + customer phone check) → `fetch_updates` (likha_sql: update timeline) → `fetch_services` (likha_sql: service lines + prices) → `shape` (exec: PII-safe response).

Body: `{ "wo": "WO-2026-0001", "key": "<phone-or-token>" }`. See `public-tracking.md` for the contract.

## `easypc_unclaimed_reminder` — placeholder

| | |
|---|---|
| Trigger | `schedule` → `0 9 * * *` (daily 9am) — **inactive** |

Design note only; needs per-item iteration to email customers whose units sit in `ready_for_release` near the 30-day claim window (T&C clause 6).

## `easypc_fix_junction_relations` — one-shot repair (inactive)

Webhook + `likha_sql` op that repaired M2M junction metadata (`junction_field`, `ON DELETE CASCADE`, `files` special) after the relation-config UI crashed on this build. Kept disabled for reference — it's the pattern for DB-level fixes the REST API can't express.

## `easypc_chart_*` — dashboard chart feeds (webhook, `accountability: all`)

Six flows (`easypc_chart_intake_trend`, `easypc_chart_revenue`, `easypc_chart_status`, `easypc_chart_top_services`, `easypc_chart_branch`, `easypc_chart_parts`) backing the `EasyPC Dashboard` echarts panels. Same shape each: `likha_sql` (key `sql_1`) → `exec` (key `chart`) returning an echarts option object; `options.error_on_reject: true`. Built by `scripts/build_dashboard.py` — full SQL/panel spec in `docs/dashboard.md`.

## Gotchas learned on this instance

- **`condition` ops fail silently** — use `throw` inside `exec` ops to gate.
- **Flow-originated `items.update` doesn't reliably chain** to other flows — generate coupled values atomically in one flow (WO number + token).
- **Every loop-risk item-update needs `emitEvents: false`** — a flow that updates its own trigger collection re-fires itself.
- **`likha_sql` returns `{sql, binding, rows}`** — read `.rows`, not the whole object.
- **Postgres timestamps serialize as `{}`** through flow responses — `::text` cast in SQL.
- **Shell quoting:** never inline `python -c` with `$trigger`/`$last`/`{{...}}` in double quotes — bash eats them. Write a script file (all `scripts/*.py` follow this).
- **Cloudflare blocks the default Python UA** — always send `User-Agent: curl/8.5.0`.
- **Webhook flows fire via `GET /flows/trigger/{id}`** — POST is 403 even for admin (verified on `bis_chart_*`/`easypc_chart_*`).
- **`exec` results can't contain functions** — structured-clone 500 (`could not be cloned`); echarts formatters must be string templates.
- **Flow side effects are async** — `items.create` flows stamp fields (WO number, tracking token) after the POST responds; re-fetch before asserting.
