# Premium Indian Menswear Commerce Platform

A production-oriented ecommerce platform for a premium Indian men's wedding and occasion-wear brand: sherwanis, kurta sets, indo-western, wedding suits and accessories, sold ready-to-wear and made-to-measure.

> The brand name is **not yet approved**. The platform runs under the configurable development identity `ATELIER`. See [`docs/brand-identity.md`](docs/brand-identity.md).

## Repository layout
```
backend/     Django + DRF modular monolith (Python, uv)          — from Phase 2
frontend/    Next.js App Router storefront + /admin (TypeScript)  — from Phase 3
infra/       Caddy, Postgres init, dev S3 (SeaweedFS) config
docs/        Architecture, brand, design system, schema, API, workflows, deployment, testing, roadmap
docker-compose.yml   Development stack
PROJECT_STATUS.md    Milestones, test results, known issues, decisions
```

## Stack
**Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS v4, Framer Motion, React Bits, shadcn/ui.
**Backend:** Python 3.14, Django, DRF, drf-spectacular, PostgreSQL 17, Redis, Celery, uv.
**Infra:** Docker Compose, Caddy, S3-compatible storage. **Integrations:** Razorpay, shipping/email/SMS provider abstractions.

## Development setup

Prerequisites: Docker Desktop (or Engine + Compose v2.24+), Node 22+, uv.

```bash
cp .env.example .env            # adjust *_HOST_PORT if a port is taken locally
docker compose up -d            # postgres, redis, s3 (+ s3-init), mailpit
docker compose ps               # all healthy; s3-init exits 0
```

| Service | URL / port |
|---|---|
| PostgreSQL | `localhost:${POSTGRES_HOST_PORT:-5432}` (db/user `ecommerce`) |
| Redis | `localhost:6379` |
| S3 (SeaweedFS) | `http://localhost:9000`, bucket `ecommerce-media` (`public/` is anonymous-read, everything else private) |
| Mailpit (dev email inbox) | http://localhost:8025 |
| Site via Caddy (from Phase 3) | http://localhost:8080 |
| Django API (direct) | http://localhost:8000/api/v1/ (via Caddy on :8080 from Phase 3) |

### Backend (Phase 2)
```bash
make up-app      # backend (auto-migrates) + Celery worker + beat on http://localhost:8000
make seed        # idempotent dev catalogue: 23 products, labelled DEV PLACEHOLDER images; prints a one-time admin password
make check       # lint, import contracts, tests + coverage, OpenAPI drift, migration check
```
- API docs: http://localhost:8000/api/v1/docs/. Django Admin (break-glass): http://localhost:8000/django-admin/
- Reset the dev admin password: `docker compose exec backend uv run --no-sync python manage.py changepassword admin@localhost`
- Running Django on the host instead: `cd backend && cp .env.host.example .env.host` (adjust ports), then `set -a; source .env.host; set +a; uv run pytest`.

`frontend` and `caddy` join the `app` profile in Phase 3.

Reset everything (destroys local data): `docker compose down -v`.

## Documentation
| Doc | Contents |
|---|---|
| [architecture](docs/architecture.md) | Requirements audit, system design, app boundaries, service layer, ADRs, reference-resource evaluation |
| [brand-identity](docs/brand-identity.md) | Three brand directions, configurable brand metadata, dev identity |
| [design-system](docs/design-system.md) | Tokens, typography, grid, imagery, motion, React Bits selection, a11y, performance budgets |
| [database-schema](docs/database-schema.md) | All tables, constraints, state machines |
| [api-contracts](docs/api-contracts.md) | Conventions, error envelope, endpoint map, CMS block schemas, changelog |
| [commerce-workflows](docs/commerce-workflows.md) | Pricing/GST, checkout, payments, webhooks, COD, cancellations, returns, refunds, MTM |
| [deployment](docs/deployment.md) | Topology, release, secrets, Razorpay go-live, observability, backups |
| [testing-strategy](docs/testing-strategy.md) | Test layers, coverage targets, milestone gate |
| [implementation-roadmap](docs/implementation-roadmap.md) | Phases 1–8 and business dependencies |

## Rules of the road
- Business logic lives in `services.py`. Views and serializers stay thin.
- The server computes every price and payment status. The client sends IDs and quantities only.
- No secrets in source. `.env` is gitignored.
- Breaking API changes are recorded in `docs/api-contracts.md#changelog`.
- A milestone is complete only when tests pass and `PROJECT_STATUS.md` is updated.
