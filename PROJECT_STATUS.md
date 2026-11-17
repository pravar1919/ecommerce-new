# Project Status

_Last updated: 2026-11-17_

## Completed milestones

### Phase 1: Initialisation, architecture, brand & design system ✅
- Requirements audit, architecture (ADR-001…013), database design, API conventions, commerce workflows
- Brand discovery: **Direction B "Quiet Heirloom" approved 2026-11-17** (theme key `heirloom`). Brand **name** still pending, so the dev identity `ATELIER` is in use.
- Design system, deployment, testing and roadmap docs. Repo, compose infra, Caddyfile, `.env.example`.

### Phase 2: Django foundation, models, auth, catalogue ✅
- **Project:** uv-managed (Python 3.14, Django 6.1.3, DRF 3.18, drf-spectacular 0.30). Settings split (base/development/test/production), env-driven config, Django 6.1 `MAILERS`, Celery + beat, structlog JSON/console logging with request-ID propagation.
- **Common kernel:** UUIDv7 base models, integer-paise `Money` with Indian digit grouping, `DomainError` → standard error envelope, CSRF enforced for anonymous unsafe requests, public/private S3 storages, health endpoints, production deploy checks (dev brand and dev secret blocked).
- **accounts:** custom email user (case-insensitive unique), Argon2, session auth, 9 staff roles synced to model permissions, login/logout/me, password reset via Celery email.
- **customers:** profiles, Indian addresses (GST state codes, pincode, +91 mobile, optional GSTIN, one default enforced in DB), body-measurement profiles validated against measurement definitions. Registration and all customer resources are owner-scoped (no IDOR).
- **categories / attributes:** category tree with materialised paths (cascading moves), collections with schedule windows and campaign accent. Typed facet tables (fabric, occasion, fit, pattern, embroidery, sleeve, colour, size systems/sizes).
- **catalog:** product ≠ variant (product × colour × size, size NULL for made-to-measure). MRP/sale price constraints, media with alt text, focal point and placeholder flag. Garment size charts kept separate from body measurement guidance. Complete-the-look, publish/archive services, weighted FTS + trigram search.
- **Catalogue API:** listing with filters (category subtree, collection, occasion, colour, size, fabric, fit, embroidery, pattern, fulfilment, price, in-stock), with variant conditions matched on the *same* variant. Disjunctive facets, 5 sort orders, search + suggest, product detail with per-variant stock status, related, size charts, measurement guide.
- **inventory:** stock levels (DB-checked `0 ≤ reserved ≤ on_hand`), append-only movement ledger, all-or-nothing reservations with deterministic row locking, release/commit/expiry (beat task every 60s), low-stock alerts + email.
- **pricing:** tax classes, date-ranged GST slab rules (DB exclusion constraint against overlaps), inclusive-tax split (CGST/SGST vs IGST), exact pro-rata discount allocation.
- **Django Admin:** catalogue with inlines and publish/archive actions. Stock adjustments go through the inventory service. Ledger and reservations are read-only.
- **devtools `seed_dev`:** idempotent, 23 products / 310 variants / stock / 3 collections / looks. Images are generated "DEV PLACEHOLDER" PNGs flagged `is_placeholder`. Refuses production.
- **Docker:** backend `Dockerfile` (dev target, plus a non-root gunicorn prod target with healthcheck). Compose backend auto-migrates, and worker/beat wait for a healthy backend. `Makefile` shortcuts.
- **Contract:** `backend/schema/openapi.yaml` (37 operations), validated with `--fail-on-warn`.

### Phase 3: Frontend design system, homepage, navigation ✅ (exit criteria verified 2026-11-17, not yet committed)
- **Frontend:** Next.js 16.4 (Cache Components, Partial Prefetching, standalone output), React 19.3, Tailwind v4 heirloom tokens/theme, next/font (Bodoni Moda + Hanken Grotesk), typed client generated from `openapi.yaml` (`npm run api:types` / `api:check`).
- **UI:** shadcn/ui primitives restyled. Motion wrappers around React Bits (Split Text, Blur Text, Count Up, Magnet, Noise) all load lazily and are reduced-motion aware. A single scroll `RevealObserver` and a head bootstrap script mean nothing is pre-hidden without JS.
- **Chrome:** announcement bar (pausable), header with desktop mega-menu and mobile drawer, footer, branded 404 inside the storefront chrome.
- **cms app:** `SiteSettings`, `Page`/`PageVersion`/`ContentBlock`, `MediaAsset`, `Testimonial`, `NavigationFeature`, `NewsletterSubscriber` (double opt-in). Public API: site settings, navigation, pages, newsletter signup/confirm. Publishing triggers tag revalidation of Next.js through Celery (`common/tasks.py` → `/api/revalidate`). Seeded by `devtools/cms_seed.py`.
- **Homepage:** all 14 sections composed from CMS blocks. `frontend` + `caddy` run in compose.
- **Performance work for the exit budgets:**
  - `motion` and GSAP load only as their sections near the viewport.
  - The mobile drawer (Radix Dialog + Accordion) loads on intent, and the desktop mega-menu (Radix NavigationMenu) loads only on ≥1024px over plain SSR links.
  - The footer uses native `<details>`, the newsletter checkbox is native, and film grain starts after load and idle.
  - `cn` uses merge tables fitted to our sources (`src/lib/cn-tables.ts`, generated by `withCn`). This also fixes a latent bug: stock tables don't know theme scales, so `cn("text-display-xl", "text-text-muted")` dropped the font size.

## In progress
- None. Phase 3 is ready to commit; awaiting go-ahead for Phase 4.

## Pending
- CI pipeline (none exists yet): `make check`, e2e against compose, `make lighthouse`, plus `mypy` / django-stubs.
- Phases 4–8 per `docs/implementation-roadmap.md`.
- Brand name selection + trademark checks. CA confirmation of GST slabs.

## Test results
| Date | Check | Result |
|---|---|---|
| 2026-11-17 | Phase 1 infra: compose config, Caddy validate, clean-slate boot, S3 policy (public 200 / private 403 / presigned / bad creds) | ✅ |
| 2026-11-17 | `pytest`: host and inside backend container | ✅ **84 passed** (0 warnings with `-W error::DeprecationWarning`) |
| 2026-11-17 | Coverage | ✅ 93% overall. Services: inventory 96%, customers 94%, pricing 93%, catalog 92%. Catalog selectors 98%. |
| 2026-11-17 | Concurrency: 5 simultaneous buyers for the last unit | ✅ exactly 1 reservation, 4 `OutOfStock` |
| 2026-11-17 | `ruff check`, `ruff format --check` | ✅ |
| 2026-11-17 | `lint-imports` (3 boundary contracts) | ✅ 3 kept, 0 broken |
| 2026-11-17 | `spectacular --validate --fail-on-warn` | ✅ |
| 2026-11-17 | `makemigrations --check` | ✅ no changes |
| 2026-11-17 | Fresh DB: migrate + `seed_dev` (twice, idempotent) | ✅ |
| 2026-11-17 | Live smoke (Docker): health, listing/filters/facets/search/typo/suggest/detail, placeholder image served from S3, 404/validation envelopes | ✅ |
| 2026-11-17 | Password reset: API → Redis → Celery worker → Mailpit | ✅ email delivered |
| 2026-11-17 | Django Admin: dashboard, product list/change, stock adjustment via service (20→24, ledger row), anon redirect | ✅ |
| 2026-11-17 | Beat → `release_expired_reservations` executing | ✅ |
| 2026-11-17 | Prod image: non-root (`uid=999`), `check --deploy` blocks the dev brand, and is clean with an approved brand | ✅ |
| 2026-11-17 | Phase 3 backend: `pytest` (incl. cms), ruff, `lint-imports` (4 contracts), schema in sync, `makemigrations --check` | ✅ **126 passed**, 4 contracts kept |
| 2026-11-17 | Frontend `make check-frontend`: typecheck, ESLint, Prettier, Vitest, API types and cn tables in sync | ✅ **28 unit tests passed** |
| 2026-11-17 | E2E (Playwright, desktop Chromium / Pixel 7 / iPhone 14 WebKit) on the compose stack: sections, a11y (axe WCAG 2.2 AA), reduced motion, nav, newsletter double opt-in via Mailpit | ✅ **41 passed**, 10 skipped by design (device-specific) |
| 2026-11-17 | E2E against the production build (`next start`) | ✅ 40 passed. The newsletter test needs Caddy's same origin (CSRF), as designed. |
| 2026-11-17 | Lighthouse mobile (`make lighthouse`, median of 3, slow 4G + 4x CPU, applied throttling) | ✅ LCP 1.6 s, CLS 0.002, TBT 43 ms, first-load JS 168.3 KB / 170, hero 5.7 KB. Perf 92, A11y 100, BP 100. |

## Known issues / notes
- **JS budget headroom is thin (168.3 / 170 KB gzip).** About 137 KB is the React + Next.js runtime. New client code on the home/PLP/PDP first load must be lazy or offset.
- Lighthouse runs with *applied* throttling locally. Lantern's simulation on localhost charges all JS to LCP (it reports about 3.7 s against 1.6 s applied), because every resource lands before first paint. Use `LH_THROTTLING=simulate` against a deployed origin.
- Lighthouse SEO 69 locally is expected: non-production pages are `noindex`.
- The axe "open navigation" check excludes Radix NavigationMenu's focus-proxy span (an aria-hidden, focus-forwarding element that focus never rests on).
- Reveal targets carry `suppressHydrationWarning`, because `RevealObserver` can mark them before their streamed Suspense boundary hydrates. `<body>` has it too, for browser extensions such as Grammarly.
- Dev S3 is SeaweedFS (MinIO images unavailable), ADR-011. Local Postgres host port is 5433 because 5432 is used by an unrelated container.
- `.env` values must not have inline `# comments` (django-environ keeps them). `.env.example` is formatted accordingly.
- pytest forces `--ds=config.settings.test`, because the compose `.env` exports `DJANGO_SETTINGS_MODULE=…development`. Before this fix, one in-container run used dev settings and uploaded test images to the dev bucket. 219 orphaned objects were deleted.
- "Bestselling" sort falls back to Featured until order analytics exist (Phase 6).
- `mypy` / django-stubs is not yet wired (planned with the CI pipeline, see Pending).
- Low-stock emails go only to staff in the "Inventory Manager" group. There are none in dev, so the tasks no-op.
- The dev admin password is printed once by `seed_dev`. Reset it with `manage.py changepassword admin@localhost`.

## Architectural decisions
See `docs/architecture.md` §8 (ADR-001 to ADR-013) and the as-built notes in `docs/database-schema.md`.
