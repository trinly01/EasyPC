# Roles, Policies & Access Control

## Staff roles

Three app roles, each bound to a same-named policy:

| Role | Policy | Purpose |
|------|--------|---------|
| `easypc_front_desk` | `easypc_front_desk_policy` | Intake: customers, work orders, intake parts checklist, releasing, files |
| `easypc_technician` | `easypc_technician_policy` | Assessment→testing: job processes, diagnostics, approvals, parts used, updates |
| `easypc_manager` | `easypc_manager_policy` | Full access, all branches, status overrides, lookups admin |

## Permission model

All scoped collections use the **branch filter** so staff only see their own store's queue:

- Work orders: `{"store": {"_eq": "$CURRENT_USER.easypc_store"}}`
- O2M children (parts, processes, diagnostics, approvals, parts_used, updates): `{"work_order": {"store": {"_eq": "$CURRENT_USER.easypc_store"}}}`
- M2M junctions (services, files): `{"easypc_work_orders_id": {"store": {"_eq": "$CURRENT_USER.easypc_store"}}}`
- The user's branch comes from `directus_users.easypc_store` (M2O → `easypc_stores`)
- `easypc_manager` perms carry **no filter** — sees all branches

## Permission matrix

| Collection | front_desk | technician | manager |
|---|---|---|---|
| `easypc_customers` | CRUD | read | CRUD |
| `easypc_work_orders` | CRUD (branch) | read+update (branch) | CRUD (all) |
| `easypc_work_order_parts` (intake) | CRUD (branch) | read (branch) | CRUD |
| `easypc_work_order_parts_used` | CRUD (branch) | CRUD (branch) | CRUD |
| `easypc_job_processes` | read (branch) | CRUD (branch) | CRUD |
| `easypc_diagnostics` | read (branch) | CRUD (branch) | CRUD |
| `easypc_approvals` | CRUD (branch) | CRUD (branch) | CRUD |
| `easypc_work_order_updates` | **create + read only** (branch) | **create + read only** (branch) | CRUD — incl. edit/delete |
| `easypc_work_orders_services` (M2M) | CRUD (branch) | CRUD (branch) | CRUD |
| `easypc_work_orders_files` (M2M) | CRUD (branch) | CRUD (branch) | CRUD |
| `easypc_stores` / `easypc_services` / `easypc_parts_catalog` | read | read | CRUD |
| `directus_users` / `directus_files` / `directus_folders` | read / files RW | read / files RW | read / files RW |

Key points:

- **Updates are append-only** for front desk and technicians (create + read, no update/delete) — the customer-notification log can't be rewritten. Only managers can edit/delete.
- **`create` perms are unfiltered** (branch can't be known until the row exists); `read`/`update`/`delete` are branch-scoped. Front-desk create presets `store` to the user's branch.
- Everyone can read lookups (`stores`, `services`, `parts_catalog`, `customers`) — they're needed to fill forms.

## Test accounts (playground only)

| Email | Role | Branch | Password |
|---|---|---|---|
| `myla+front_desk@easypc.com` | `easypc_front_desk` | GIL | = email |
| `myla+technician@easypc.com` | `easypc_technician` | GIL | = email |
| `myla+manager@easypc.com` | `easypc_manager` | GIL (sees all) | = email |

> ⚠️ Passwords equal emails — **playground only, change before production.**

## Public (unauthenticated) access

**No public read permissions on any `easypc_*` collection.** The only public surface is the `easypc_track_lookup` webhook flow, which runs with full internal permissions (`likha_sql`) and returns a hand-shaped, PII-safe payload. Details in `public-tracking.md`.

## Auditability

Every collection carries `user_created` / `date_created` / `user_updated` / `date_updated`. Staff attribution fields (`received_by`, `assessed_by`, `done_by`, `tested_by`, `released_by`, `recorded_by`, `created_by`) are `directus_users` references — populated by the person performing the action, never the customer.
