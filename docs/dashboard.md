# Dashboard — EasyPC Insights

Directus Insights dashboard **`EasyPC Dashboard`** (id `9267580f-5909-4377-9774-e59bd341c2f4`), modeled on the `BIS Dashboard` pattern on this instance. Built/updated by `scripts/build_dashboard.py`; demo data by `scripts/seed_dashboard_data.py`.

## Layout

Top row: 6 `metric` panels (w=8, h=9, x=1,10,19,28,37,46). Below: 6 `echarts-panel` panels in a 2×3 grid (w=27, h=22; x=1/29, y=11/33/55). All panels set `show_header: true` — the `name` renders as the panel title bar (defaults to false on API-created panels; charts also embed an echarts `title`, matching BIS).

## Metrics

| Panel | Collection | Function | Filter |
|-------|-----------|----------|--------|
| Open Work Orders | `easypc_work_orders` | count | status ∉ `released`/`cancelled`/`unclaimed` |
| Ready for Pickup | `easypc_work_orders` | count | status = `ready_for_release` |
| Awaiting Approval | `easypc_work_orders` | count | status = `awaiting_approval` |
| Customers | `easypc_customers` | count | — |
| Revenue Released | `easypc_work_orders` | sum `amount` | status = `released` |
| Bookings Ahead | `easypc_appointments` | count | `preferred_date >= $NOW`, status = `confirmed` |

## ECharts panels — flow pattern

Each `echarts-panel` stores `options.flow = {key: <flow id>, collection: 'directus_flows'}` and the panel **GETs `/flows/trigger/<id>`** (POST returns 403 on this instance). Each flow is `trigger: webhook`, `accountability: all`, `options.error_on_reject: true`, with two ops:

1. `likha_sql` (key `sql_1`) — raw SQL, resolves into the chart op.
2. `exec` (key `chart`) — returns the echarts option object. Reads `data.sql_1` (fall back to `data.$last`; unwrap `.rows`).

| Panel | Flow | SQL |
|-------|------|-----|
| Work Order Intake Trend | `easypc_chart_intake_trend` | count WOs by `date_trunc('month', date_time_in)` |
| Monthly Revenue | `easypc_chart_revenue` | `SUM(amount)` by month of `released_at`, released only |
| Work Orders by Status | `easypc_chart_status` | count by status, keys mapped to friendly labels in JS |
| Top Services | `easypc_chart_top_services` | junction → `easypc_services` count, top 10 |
| Work Orders by Branch | `easypc_chart_branch` | join `easypc_stores`, count |
| Parts Used | `easypc_chart_parts` | `SUM(qty)` by `part_type` |

## Gotchas

- **No function values in exec output.** The exec sandbox can't clone `function` properties (e.g. `valueFormatter: function(){...}` → `could not be cloned` 500). Use string templates (`'{b}: {c}'`) or precomputed strings only.
- **Charts trigger via GET**, not POST — POST `/flows/trigger/{id}` is 403 even for admin.
- Brand color `#00c853` on flows + dashboard + single-series bar/line colors.
- Panels dedupe on `(dashboard, name)`; flows dedupe on `name` — safe to rerun `build_dashboard.py`.

## Demo data

`seed_dashboard_data.py` (idempotent via `job_order_no` `JO-26-NNNN`): 66 work orders May→Oct 2026 with a realistic pipeline spread (~69% released, rest in-flight/exception), service junctions with snapshotted `charged_price`, `parts_used` line items, approvals/diagnostics for progressed WOs, plus ~25 customers and ~14 upcoming appointments.
