# EasyPC — Directus Data Model

Data model for the EasyPC work order system, derived from `EasyPC_Service_Form.docx` and the proposed six-stage service journey. **All created artifacts are prefixed `easypc_`** — collections, junctions, flows, roles — keeping the schema cleanly separated from `directus_*` system tables.

## Service journey (reference)

| Stage | Name | What happens |
|-------|------|--------------|
| 01 | Choose intake path | Wait for assessment or leave device |
| 02 | Register device | Record device, symptoms, condition & accessories |
| 03 | Assess now or later | Technician assesses when capacity is available |
| 04 | Decide | Customer approval when required by policy |
| 05 | Repair & test | Work proceeds within authorization |
| 06 | Release | Notify customer and return device |

> The **Work Order Number confirms receipt — not diagnosis or repair acceptance.** Email updates notify customers when meaningful work-order milestones or technician updates are recorded.

## Collection organization

Grouped by **change frequency** in the `EasyPC` folder:

```
EasyPC
├── easypc_operations          — transactional, touched daily
│   ├── easypc_work_orders              (1) core record
│   ├── easypc_customers                (2) new row per new customer
│   ├── easypc_work_order_updates       (3) milestones/notes
│   ├── easypc_work_order_parts_used    (4) install/charge lines
│   ├── easypc_job_processes            (5) work done
│   ├── easypc_diagnostics              (6) tests
│   ├── easypc_approvals                (7) decisions
│   ├── easypc_work_order_parts         (8) intake checklist
│   ├── easypc_work_orders_services     (9) M2M junction
│   └── easypc_work_orders_files        (10) M2M junction
├── easypc_master_data         — lookups, edited occasionally
│   ├── easypc_services                 (1) prices change
│   ├── easypc_parts_catalog            (2) SKUs/prices change
│   └── easypc_stores                   (3) branches rarely change
└── easypc_settings            — singleton config, rarely touched
```

## Collections at a glance

| Collection | Kind | Source on form | Purpose |
|------------|------|----------------|---------|
| `easypc_customers` | entity | Customer name / contact / email | Reusable customer records; one customer → many work orders |
| `easypc_stores` | lookup | Store | Branch that received the unit |
| `easypc_services` | lookup | §1 Service checkboxes | Diagnosis, Recase, Upgrade, Cleaning, PC Assembly |
| `easypc_parts_catalog` | lookup | Replacement parts sold | Current catalog price; not inventory (Odoo's job later) |
| `easypc_work_orders` | entity (core) | Header + §1 + §4 + §5 + signatures | One record from intake through release; carries status |
| `easypc_work_order_parts` | child (O2M) | §2 Parts checklist rows | One row per part type checked at intake |
| `easypc_work_order_parts_used` | child (O2M) | Parts/items installed & charged | Transactional lines — catalog pick or manual entry, price snapshot, approval link, warranty |
| `easypc_job_processes` | child (O2M) | §3 Process rows | Cleaning / Install-Upgrade / Troubleshooting coverage done |
| `easypc_diagnostics` | child (O2M) | §3 Full diagnostic rows | One row per tested area, with metrics |
| `easypc_approvals` | child (O2M) | §4 Customer informed/approved | Approval rounds (initial + additional work per T&C clause 1) |
| `easypc_work_order_updates` | child (O2M) | Email-update promise | Technician notes / milestones that trigger customer email |
| `easypc_work_orders_files` | junction (M2M) | §2 photos, signatures | Photos & attachments on a work order, with category |
| `easypc_work_orders_services` | junction (M2M) | §1 services ticked | Links work orders ↔ services; snapshots `charged_price` per order |
| `easypc_settings` | singleton | T&C / waiver text | Shop-wide settings: legal text, warranty-day policy, tracking/Jitsi URLs — read by all staff, editable by manager |

Staff references (`received_by`, `assessed_by`, `done_by`, `tested_by`, `released_by`, `recorded_by`) point to `directus_users` — no separate staff collection needed.

## Entity relationships

```mermaid
erDiagram
    easypc_customers ||--o{ easypc_work_orders : "has"
    easypc_stores ||--o{ easypc_work_orders : "receives"
    easypc_work_orders }o--o{ easypc_services : "requests"
    easypc_work_orders ||--o{ easypc_work_order_parts : "intake checklist"
    easypc_work_orders ||--o{ easypc_work_order_parts_used : "parts installed"
    easypc_parts_catalog ||--o{ easypc_work_order_parts_used : "catalog ref"
    easypc_work_orders ||--o{ easypc_work_orders : "warranty claims"
    easypc_work_orders ||--o{ easypc_job_processes : "work done"
    easypc_work_orders ||--o{ easypc_diagnostics : "tests"
    easypc_work_orders ||--o{ easypc_approvals : "decisions"
    easypc_work_orders ||--o{ easypc_work_order_updates : "notifications"
    easypc_work_orders }o--o{ directus_files : "attachments"
    directus_users ||--o{ easypc_work_orders : "staff actions"
```

## Design decisions

1. **One work order record for the whole journey.** Stages 01–06 are expressed through the `status` field plus child collections — matching the "one service record" principle.
2. **Checklist sections become child collections**, not JSON blobs on the work order, so parts, tests, and processes are queryable and reportable. The fixed option lists (part types, coverage items, diagnostic tests) stay as `select`/`json` values since the form defines them.
3. **Approval is its own collection** (`easypc_approvals`), not a field. T&C clause 1 requires written OK for extra work — multiple approval rounds per work order must be possible.
4. **`easypc_work_order_updates` is customer-facing**, distinct from `directus_activity` (internal audit). It exists to drive the promised email notifications via Flows.
5. **Prices are snapshot at transaction time.** `easypc_services` / `easypc_parts_catalog` hold *current* prices; `easypc_work_orders_services.charged_price` and `easypc_work_order_parts_used.unit_price` freeze what was charged on that work order — catalog price changes never rewrite history.
6. **Warranty is tracked per installed part** (`warranty_until` stamped at release) plus a labor warranty on the work order (`service_warranty_until`). A warranty claim is a *new* work order linked via `warranty_claim_of` — it reuses the same journey instead of a separate claims subsystem.
7. **Passwords are never stored.** `password_handling` records only the arrangement (`not_needed` / `customer_to_enter`).
8. **`job_order_no`** stores the handwritten paper form number; **`work_order_number`** is the system-generated public reference quoted in emails and used for claims.
9. **Customer is a separate collection** for dedup/history; create-or-match by contact number or email at intake.
10. **Multi-branch ready.** `store` on every work order + `easypc_store` on `directus_users`; non-manager roles are permission-filtered to their branch, `easypc_manager` sees all. `store.code` can prefix WO numbers for per-branch sequences.

## Configuration notes

- **Timestamps are system-generated.** `date_time_in`, `assessed_at`, `terms_accepted_at`, `informed_at`, `decided_at`, `done_at`, `tested_at`, `notification_sent_at` use a real Postgres `CURRENT_TIMESTAMP` default (API value `now()`) and are readonly. Milestone stamps (`released_at`, `service_warranty_until`, `warranty_until`) are readonly and set by `easypc_warranty_stamp`, never typed.
- **Print interface.** `easypc_work_orders.print` is an alias field, `interface: "print"`, bound to `print_template` row `easypc_work_order_form` (id `3f63e917-44de-4dbe-ae08-cd58617ba9da`), `fields: ["*.*.*"]`. Template source: `scripts/easypc_work_order_form.liquid` (LiquidJS; edit there, re-upload). **The template body field is `code` (text, `input-code` interface) — not `content`.** PATCHing `content` returns 200 but silently ignores the body — always PATCH `{"code": <template>}` and verify by reading `code` back. Verify interface names against UI-created fields — `likha-print-template` is the legacy registration.
- **Tracking QR on print.** Rendered as `<img src="https://api.qrserver.com/...">` encoding `tracking_url/?wo=<WO>` — scanning opens the tracker with the WO number pre-filled; customer just enters their registered mobile. No token printed on paper. Requires `img-src` CSP to allow the host — server currently runs permissive `img-src 'self' data: blob: http: https:` via `CONTENT_SECURITY_POLICY_DIRECTIVES__IMG_SRC`. The `genqr → qreq → b64 → setqr` flow ops still populate `tracking_qr` (data-URI fallback) but the template doesn't use it; the ops can be removed if external URL rendering is settled.
- **`video_call_link`** — readonly, generated by `easypc_video_link` at `in_repair`; `https://meet.jit.si/easypc-<wo>-<rand8>`. Never regenerates on rework.
- **`tracking_token`** — hidden readonly, generated with the WO number; accepted as a public lookup key alongside the customer phone.
- **Signatures stay on paper** — no digital signature fields; the printed form is the legal copy.

## Files in this folder

- `data-model.md` — full field-by-field spec for every collection
- `workflow.md` — status lifecycle ↔ journey mapping, notifications, roles, implementation notes
- `flows.md` — every `easypc_*` flow: triggers, operation chains, behavior, instance gotchas
- `roles-and-access.md` — roles, policies, permission matrix, branch scoping, test accounts
- `public-tracking.md` — customer tracker: API contract, security model, frontend, deployment
- `design-system.md` — EasyPC branding: color tokens (dark screen theme + light print theme), typography, components, status colors

## Public tracking page (`tracker/`)

Customer-facing repair tracker (LBC/Shopee-style), no account needed — see `public-tracking.md`.

- **URL:** `https://trinly01.github.io/EasyPC/` — customer enters **WO number + registered mobile number** (full or last 4 digits). The random `tracking_token` still works as a fallback key.
- **Data path:** POST to the `easypc_track_lookup` webhook flow (`/flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70`). Validates WO+key, queries via `likha_sql` server-side, returns a PII-safe payload. **No public collection read permissions** — enumeration impossible.
- **Stack:** Vite + React 19 + Tailwind 4 + shadcn-style components; dark theme, EasyPC green. Deploys to GitHub Pages via `.github/workflows/deploy-pages.yml`.
- **SPA routing:** `public/404.html` fallback gives clean URLs on Pages.
