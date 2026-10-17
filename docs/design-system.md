# EasyPC Design System — Branding & Themes

Single source of truth for EasyPC's visual identity across the tracking frontend, printed documents, and any future surfaces (Directus extensions, emails, Odoo-facing pages).

## Brand

| | |
|---|---|
| Wordmark | **EASY** in vivid green + **PC** in near-black (light surfaces) or white (dark surfaces) |
| Tagline | `TECH IT EASY` — uppercase, wide letter-spacing (~3.5px), muted |
| Personality | Technical, high-contrast, energetic green on dark |

## Color tokens

Two theme expressions of the same brand — **dark** for screens, **light** for print.

### Screen theme (tracker — `tracker/src/index.css`)

Dark-first. Values are oklch; hex approximations shown.

| Token | Value | ~Hex | Use |
|---|---|---|---|
| `--background` | `oklch(0.16 0.01 145)` | ~#101512 | App/page background |
| `--foreground` | `oklch(0.96 0.01 145)` | ~#f2f5f2 | Primary text |
| `--card` / `--popover` | `oklch(0.20 0.015 145)` | ~#1a201c | Card/panel surfaces |
| `--primary` | `oklch(0.82 0.28 145)` | ~#4afa82 | Brand green — buttons, links, highlights |
| `--primary-foreground` | `oklch(0.14 0.02 145)` | ~#0e1310 | Text on green |
| `--secondary` | `oklch(0.28 0.02 145)` | ~#2a332d | Secondary fills |
| `--muted` / `--muted-foreground` | 0.28 / 0.70 lightness | — | Subtle surfaces / secondary text |
| `--accent` | = primary | — | Highlights |
| `--destructive` | `oklch(0.62 0.24 27)` | ~red | Cancelled/error states |
| `--success` | = primary | — | Warranty/positive |
| `--warning` | `oklch(0.82 0.17 90)` | ~amber | Attention statuses |
| `--border` / `--input` / `--ring` | 0.32 / 0.28 / primary | — | Borders, inputs, focus |
| `--radius` | `0.625rem` | 10px | Base corner radius (lg/md/sm derive) |

### Print theme (`scripts/easypc_work_order_form.liquid`)

Light, ink-friendly — same brand, paper-appropriate.

| Element | Value |
|---|---|
| Brand green | `#00c853` (accents, borders, header rule) |
| Dark green (text on light) | `#0a7a38` / `#0a8a3c` |
| Tint surface | `#f0faf3` (section headers, table headers) |
| Tint border | `#cdeed8` |
| Body text | `#1a1a1a`; muted `#777` |
| Grid borders | `#dcdcdc`; section borders `#d5d5d5` |
| Page | A4, 11–12mm margins, `page-break-inside: avoid` per section |

Print motifs: 3px green rule under header · green left-bar on `.sec-h` · dashed green tracking strip · green signature labels · thin green footer rule.

## Typography

| Context | Stack |
|---|---|
| Screen | `ui-sans-serif, system-ui, "Segoe UI", Roboto` |
| Print | `'Segoe UI', Arial, Helvetica` |
| Numbers / codes | `Consolas, monospace` — WO numbers, tracking keys, prices |

Logo lockup: `font-weight 900`, `letter-spacing -1px`, "EASY" in primary green. Headings use uppercase + `letter-spacing 0.4–1.5px` at small sizes (9–11px) — the "section label" voice.

## Components (shadcn-style, `tracker/src/components/ui/`)

`cn()` helper + `cva` variants — drop-in compatible with `npx shadcn add`.

| Component | Variants | Notes |
|---|---|---|
| `Button` | default, outline, secondary, ghost, destructive | `lg` size used on forms; focus ring = `--ring` |
| `Card` | — | `bg-card`, `border`, `rounded-lg`; `border-primary/40` for highlighted cards (video call) |
| `Badge` | default, secondary, destructive, warning, outline | Status badges driven by `statusVariant()` |

## Status color language

`tracker/src/lib/status.js` maps work-order statuses → badge variants:

| Status | Variant | Reading |
|---|---|---|
| `released` | default (green) | Done — positive terminal |
| `testing`, `ready_for_release` | warning (amber) | Almost there — act soon |
| `cancelled`, `unclaimed` | destructive (red) | Exception |
| all others | secondary (neutral) | In-flight |

Journey order for the timeline: `registered → awaiting_assessment → assessing → awaiting_approval → in_repair → testing → ready_for_release → released` (`approved`/`declined` are decision flags on the WO, not timeline stages).

## Usage rules

- **Green is reserved for brand/interaction** — primary actions, brand marks, status-positive. Don't use green for decorative noise.
- **Dark-first on screen; light-only on paper.** Never print the dark theme — the print template is a separate light stylesheet.
- Customer-facing surfaces show no staff identity; statuses use the friendly labels above (e.g. `ready_for_release` → "Ready for Pickup").
