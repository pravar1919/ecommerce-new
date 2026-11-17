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

## In progress
- None. Awaiting go-ahead for Phase 3.

## Pending
- **Phase 3:** Next.js scaffold, heirloom tokens, typed client from `openapi.yaml`, navigation, `cms` app, homepage blocks, `frontend` + `caddy` in compose.
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

## Known issues / notes
- Dev S3 is SeaweedFS (MinIO images unavailable), ADR-011. Local Postgres host port is 5433 because 5432 is used by an unrelated container.
- `.env` values must not have inline `# comments` (django-environ keeps them). `.env.example` is formatted accordingly.
- pytest forces `--ds=config.settings.test`, because the compose `.env` exports `DJANGO_SETTINGS_MODULE=…development`. Before this fix, one in-container run used dev settings and uploaded test images to the dev bucket. 219 orphaned objects were deleted.
- "Bestselling" sort falls back to Featured until order analytics exist (Phase 6).
- `mypy` / django-stubs is not yet wired (planned with Phase 3 CI).
- Low-stock emails go only to staff in the "Inventory Manager" group. There are none in dev, so the tasks no-op.
- The dev admin password is printed once by `seed_dev`. Reset it with `manage.py changepassword admin@localhost`.

## Architectural decisions
See `docs/architecture.md` §8 (ADR-001 to ADR-013) and the as-built notes in `docs/database-schema.md`.
