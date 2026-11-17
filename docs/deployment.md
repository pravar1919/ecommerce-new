# Deployment

## Environments
| Env | Purpose | Infra |
|---|---|---|
| `development` | Local | `docker-compose.yml`: Postgres, Redis, SeaweedFS (S3), Mailpit (+ app services under the `app` profile) |
| `test` | CI | Ephemeral Postgres + Redis service containers |
| `staging` | Pre-release, Razorpay **test** keys | Same compose as production on a smaller VM |
| `production` | Live | `docker-compose.prod.yml` on a VM (e.g. 4 vCPU / 8 GB), with managed Postgres recommended |

## Production topology
- **Caddy**: automatic HTTPS (Let's Encrypt), HTTP/3, zstd/gzip, security headers, `X-Request-ID`. Routes `/api/*`, `/django-admin/*` and `/static/*` → backend, and everything else → frontend.
- **backend**: `gunicorn config.wsgi` (4 workers × 2 threads to start). Runs as non-root. Read-only root FS.
- **worker**: `celery -A config worker -Q default,notifications,media --concurrency=4`
- **beat**: `celery -A config beat` (single instance only)
- **frontend**: `next start` from a standalone build (`output: "standalone"`)
- **postgres**: managed (RDS / DigitalOcean / Neon) preferred. If self-hosted, run nightly `pg_dump` + WAL archiving to S3.
- **redis**: persistent volume (AOF). Used as cache, broker and throttle store.
- **Media**: S3 / R2 bucket. Product images and campaign media sit under a public-read prefix (`public/`), served via a CDN. Invoices, labels and return evidence sit under a **private** prefix and are served by presigned URLs with ≤ 5 min TTL.

## Release procedure
1. CI green: lint, typecheck, unit + API tests, OpenAPI diff, Playwright smoke, image build.
2. Build and tag images `backend:<git-sha>` and `frontend:<git-sha>`. Push to the registry.
3. On the host: `docker compose -f docker-compose.prod.yml pull`.
4. `docker compose run --rm backend uv run python manage.py migrate --noinput` (migrations must be backward-compatible with the running version: expand → migrate → contract).
5. `docker compose up -d --no-deps backend worker beat frontend`. Caddy health-checks upstreams.
6. Smoke check: `/api/v1/health/`, the homepage, a PDP, the Razorpay test order on staging.
7. Rollback: redeploy the previous SHA. Migrations are not reversed automatically.

## Configuration & secrets
- Everything comes from environment variables (`.env.example` lists them all). In production, secrets come from the host secret store or an SSM / Doppler-style injector, **never** a committed file.
- `DJANGO_SECRET_KEY`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `AWS_SECRET_ACCESS_KEY`, SMTP/SMS keys and `REVALIDATE_SECRET` are rotated on staff departure or suspected leak.
- `manage.py check --deploy` plus the custom checks (`brand_identity_approved`, `razorpay_live_keys_in_production`, `debug_off`) run at container start and fail closed.

## Razorpay go-live checklist
- Live keys are set only in the production env. The webhook URL is `https://<domain>/api/v1/payments/razorpay/webhook/`, with a secret matching `RAZORPAY_WEBHOOK_SECRET`. Subscribed events: `payment.captured`, `payment.failed`, `order.paid`, `refund.processed`, `refund.failed`.
- Auto-capture is on. Test refunds, failures and duplicate webhooks on staging.

## Observability
- Structured JSON logs to stdout, shipped by the host agent (Loki, Datadog or CloudWatch).
- Error tracking: Sentry (backend + frontend), DSN by env, PII scrubbing on.
- Health: `/api/v1/health/` (DB, Redis, storage), `/api/v1/health/live/`.
- Alerts: 5xx rate, p95 latency, failed webhooks, Celery queue depth, reservation-expiry-after-payment count, low stock digest.

## Backups & recovery
- Postgres: daily full + PITR. Restore drill monthly. RPO ≤ 15 min, RTO ≤ 2h.
- S3: versioning on, with lifecycle rules for old versions.
