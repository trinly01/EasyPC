# Flows — Automation Reference

All EasyPC flows are prefixed `easypc_`. Flows run with `accountability: all` unless noted. Gating is done inside `exec` ops with `throw` — the `condition` op is unreliable on this build. Item writes that would re-trigger `items.update` listeners use `emitEvents: false` to stay loop-safe.

## `easypc_generate_wo_number` — numbering + tracking token

| | |
|---|---|
| Trigger | `event` → `items.create` on `easypc_work_orders` |
| ID | `44615a57-1342-406e-947e-653e964809f8` |

`count` (item-read: count WOs) → `format` (exec: build `WO-YYYY-NNNN` + random `tracking_token`) → `setnum` (item-update: writes both fields, `emitEvents: false`).

- `work_order_number` — `WO-2026-0001` style, count-based sequence
- `tracking_token` — 16-char random alnum, hidden readonly field; still accepted as a lookup key for the public tracker (backward compat for already-printed forms/links)

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

Notifiable statuses: `awaiting_approval`, `ready_for_release`, `released` (+ others in map). `testing` intentionally removed — owned by `easypc_video_link`.

## `easypc_notify_on_update` — customer email

| | |
|---|---|
| Trigger | `event` → `items.create` on `easypc_work_order_updates` |
| ID | `f35b531b-b194-4e0e-87e2-ce5845b60840` |

`check` (exec: `notify_customer` flag set?) → `readupd` (item-read: update + WO + customer) → `buildmail` (exec: subject/body) → `gate` → `sendmail` (mail op) → `stampsent` (item-update: `notification_sent_at`, `emitEvents: false`).

> Requires `EMAIL_*` env vars on the Directus host; until configured the update rows still log and appear on the tracker.

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

## Gotchas learned on this instance

- **`condition` ops fail silently** — use `throw` inside `exec` ops to gate.
- **Flow-originated `items.update` doesn't reliably chain** to other flows — generate coupled values atomically in one flow (WO number + token).
- **Every loop-risk item-update needs `emitEvents: false`** — a flow that updates its own trigger collection re-fires itself.
- **`likha_sql` returns `{sql, binding, rows}`** — read `.rows`, not the whole object.
- **Postgres timestamps serialize as `{}`** through flow responses — `::text` cast in SQL.
- **Shell quoting:** never inline `python -c` with `$trigger`/`$last`/`{{...}}` in double quotes — bash eats them. Write a script file (all `scripts/*.py` follow this).
- **Cloudflare blocks the default Python UA** — always send `User-Agent: curl/8.5.0`.
