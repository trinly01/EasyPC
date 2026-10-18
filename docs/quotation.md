# EasyPC Service Work Order System — Proposal & Quotation

Prepared for: **EasyPC**
Platform: **Likha ERP** (Directus 11 core) + React public tracker on GitHub Pages
Delivery model: Likha hybrid — implementation sprints + Cloud subscription

---

## Project team

| Role | Headcount | Responsibility on this project |
|------|-----------|-------------------------------|
| **Business Analyst** | 1 | Paper-form → data-model mapping, workflow mapping, T&C/legal text, UAT scripts, client sign-off |
| **Developer** | 1 | Collections, flows, RBAC, print template, tracker app, integrations |
| **QA** | 1 | Role-permission test matrix, flow verification, security checks (public API), tracker E2E, regression |
| **Project Manager** | 1 | Schedule, client comms, sprint planning, deployment coordination, acceptance |

## Module inventory

### Phase 1 — Core Service Platform (delivered)

| # | Module | Scope | Status |
|---|--------|-------|--------|
| M1 | Data model & schema | 14 `easypc_*` collections mirroring the paper form; snapshot pricing; per-part + labor warranty fields | ✅ |
| M2 | Multi-branch RBAC | 3 roles, branch-scoped filters, append-only updates log, test accounts | ✅ |
| M3 | Workflow automation | WO numbering + token, milestone updates, release/warranty stamping, loop-safe flows | ✅ |
| M4 | Printable service form | LiquidJS template, EasyPC-branded light layout, print interface | ✅ |
| M5 | Email notifications | `notify_customer` → Titan SMTP, milestone + technician notes | ✅ |
| M6 | Video transparency | Jitsi room per WO at `in_repair`/`testing`, stable link, customer messaging | ✅ |
| M7 | Public tracking portal | WO + mobile lookup, PII-safe webhook flow, journey timeline, GitHub Pages | ✅ |
| M8 | Settings & legal versioning | `easypc_settings` singleton; per-WO T&C/waiver snapshots; live settings M2O | ✅ |
| M9 | Seed data & documentation | Realistic multi-branch data; 7 doc files | ✅ |

### Phase 2 — Hardening & rollout (proposed)

| # | Module | Scope |
|---|--------|-------|
| M10 | Production readiness | CORS origin, production tracker domain, password policy, backup runbook |
| M11 | QR intake | Tracking QR printed on the service form |
| M12 | Public-message curation | `public_message` field — internal notes never reach the tracker |
| M13 | Abuse protection | Rate-limit lookup webhook |
| M14 | Unclaimed reminders | Scheduled flow: `ready_for_release` past claim window → email + flag |
| M15 | Delivery assurance | `email_status` sent/failed + retry; stop stamping on failed sends |
| M16 | Branded email | EasyPC HTML email template (design system) |

### Phase 3 — Integrations (proposed, needs discovery)

| # | Module | Scope |
|---|--------|-------|
| M17 | Odoo integration | `odoo_ticket` → live link/sync: SO numbers, parts inventory/pricing, customer dedup |
| M18 | SMS notifications | Semaphore/Twilio alongside email for milestones |
| M19 | Customer portal v2 | Approve/decline from tracker, photo galleries, PDF download |

---

## Effort by role — Phase 1 (delivered)

| Role | Rate/day | Days | Amount |
|------|----------|------|--------|
| Developer | ₱3,000 | 18 | ₱54,000 |
| QA | ₱2,500 | 6 | ₱15,000 |
| Business Analyst | ₱3,000 | 4 | ₱12,000 |
| Project Manager | ₱3,500 | 3 | ₱10,500 |
| **Phase 1 subtotal** | | **31 person-days** | **₱91,500** |

*Or packaged as Likha sprints: ~1-month expert engagement (₱40,000) + QA/BA/PM support package (₱51,500) = ₱91,500 — equivalent either way.*

## Phase 2 (proposed)

| Role | Days | Amount |
|------|------|--------|
| Developer | 4.5 | ₱13,500 |
| QA | 1.5 | ₱3,750 |
| BA | 0.5 | ₱1,500 |
| PM | 0.5 | ₱1,750 |
| **Phase 2 subtotal** | **7** | **₱20,500** |

## Phase 3 (indicative — discovery required)

| Module | Est. team-days | Range |
|--------|----------------|-------|
| M17 Odoo integration | 8–12 | ₱25,000–40,000 |
| M18 SMS notifications | 2–3 | ₱7,000–10,000 |
| M19 Customer portal v2 | 6–9 | ₱20,000–30,000 |

## Recurring — Likha Cloud subscription

| Item | Price | Notes |
|------|-------|-------|
| Cloud Standard | ₱6,000/mo | 6 CPU / 12GB / 200GB — sufficient for multi-branch EasyPC |
| Domain + CMS + email package (optional) | ₱8,000/yr | `track.easypc.com.ph` + managed email accounts |
| Maintenance retainer (optional) | ₱10,000/mo | Monitoring, minor adjustments, backup verification |

## Commercial summary

| | One-time | Recurring |
|---|----------|-----------|
| Phase 1 implementation | ₱91,500 | — |
| Phase 2 hardening | ₱20,500 | — |
| Likha Cloud Standard | — | ₱6,000/mo |
| **Year-1 estimate (P1+P2+12mo cloud)** | | **₱184,000 total** |

## Terms & assumptions

- Client provides: domain decision, Titan/GoDaddy mailbox, Odoo API access (M17), T&C wording sign-off
- 90-day initial cloud term per Likha model, then month-to-month; on-prem migration available (one-time local deployment fee + 12-mo stability agreement)
- Not included: SMS/email provider usage fees, Jitsi self-hosting (public meet.jit.si used)
- Change requests: role rates above
- Payment: 40% mobilization · 40% Phase 1 UAT sign-off · 20% go-live
- Warranty: 30 days bug-fix post go-live
