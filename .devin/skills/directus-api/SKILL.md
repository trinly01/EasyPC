# Directus API — EasyPC on likha-playground

Project skill for working with the EasyPC Directus instance. Read before any Directus API work.

## Instance

- URL: `https://likha-playground.zyberlab.com` — Directus **11.17.4**, project "LikhaERP"
- **Shared playground**: 100+ collections belonging to other projects. NEVER touch anything not prefixed `easypc_`. Every artifact we create (collections, junctions, flows, roles, policies) is prefixed `easypc_`.
- Token: admin bearer token provided by user (kept in env var `DIRECTUS_TOKEN`, never committed).

## Hard-won rules (each one came from a real failure)

1. **Cloudflare blocks non-curl user agents.** Default `Python-urllib/*` and spoofed browser UAs get `403 error code: 1010` on writes. Always send `User-Agent: curl/8.5.0` (urllib/requests) or use `curl` directly. GETs are unaffected.
2. **NEVER PATCH `/relations` — it crashes this server.** Any `PATCH /relations/{collection}/{field}` (even correct, verified) enters `RelationsService.alterType` → `schema.collections[...].fields` → TypeError → process crash; nodemon does NOT auto-restart (needs `rs`). POST /relations is safe. To change relation behavior post-creation, use SQL directly (see below) or recreate the relation.
3. **Missing-field GETs return 403, not 404.** `GET /fields/{col}/{missing}` → 403 FORBIDDEN, so don't treat non-200 as "doesn't exist". For existence checks list `/fields/{col}` and search, or just POST and tolerate 400.
4. **M2M junction deletes**: `one_deselect_action` can't be PATCHed (rule 2). Options: (a) delete junction rows before the parent, or (b) DB-level cascade + meta fix via SQL:
   ```sql
   ALTER TABLE easypc_work_orders_services DROP CONSTRAINT easypc_work_orders_services_easypc_work_orders_id_foreign,
     ADD CONSTRAINT easypc_work_orders_services_easypc_work_orders_id_foreign FOREIGN KEY (easypc_work_orders_id) REFERENCES easypc_work_orders(id) ON DELETE CASCADE;
   ALTER TABLE easypc_work_orders_files DROP CONSTRAINT easypc_work_orders_files_easypc_work_orders_id_foreign,
     ADD CONSTRAINT easypc_work_orders_files_easypc_work_orders_id_foreign FOREIGN KEY (easypc_work_orders_id) REFERENCES easypc_work_orders(id) ON DELETE CASCADE;
   UPDATE directus_relations SET one_deselect_action='delete'
     WHERE many_collection IN ('easypc_work_orders_services','easypc_work_orders_files') AND many_field='easypc_work_orders_id';
   ```
5. **URL-encode filter params.** `?filter[key][_eq]=x` with raw brackets intermittently fails through the proxy; always encode (`filter%5Bkey%5D%5B_eq%5D`).
6. **Reverse O2M aliases are created by `meta.one_field`** on the relation POST — then PATCH `/fields/{col}/{alias}` to set `interface: list-o2m`, options template, and `group` for tab placement. M2M needs `junction_field` on the junction→parent relation + patch the alias to `interface: list-m2m` / `files`.
7. **group-tabs is native** (≥11.17.1). Group fields are `type: alias`, `special: ["alias","group","no-data"]`; children point at parent via `meta.group`. Set `meta.translations` for tab labels.
8. **Multi-branch is implemented.** `directus_users.easypc_store` (M2O → `easypc_stores`) assigns each staff user a branch; `easypc_front_desk`/`easypc_technician` permissions filter `easypc_work_orders` to `$CURRENT_USER.easypc_store` (children via `work_order.store`, junctions via `easypc_work_orders_id.store`); front-desk creates preset `store` to their branch. `easypc_manager` is unfiltered — sees all branches.
9. **Audit-field relations are NOT auto-created.** `user_created`/`user_updated`/`date_*` fields save values on collection create, but the M2O relation to `directus_users` must be POSTed manually — otherwise the field stores a UUID it can't resolve (part of "relationship not configured" errors). Created for all 11 entity collections on 2026-10-17.
10. **Junction FK fields must not be `hidden`** — hiding `easypc_work_orders_id`/`easypc_services_id`/`directus_files_id` breaks the `list-m2m`/`files` interface ("relationship not configured" error).
11. **`$CURRENT_USER` is NOT a valid `schema.default_value`** (500 invalid uuid). Default-to-logged-in-user goes in permission **presets**: `presets: {"created_by": "$CURRENT_USER"}` on each role's create permission. Done for created_by/recorded_by/done_by/tested_by/received_by (+ `store` on WOs). `$CURRENT_USER.easypc_store` works in presets/filters too.
12. **`easypc_work_order_updates` is append-only** for front_desk/technician (update+delete perms removed; manager keeps all). `created_by` is readonly+preset; `notification_sent_at` readonly (flow-stamped after send, blank = pending).
13. **`condition` flow op silently fails here — gate inside `exec` instead.** An op that `throw`s routes to `reject` (null) and stops the chain cleanly; verified working. Also: operation `resolve`/`reject` are **unique** — two ops can't resolve to the same target; clear the existing link first. `$trigger` shape for items.update = `{payload: {changedFields}, keys: [ids], collection, event}` — `payload` is NOT double-nested.
14. **Collection folders**: `EasyPC` is a group folder (collection with `schema: null`); membership = `PATCH /collections/{name} meta.group="EasyPC"`. All 13 `easypc_*` collections are inside it.
15. **Working flows** (`scripts/build_flows.py`): `easypc_generate_wo_number` (verified: auto WO-YYYY-NNNN on create), `easypc_status_milestone` (verified), `easypc_warranty_stamp` (verified: +30d on released), `easypc_notify_on_update` (mail op needs `EMAIL_*` env on server — untested), `easypc_unclaimed_reminder` (disabled placeholder).
17. **Bash `$` expansion corrupts flow options.** `python -c "... $last ..."` inside double quotes silently strips `$trigger`/`$last`/`$full` → stored as `data. || {}`, `{{.key}}`, `permissions:""` → flow silently dies. ALWAYS write/patch ops containing `$` tokens via a script file (see `scripts/fix_warranty_flow.py`), never inline `python -c "..."`. Verify stored options after patching.
18. **`item-update` op `key` field**: use literal or `{{$last.key}}`/`{{$trigger.keys[0]}}` — both resolve here. Always set `emitEvents: false` on ops that write back to the trigger collection (every working op on this instance does; prevents self-trigger loops).
19. **Print field interface is `print`, not `likha-print-template`** — `procurement_plan.print` uses the legacy name; the UI picker registers `print`. Options shape: `{templateSelection: {collection: "print_template", key: "<template-row-uuid>"}, fields: ["*.*.*"]}`. Templates (`print_template` rows) are LiquidJS HTML; `scripts/easypc_work_order_form.liquid` = local source of `easypc_work_order_form` (id 3f63e917-44de-4dbe-ae08-cd58617ba9da). Terminal output can clip UUIDs — always re-fetch real ids by name before writing them into options.
20. **`likha_sql` custom op exists** — runs raw SQL server-side (`options.sql`, multi-statement OK). The sanctioned way to change things the crashing `/relations` PATCH can't (junction_field, deselect actions, FK cascades). Fire it via a **webhook-triggered** flow + `POST /flows/trigger/{id}` — `manual` trigger 403s via API. Used to fix M2M `junction_field` on both junction relations (both sides must point at each other's field — missing second side = "relationship not configured" in app) + `ON DELETE CASCADE`. `POST /utils/cache/clear {"cache":"system"}` refreshes schema after direct-DB changes. (Webhook flows fire via `GET /flows/trigger/{id}` — POST 403s; see rule 21.)
21. **echarts-panel pattern (dashboards)**: `directus_panels` rows `type: 'echarts-panel'` store `options: {flow: {key: <flow-id>, collection: "directus_flows"}}`. The panel **GETs `/flows/trigger/{id}`** — POST returns 403 even for admin (observed on `bis_chart_*` and `easypc_chart_*`). Flow shape: `trigger: webhook`, `accountability: all`, `options.error_on_reject: true`; ops: `likha_sql` (key `sql_1`, `options.sql`) → `exec` (key `chart`) returning the echarts option object. In exec, rows = `data.sql_1` (unwrap `.rows`). **Exec output can't contain functions** — `formatter`/`valueFormatter` functions → `could not be cloned` 500; use string templates (`'{b}: {c}'`). Built by `scripts/build_dashboard.py`; see `docs/dashboard.md`.
22. **Interface `readonly` ≠ API-immutable.** `date_time_in` (readonly + CURRENT_TIMESTAMP default) accepts explicit values on POST/PATCH with the admin token — how `seed_dashboard_data.py` backdates WOs across months. Same for `released_at`, `amount`, `service_warranty_until`.
23. **Flow effects are async — don't assert on the POST response.** `easypc_generate_wo_number` fires on `items.create`, but the POST returns `work_order_number: null`; number + `tracking_token` appear a few seconds later. Re-fetch before verifying.
24. **Creating at final status bypasses update-triggered flows.** `easypc_status_milestone`, `easypc_video_link`, `easypc_warranty_stamp` all trigger on `items.update` — POST `status:'released'` fires only `items.create` flows (numbering). For seeded/released WOs set `released_at`, `service_warranty_until`, `amount`, `test_result` explicitly in the payload; nothing stamps them for you.
25. **Metric panel options**: `{collection, field, function: count|sum|avg|min|max, sortField, filter}` — `filter` is a normal Directus filter object and **`$NOW` works** (verified: `preferred_date _gte $NOW` on `easypc_appointments`). `/items/{coll}?aggregate[count]=id&aggregate[sum]=amount` honors the same filters — handy for pre-verifying a metric's number.
26. **No dedupe on `/panels`, `/dashboards`, `/flows`, `/operations`.** Repeat POSTs create duplicates — always GET-filter by name (+dashboard for panels) before creating. Chain order: POST ops (tail first, `resolve`→next op id), then PATCH `flow.operation` = first op id.
27. **Windows shell gotchas (this repo's box):** Windows Python reads files as cp1252 — JSON fetched via curl needs `open(..., encoding='utf-8')` or it dies on smart quotes. `/tmp` isn't shared between Git Bash and Windows `python` — write scratch files into the repo dir and clean up.

## What exists (built 2026-10-17, script: `scripts/build_schema.py`)

13 collections: `easypc_stores`, `easypc_services`, `easypc_parts_catalog`, `easypc_customers`, `easypc_work_orders` (+ `grp_tabs` 7-tab layout), `easypc_work_order_parts`, `easypc_work_order_parts_used`, `easypc_job_processes`, `easypc_diagnostics`, `easypc_approvals`, `easypc_work_order_updates`, junctions `easypc_work_orders_services` (with `charged_price` snapshot) and `easypc_work_orders_files`.

Roles/policies: `easypc_front_desk`, `easypc_technician`, `easypc_manager` (+ `*_policy`).

Dashboards: `EasyPC Dashboard` (id `9267580f-5909-4377-9774-e59bd341c2f4`) — 6 metric + 6 echarts-panel panels; chart flows `easypc_chart_*` (`scripts/build_dashboard.py`, `docs/dashboard.md`). Demo seed: `scripts/seed_dashboard_data.py`.

Design spec: `docs/data-model.md`, `docs/workflow.md`, `docs/README.md`.
