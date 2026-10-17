# Workflow — Statuses, Notifications, Roles

## Status lifecycle

`easypc_work_orders.status` drives the journey. Suggested values:

| Status | Journey stage | Meaning | Set when |
|--------|---------------|---------|----------|
| `registered` | 02 Register device | Intake complete; WO number issued (receipt only) | Work order created |
| `awaiting_assessment` | 03 Assess now or later | Queued for a technician (leave-device path) | `intake_path = leave_device` |
| `assessing` | 03 | Technician actively diagnosing | Tech opens diagnostics |
| `awaiting_approval` | 04 Decide | Findings / estimate sent to customer | `easypc_approvals` row created, `decision = pending` |
| `approved` | 04 | Customer authorized the work | Approval `decision = approved` |
| `declined` | 04 | Customer declined; unit goes back | Approval `decision = declined` |
| `in_repair` | 05 Repair & test | Authorized work in progress | Approval granted / job processes started |
| `testing` | 05 | Work done; unit in boot/stress verification | Tech starts §5 test run |
| `ready_for_release` | 05→06 | Boot test passed; customer notified to claim | `test_result = passed` |
| `released` | 06 Release | Unit returned; record complete | `released_at` set |
| `cancelled` | — | Cancelled before completion | Manual |
| `unclaimed` | — | 30-day claim window lapsed (T&C clause 6) | Manual / scheduled flow |

Transitions worth automating (Flows):

- `approved` → `in_repair`: when first `easypc_job_processes` row is saved.
- `in_repair` → `testing`: when the tech starts the §5 Test Run / Boot Test.
- `testing` → `ready_for_release`: when `test_result = passed`.
- `testing` → `in_repair`: when `test_result = failed` (rework loop — trackable).
- `testing` → `awaiting_approval`: when testing surfaces additional findings needing customer OK (§4 "Additional findings (testing)" + T&C clause 1).
- `declined` → `ready_for_release`: decline still ends in release (assessment-only or untouched unit).
- `ready_for_release` → `released`: when `released_at` + `receiver_name` are filled.

## Customer email updates

Promise on the journey card: email on *meaningful milestones or technician updates*. Implementation:

All flows are prefixed `easypc_` per the naming convention — full operation chains in `flows.md`. **Implemented:**

1. **`easypc_notify_on_update`** ✅ — `items.create` on `easypc_work_order_updates` (notify=true) → read customer email → send mail → stamp `notification_sent_at`. *Requires `EMAIL_*` env on the server for mail op.*
2. **`easypc_status_milestone`** ✅ verified — `items.update` on `easypc_work_orders` where status → notifiable (`awaiting_approval`, `ready_for_release`, `released`) → auto-create update row → flow 1 sends. `testing` is excluded — owned by the video flow.
3. **`easypc_generate_wo_number`** ✅ verified — `items.create` → assigns `WO-YYYY-NNNN` + `tracking_token` atomically.
4. **`easypc_warranty_stamp`** ✅ verified — status → `released` → stamps `released_at` + `service_warranty_until` = +30d.
5. **`easypc_video_link`** ✅ verified — status → `in_repair`/`testing` → generates (once) or reuses the Jitsi room link + posts a `notify_customer` update. Loop-safe; link is stable for the WO's life.
6. **`easypc_track_lookup`** ✅ verified — webhook endpoint powering the public tracker; see `public-tracking.md`.
7. **`easypc_unclaimed_reminder`** — disabled placeholder; needs per-item iteration design.

Flow caveat on this instance: the `condition` operation fails silently — gating is done inside `exec` ops via `throw` instead.

Do not email on internal-only changes (`assessing`, `in_repair` progress notes) unless staff explicitly create a `technician_note` update.

## Roles & permissions (implemented)

| Role | Access |
|------|--------|
| `easypc_front_desk` (RA-TECH) | Create/edit work orders intake fields, customers, parts checklist, releasing group, files |
| `easypc_technician` | Edit `assessing` onward: processes, diagnostics, findings, approvals (record), updates |
| `easypc_manager` | Full + status overrides, `cancelled`/`unclaimed`, T&C version |
| Customer | No app login — email updates + the public tracker (`public-tracking.md`) |

Full permission matrix → `roles-and-access.md`.

**Multi-branch (implemented):** `directus_users.easypc_store` assigns each staff user a home branch. `easypc_front_desk` and `easypc_technician` permission filters scope `easypc_work_orders` to `$CURRENT_USER.easypc_store` — children via `work_order.store`, junctions via `easypc_work_orders_id.store` — so each branch only sees its own queue; front-desk creates auto-preset `store` to their branch. `easypc_manager` is unfiltered and sees all branches. Add `store.code` to the WO number format for per-branch sequences.

## Work order number

Generate in Flow `easypc_generate_wo_number` on `items.create` of `easypc_work_orders`: format `{store.code}-WO-{YYYY}-{seq}` or plain `WO-{YYYY}-{seq}` using an incrementing counter (store last sequence in project settings or a tiny `easypc_counters` collection). Keep `job_order_no` as the free-typed paper reference — do not merge them; the paper number may be illegible, duplicated, or missing.

## Parts, pricing & warranty

- **Additional items mid-repair** (replacement parts, consumables, misc charges): create `easypc_work_order_parts_used` rows — either picked from `easypc_parts_catalog` (price auto-copies, editable) or typed manually (`catalog_item` empty, `price_source = manual`). Each row saves the price *at that time* — the transaction is permanent regardless of later catalog edits. Lines needing customer OK link to an `easypc_approvals` row with `kind = additional_work` via their `approval` field; status goes `in_repair`/`testing` → `awaiting_approval` until decided (T&C clause 1 — nothing proceeds on unapproved lines).
- **`amount` at release** ≈ `Σ services.charged_price + Σ parts_used.(qty × unit_price)`. A Flow can pre-fill `amount` or warn when the SO total differs — keep `amount` staff-editable since the SO is authoritative.
- **Warranty stamping at release:** when `status → released`, a Flow sets `parts_used.warranty_until = released_at + warranty_days` per line and `service_warranty_until` on the work order (labor warranty per shop policy). Customer-supplied parts get `warranty_provider = seller`, `warranty_days = 0` (T&C clause 5).
- **Warranty claim intake:** customer returns within warranty → create a new work order with `warranty_claim_of` = the original. Front desk can verify coverage by checking `warranty_until` on the original's parts. The claim follows the normal journey; warranty-covered work can be priced ₱0 on its line items.

## Field-group layout for the app

The work order detail page uses a **`group-tabs`** interface (native since Directus 11.17.1; older versions need the `directus-extension-group-tabs-interface` extension or `group-accordion` fallback). `work_order_number` and `status` stay at top level; everything else sits in journey-ordered tabs — full spec in `data-model.md` → *App layout — groups & tabs*:

`grp_intake` → `grp_unit` → `grp_parts` → `grp_assessment` → `grp_work` → `grp_releasing` → `grp_updates`

## Open questions to confirm

None outstanding.

Resolved:

- `services` stays M2M to the `easypc_services` lookup. The junction `easypc_work_orders_services` carries `charged_price` — a snapshot of the price at the time of the work order (editable per order for discounts), so price updates to the catalog never alter historical records.
- `odoo_ticket` stays free-text for now; design allows a future Odoo integration (sync or link) without schema change.
- No receiver or customer signature fields — releasing and T&C consent are signed on the printed paper form, which remains the legal copy.
