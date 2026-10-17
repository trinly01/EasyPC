# EasyPC — Service Work Order System

Directus 11 backend + public repair tracker for EasyPC's paper-based service form. All created artifacts are prefixed `easypc_`.

**Live tracker:** `https://trinly01.github.io/EasyPC/` — customers track with **WO number + registered mobile number**.
**Backend:** `https://likha-playground.zyberlab.com` (Directus 11.17.4).

## Repo layout

| Path | What |
|---|---|
| `docs/` | All documentation — start at `docs/README.md` |
| `docs/data-model.md` | Field-by-field spec for every `easypc_*` collection |
| `docs/workflow.md` | Status lifecycle, transitions, roles overview |
| `docs/flows.md` | Every flow: triggers, op chains, gotchas |
| `docs/roles-and-access.md` | Policies, permission matrix, branch scoping, test accounts |
| `docs/public-tracking.md` | Tracker API contract, security model, deployment |
| `docs/design-system.md` | Brand tokens, themes (dark screen / light print), components |
| `tracker/` | React 19 + Vite + Tailwind 4 + shadcn-style public tracker |
| `scripts/` | Idempotent build/seed/fix scripts (run with `DIRECTUS_TOKEN` env) |
| `scripts/easypc_work_order_form.liquid` | Print template source (LiquidJS) — edit here, upload to `print_template` |
| `.github/workflows/deploy-pages.yml` | Tracker → GitHub Pages deploy |

## Scripts

All scripts read `DIRECTUS_TOKEN` from the environment — never hardcode tokens.

```bash
export DIRECTUS_TOKEN=<admin-token>
python scripts/build_schema.py      # collections, fields, relations
python scripts/build_flows.py       # milestone / notify / warranty / numbering flows
python scripts/seed_data.py         # realistic stores, services, parts, customers, WOs
python scripts/add_tracking_token.py
python scripts/build_track_lookup.py
python scripts/add_phone_lookup.py  # phone-based public lookup
python scripts/fix_warranty_flow.py
```

`add_video_link*.py` / `fix_video_link*.py` are the iterative history of the Jitsi link flow — the current behavior is documented in `docs/flows.md`, not in script order.

## Quick links

- Public tracker endpoint: `POST /flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70` — `{wo, key}` where `key` = customer mobile (full or last-4) or `tracking_token`
- Print template: `print_template` → `easypc_work_order_form`
- GitHub Pages: repo Settings → Pages → source **GitHub Actions**
