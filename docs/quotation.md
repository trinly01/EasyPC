# EasyPC Service Work Order System — Modules & Quotation

Prepared for: **EasyPC**
Platform: Directus 11 (self-hosted) + React public tracker
Status legend: ✅ delivered · 🔧 partial · 📋 proposed

---

## Module inventory

### Phase 1 — Core Service Platform (delivered)

| # | Module | What it includes | Status |
|---|--------|------------------|--------|
| M1 | **Data model & schema** | 14 `easypc_*` collections mirroring the paper service form — work orders, customers, intake parts checklist, processes, diagnostics, approvals, parts-used lines, updates, junctions for services/files. Snapshot pricing (charged price frozen per transaction). Warranty fields per part + labor warranty. | ✅ |
| M2 | **Multi-branch RBAC** | 3 roles (front desk / technician / manager), branch-scoped permission filters (`$CURRENT_USER.easypc_store`), append-only customer-update log, print-template read, app access. Test accounts per role. | ✅ |
| M3 | **Workflow automation (Flows)** | `WO-YYYY-NNNN` numbering + tracking token; status milestone → customer update rows; release stamping (`released_at` + 30-day service warranty); loop-safe wiring. | ✅ |
| M4 | **Printable service form** | LiquidJS template bound to `print_template`; branded light layout matching the paper form; T&C/waiver text + tracking instructions; print button on the work order. | ✅ |
| M5 | **Email notifications** | `notify_customer` update → SMTP email via Titan/GoDaddy; `notification_sent_at` stamping; milestone + technician-note messages. | ✅ |
| M6 | **Live video transparency** | Auto-generated Jitsi room per WO at `in_repair`/`testing`; stable link reused on rework loops; "watch the actual work" customer message; Join button on tracker + printed form. | ✅ |
| M7 | **Public tracking portal** | Unauthenticated LBC-style tracker: `WO number + mobile (or token)` lookup; webhook flow returns PII-safe payload only (no public collection reads); journey timeline, warranty, video link, services/prices. React 19 + Vite + Tailwind + shadcn-style, GitHub Pages deploy, SPA clean routes. | ✅ |
| M8 | **Settings & legal versioning** | `easypc_settings` singleton — T&C/waiver text, warranty-day policy, tracking/Jitsi URLs, support contacts; per-WO `terms_snapshot`/`waiver_snapshot`/`terms_version` frozen at intake + live `settings` M2O. | ✅ |
| M9 | **Seed data & docs** | Realistic stores/services/parts/customers/WOs at every journey stage; full docs set (data model, flows, RBAC, tracking, design system). | ✅ |

### Phase 2 — Hardening & rollout (proposed)

| # | Module | Scope | Status |
|---|--------|-------|--------|
| M10 | **Production readiness** | `CORS_ORIGIN` for Pages origin; staff password policy; production domain for tracker (e.g. `track.easypc.com.ph`); backup/restore runbook | 🔧 pending |
| M11 | **QR intake** | Print tracking QR (WO + token deep link) on the service form | 📋 |
| M12 | **Public-message curation** | `public_message` field on updates so internal notes never leak to the tracker | 📋 |
| M13 | **Abuse protection** | Rate-limit the lookup webhook; optional last-4→full-phone policy | 📋 |
| M14 | **Unclaimed reminders** | Scheduled flow: units in `ready_for_release` past `unclaimed_days` → reminder email → auto-flag | 📋 (flow stub exists) |
| M15 | **Delivery assurance** | `email_status` field (sent/failed), retry on failure; branded HTML email template | 📋 |
| M16 | **Branded email** | EasyPC design-system HTML email (green header, status card, tracking CTA) | 📋 |

### Phase 3 — Integrations (proposed)

| # | Module | Scope | Status |
|---|--------|-------|--------|
| M17 | **Odoo integration** | `odoo_ticket` free-text → live link/sync: SO numbers, parts pricing/inventory, customer dedup | 📋 |
| M18 | **SMS notifications** | SMS provider (Semaphore/Twilio) alongside email for milestones | 📋 |
| M19 | **Customer portal v2** | Approval actions from tracking page (approve/decline extra work), photo galleries, PDF download | 📋 |

---

## Effort & quotation

Rate basis: **₱15,000 / developer-day** (adjust to your actual rate — totals recompute linearly).

### Phase 1 — delivered scope

| Module | Est. days | Amount |
|--------|-----------|--------|
| M1 Data model & schema | 3.0 | ₱45,000 |
| M2 Multi-branch RBAC | 2.0 | ₱30,000 |
| M3 Workflow flows | 3.0 | ₱45,000 |
| M4 Print template & interface | 1.5 | ₱22,500 |
| M5 Email notifications | 1.0 | ₱15,000 |
| M6 Video transparency | 1.0 | ₱15,000 |
| M7 Public tracking portal | 4.0 | ₱60,000 |
| M8 Settings & legal versioning | 1.0 | ₱15,000 |
| M9 Seed data & documentation | 1.5 | ₱22,500 |
| **Phase 1 total** | **18.0** | **₱270,000** |

### Phase 2 — hardening & rollout

| Module | Est. days | Amount |
|--------|-----------|--------|
| M10 Production readiness | 1.0 | ₱15,000 |
| M11 QR intake | 0.5 | ₱7,500 |
| M12 Public-message curation | 0.5 | ₱7,500 |
| M13 Abuse protection | 0.5 | ₱7,500 |
| M14 Unclaimed reminders | 1.0 | ₱15,000 |
| M15 Delivery assurance | 0.5 | ₱7,500 |
| M16 Branded email template | 0.5 | ₱7,500 |
| **Phase 2 total** | **4.5** | **₱67,500** |

### Phase 3 — integrations (indicative, needs discovery)

| Module | Est. days | Amount |
|--------|-----------|--------|
| M17 Odoo integration | 5–8 | ₱75,000–120,000 |
| M18 SMS notifications | 1–2 | ₱15,000–30,000 |
| M19 Customer portal v2 | 3–5 | ₱45,000–75,000 |

---

## Terms & assumptions

- **Client provides:** Directus hosting, domain, email account (Titan/GoDaddy), Odoo access for M17, paper-form sign-off on T&C wording.
- **Not included:** hosting costs, SMS/email provider fees, Jitsi hosting (public meet.jit.si used; self-host optional), on-site training.
- **Change requests:** priced at the same day rate.
- **Suggested payment:** 40% mobilization · 40% on Phase 1 UAT sign-off · 20% on go-live.
- **Warranty:** 30 days bug-fix warranty post go-live; enhancements billed separately.
- **Maintenance retainer (optional):** ₱10,000/mo — monitoring, minor adjustments, monthly backup verification.
