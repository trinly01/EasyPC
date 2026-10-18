# EasyPC Service Work Order System — Proposal & Quotation

Prepared for: **EasyPC**
Platform: **Likha ERP** + branded customer-facing tracker on GitHub Pages
Engagement: **2-month project** — build sprints → pilot → polish → go-live
Team: **1 Developer · 1 QA · 1 PM · 1 Business Analyst**

---

## What you're paying for — configuration, integrations, custom build

**1. Native platform capability (configured, not coded):**

| Capability | How it's used for EasyPC |
|---|---|
| Collections & relational schema | 14 `easypc_*` tables mirroring the paper form, snapshot pricing |
| Roles, policies & permissions | 3 staff roles, branch-scoped filters, append-only updates |
| Flows engine | Triggers/op chains for numbering, milestones, warranty stamping, T&C snapshotting |
| Print interface (LiquidJS) | Branded ink-friendly service form template |
| Admin app / files / audit log | Staff work-order UI, photo attachments, full history |

**2. Third-party integrations (external systems wired into the platform):**

| Integration | What was built |
|---|---|
| **Jitsi Meet** | Flow logic that generates a per-work-order video room at `in_repair`/`testing`, reuses it on rework, and posts it to the customer — customers join live diagnostics/repair |
| **Email notifications (SMTP)** | Server-level transport configured and verified — sends through **EasyPC's existing email account**, no new mail service needed |
| **Semaphore SMS** *(polish phase)* | Webhook op in the milestone flow → SMS alerts on status changes. Integration built by Zyberlab; **Semaphore account and credits are the client's own — not billed through Zyberlab** (~₱1/msg, prepaid) |
| **GitHub Pages / Actions** | CI pipeline that builds and deploys the tracker on every change |

**3. Custom build (standalone code, outside the platform):**

| Deliverable | What it is |
|---|---|
| **Public tracker web app** | React/Vite customer-facing UI — lookup page, journey timeline, video-join button, warranty display — branded, GitHub Pages-hosted, talks to Likha only through the PII-safe webhook flow |

*Plus expert design work that isn't a feature or code: mapping the paper form into a normalized model, the permission matrix, flow behavior design, and E2E verification.*

## Module inventory — grouped

### Group A — Core service platform (delivered)

| # | Module | What's included |
|---|--------|-----------------|
| M1 | Data model & schema | 14 work-order tables mirroring the paper form; snapshot pricing; per-part + labor warranty fields |
| M2 | Multi-branch RBAC | 3 roles (front desk, technician, manager), branch-scoped access, append-only updates log |
| M3 | Workflow automation | WO numbering + tracking token, milestone updates, release/warranty stamping |
| M4 | Printable service form | Branded ink-friendly print template matching the paper form |

### Group B — Customer-facing channels (delivered)

| # | Module | What's included |
|---|--------|-----------------|
| M5 | Email notifications | Milestone + technician updates to customer email |
| M6 | Video transparency | Per-WO Jitsi room at repair/testing stages, stable link |
| M7 | Public tracking portal | WO + mobile lookup, journey timeline, video-join, warranty display |
| M8 | Settings & legal versioning | Central settings; per-WO T&C snapshots — reprints keep signed terms |
| M9 | Seed data & documentation | Multi-branch demo data, full docs set |

### Group C — Hardening & rollout (pilot/polish phase)

| # | Module | What's included |
|---|--------|-----------------|
| M10 | Production readiness | Tracker domain, CORS, password policy, backup runbook |
| M11 | QR intake | Tracking QR printed on the service form |
| M12 | Public-message curation | Internal notes never leak to the tracker |
| M13 | Abuse protection | Rate-limit lookup webhook |
| M14 | Unclaimed reminders | Past claim window → email + flag |
| M15 | Delivery assurance | Email sent/failed tracking + retry |
| M16 | Branded email | Design-system HTML template |
| M17 | SMS milestone alerts | Semaphore integration (client's account) |

### Group D — Future phases (separate quotation)

| # | Module | Note |
|---|--------|------|
| M18 | Odoo integration | Requirements discovery needed first |
| M19 | Customer portal v2 | Approve/decline, photo galleries, PDF download |

## 2-month delivery plan

| Phase | Weeks | Activities | Output |
|-------|-------|-----------|--------|
| **Sprint 1 — Core build** | 1–2 | Schema, multi-branch RBAC, workflow flows | ✅ Done |
| **Sprint 2 — Surfaces** | 3–4 | Print template, email notifications, Jitsi video, public tracker, settings snapshots | ✅ Done |
| **Pilot** | 5–6 | **Live at 1 pilot branch** — real work orders, staff onboarding, daily monitoring, feedback triage | Pilot report |
| **Polish & hardening** | 7–8 | Pilot fixes, production readiness (CORS, domain, passwords), QR intake, message curation, abuse protection, branded email | Go-live ready |
| **Go-live** | End of wk 8 | Sign-off, cutover, hypercare handoff | Acceptance |

*Sprints 1–2 are delivered and verified on the playground instance. Two full weeks of pilot protect the schedule — polish lands on observed problems, not guesses.*

## Pilot scope (weeks 5–6)

- 1 branch, full journey live: intake → assessment → repair → testing → release
- Front desk + technician accounts active; real customers use the tracker
- Daily check-ins (PM), defect log, Friday feedback review
- Success criteria: work orders completed end-to-end, zero P1 defects, tracker lookups working, emails delivering

## Polish scope (weeks 7–8)

| Item | Detail |
|---|---|
| Production readiness | CORS origin for tracker, production domain, password policy, backup runbook |
| QR intake | Tracking QR printed on the service form |
| Public-message curation | `public_message` field — internal notes never leak |
| Abuse protection | Rate-limit lookup webhook |
| Delivery assurance | `email_status` sent/failed + retry |
| Branded email | EasyPC design-system HTML template |
| SMS milestone alerts | **Semaphore** — cheapest PH gateway (~₱1/SMS prepaid), webhook op in milestone flow |
| Pilot feedback | Whatever the pilot surfaces — prioritized with client |

---

## Effort & pricing — 2-month engagement

**Billing model: fixed project rate per role** — one agreed fee for the whole 2-month engagement, not tied to hours or pace. The team commits to delivering the defined scope on schedule.

| Role | Fixed project rate (2-month engagement) |
|------|----------------------------------------:|
| Developer | ₱75,000 |
| QA | ₱75,000 |
| Business Analyst | ₱18,000 |
| Project Manager | ₱31,500 |
| **Implementation total** | **₱199,500** |

*Dev/QA billed at the same fixed rate (internal cost ₱40k/mo each). PM/BA at market (~₱55k/₱50k cost basis) — confirm with internal costing.*

**Commitment & scope discipline:**

- The fixed fee covers the **defined scope only** — the module list above, delivered within 2 months
- **Anything beyond scope is quoted separately before work starts**, sized by complexity:
  - Small tweak (field, label, minor flow adjustment): ₱3,000–8,000
  - Medium feature (new flow, report, template change): ₱10,000–25,000
  - Large item (new module, integration, portal feature): scoped & quoted individually
- Schedule slips caused by client-side delays (access, feedback, sign-offs) extend the monthly billing pro-rata
- Schedule slips caused by Zyberlab are absorbed — that's the client's protection under fixed billing

*Alternative — dedicated full-time team × 2 months: ₱252,000/mo (all four roles at 100%). Not recommended: the workload is genuinely dev-heavy and fractional.*

*SMS is client-funded directly: EasyPC owns the Semaphore account and buys prepaid credits (~₱1/message — e.g. ₱2,500 ≈ 2,500 milestone alerts). Zyberlab bills only the integration build, never the usage.*

## Rollout options — by branch count

| | **Option A — Pilot first** | **Option B — Multi-branch** | **Option C — Network-wide** |
|---|---|---|---|
| Branches at go-live | 1, expand later | 3–5 | 6+ / all |
| Implementation (2 mo) | ₱199,500 | ₱199,500 | ₱199,500 |
| Extra training & rollout | incl. pilot | +4 pd — ₱12,000 | +8 pd — ₱24,000 |
| Likha Cloud tier | Standard ₱6k/mo | Standard ₱6k/mo | Pro ₱12k/mo |
| Go-live support | hypercare wk 9 | +2 wks remote | +1 mo remote/on-call |
| **One-time total** | **₱199,500** | **₱211,500** | **₱223,500** |
| **Year-1 all-in** (+ 12 mo cloud) | **₱271,500** | **₱283,500** | **₱367,500** |

*Branch scaling is already in the schema (`easypc_store` + permission filters) — moving A → B/C is training & rollout, not a rebuild.*

## Billing model — what Zyberlab bills vs. what the client owns

**Billed by Zyberlab:**

| Item | Price | Notes |
|------|-------|-------|
| Implementation (2-month engagement) | ₱199,500 | fixed project rate per role, table above |
| Likha Cloud subscription | ₱6,000–12,000/mo | **starts in parallel with project kickoff/development** — the environment is provisioned day one so build, pilot, and polish run on the client's own instance; 90-day initial term, then month-to-month |
| Maintenance retainer (optional) | ₱10,000/mo | monitoring, minor adjustments, backup verification |

**Client's own accounts — paid directly by EasyPC, never through Zyberlab:**

| Service | Cost | Purpose |
|---------|------|---------|
| Semaphore SMS | ~₱1/msg prepaid | milestone SMS alerts |
| Titan/GoDaddy email | existing mailbox | notification sender |
| Jitsi Meet | free (meet.jit.si) | technician video calls |
| GitHub Pages | free | tracker hosting |
| Tracker domain | ₱0 — EasyPC-owned | `track.easypc.com.ph` is a subdomain on EasyPC's existing domain — their DNS, their control |

*Any future third-party integration (SMS provider, payment gateway, Odoo, etc.) follows the same rule: Zyberlab bills the integration work; the platform account and usage fees are the client's.*

## Excluded — separate quotation

- **Odoo integration** — scoped only after requirements discovery (ticket linking, SO sync, parts inventory, customer dedup). Price depends on Odoo version/API access and sync depth.
- Customer portal v2 (approve/decline from tracker, photo galleries, PDF download)
- Unclaimed-reminder automation

## Terms

- **Payment:** 40% mobilization · 30% at pilot start (wk 5) · 30% go-live sign-off
- **Subscription start:** Likha Cloud billing begins at project kickoff and runs in parallel with development — the environment is provisioned day one so sprints, pilot, and polish all run on the client's live instance; 90-day initial term, then month-to-month
- **Client provides & owns:** all third-party service accounts — Semaphore (SMS), Titan/GoDaddy mailbox, domain, plus pilot branch access + staff time and T&C wording sign-off
- **Not included:** any third-party usage/subscription fees (client-paid direct), Jitsi self-hosting (public meet.jit.si used), hardware
- **Change requests:** charge-out rates above
- **Warranty:** 30 days bug-fix post go-live (hypercare week 9 included)
- **Negotiation floor:** internal cost ≈ ₱100k for the 2 months — below ₱150k, cut scope (drop SMS/branded email/QR) rather than margin
