# Architecture

## 1. Requirements audit

The brief was audited for gaps, contradictions and risks before any design work. The resolutions below are binding unless revised here.

| # | Finding | Resolution |
|---|---|---|
| 1 | "`categories`" and "`catalog`" are separate apps, but products need categories | `catalog` depends on `categories` and `attributes`. Never the reverse. See the dependency rules below. |
| 2 | "Discount price" is per variant, while "Promotions/Coupons" is a separate app | Variant `sale_price` is the list-level markdown. Promotions/coupons apply at cart level on top. The two are never merged in storage. |
| 3 | GST on apparel depends on the **transaction value per piece**, and slabs change by notification | GST is a data-driven `pricing.TaxRule` with threshold slabs and effective dates. No rates are hardcoded. Rates are confirmed by a CA before launch. |
| 4 | Made-to-measure (MTM) conflicts with "inventory by variant" | MTM variants have `size = NULL`, `inventory_policy = made_to_order` (not stock-tracked) and a lead time. The MTM line snapshot stores the measurement profile. |
| 5 | A "dedicated Next.js admin" alongside "Django Admin" risks two sources of truth | The Next.js admin is the **operational** UI and uses the same DRF API with staff permissions. Django Admin is mounted at `/django-admin/` for engineers and support break-glass, restricted to superusers and audited. |
| 6 | "Never trust frontend prices or payment status" | The server recomputes every quote, and checkout submits only IDs and quantities. An order moves to `paid` only from a server-verified Razorpay signature or webhook. |
| 7 | Webhooks are at-least-once | `payments.WebhookEvent` has a unique `(provider, event_id)`. Processing is idempotent and transactional. |
| 8 | Photography rules: no invented product images | `ProductMedia` accepts uploads only through the admin. CMS `MediaAsset` carries `is_product_photo=false` and cannot be linked to products. Dev seed data uses clearly labelled placeholders. |
| 9 | Unapproved brand name must not be hardcoded | Brand is CMS data plus an env fallback, and a production startup check blocks the dev identity. See `brand-identity.md`. |
| 10 | Unsloth listed as a "mandatory reference" | Evaluated in §9 and excluded from the stack. |
| 11 | Auth between Next.js and Django | Same-origin via Caddy, Django session cookies plus CSRF (§4). No tokens in `localStorage`. |
| 12 | COD increases RTO (return-to-origin) risk | COD availability is per pincode, with an order-value cap, a COD fee and optional OTP confirmation, all configurable. |
| 13 | Invoices need GST-compliant sequential numbering per financial year | A `orders.InvoiceSequence` row locked with `SELECT … FOR UPDATE` per FY. Format `INV/26-27/000123` (≤ 16 chars). |
| 14 | Reviews must not be spoofable | Only customers with a delivered order line can review that product (verified purchase). Reviews are moderated before display. |
| 15 | Redis 8 licence (AGPLv3 / RSALv2 / SSPLv1) | Fine for self-hosted use. Valkey is a documented drop-in alternative (`REDIS_URL` only). |

## 2. System overview

```
                         ┌──────────────────────────────┐
  Browser ──HTTPS──▶  Caddy (TLS, compression, headers) │
                         │  /api/*, /django-admin/*,    │──▶ Django (gunicorn/uvicorn) ──▶ PostgreSQL
                         │  /static/*                   │          │        ▲
                         │  everything else             │──▶ Next.js (SSR/ISR, storefront + /admin)
                         └──────────────────────────────┘          │        │
                                                                    ▼        │
                                                             Redis (cache, Celery broker, rate limits)
                                                                    │
                                                         Celery worker + beat ──▶ Email/SMS/Shipping/Razorpay
                                                                    │
                                     S3-compatible storage (media, invoices) ◀── direct, presigned uploads
```

- **Modular monolith:** one Django project and one Next.js project. No microservices, no Kubernetes.
- **Same origin:** Caddy serves both apps under one domain. That removes CORS, allows `SameSite=Lax` session cookies and keeps CSRF simple.
- Next.js server components call Django **inside the network** (`INTERNAL_API_URL=http://backend:8000`), forwarding the user's cookies when personalised. Public catalogue reads use ISR with tag revalidation that Django triggers on publish.

## 3. Backend (Django)

### Stack
Python 3.14 (pinned via `.python-version` and uv; 3.14 adds stdlib `uuid.uuid7()` for time-ordered PKs. The local system Python 3.15 is not used.), Django (latest stable 6.x at scaffold time), DRF, drf-spectacular, psycopg 3, django-storages (S3), Celery + Redis, django-filter, structlog, Pillow, WeasyPrint (invoice PDF), razorpay SDK, pytest-django, factory_boy and ruff for tooling. Dependencies are managed only with **uv** (`pyproject.toml` + `uv.lock`).

### Project layout
```
backend/
  pyproject.toml  uv.lock  .python-version  Dockerfile  manage.py
  config/
    settings/ base.py  development.py  test.py  production.py
    urls.py  api_urls.py  celery.py  asgi.py  wsgi.py
  common/              # shared kernel: Money, base models (UUID, timestamps),
                       # exceptions → error envelope, pagination, permissions, logging, idempotency
  apps/
    accounts/ customers/ catalog/ categories/ attributes/ inventory/ pricing/
    carts/ wishlists/ checkout/ orders/ payments/ shipping/ promotions/
    reviews/ returns/ cms/ notifications/ analytics/
  devtools/            # dev-only management commands (seed_dev); outside import-linter domain contracts
  integrations/
    razorpay/  shipping_providers/  email_providers/  sms_providers/
```

### Inside every app
```
apps/<app>/
  models.py          # data + DB constraints; no business workflows
  selectors.py       # read queries (optimised querysets, annotations)
  services.py        # business operations, @transaction.atomic, explicit inputs
  serializers.py     # validation + representation only
  api/ views.py urls.py   # thin: parse → call service/selector → serialise
  permissions.py
  tasks.py           # Celery tasks; call services, never contain logic
  admin.py           # Django Admin registration
  signals.py         # avoided; only for decoupled side effects (cache bust)
  tests/ test_models.py test_services.py test_api.py factories.py
```

**Rules**
- Views and serializers never call `.save()` on another app's models. They call that app's `services`.
- Cross-app access goes through the target app's `services` / `selectors` public functions, never its internals.
- Services take primitives or model instances, return domain results and raise `common.exceptions.DomainError` subclasses (`OutOfStock`, `PriceChanged`, `CouponInvalid`, `PaymentVerificationFailed`, …), which map to the API error envelope.
- Side effects outside the DB (email, SMS, provider calls) are queued with `transaction.on_commit(lambda: task.delay(...))`.

### Dependency direction (enforced with `import-linter` contracts)
```
common ◀── accounts ◀── customers
categories, attributes ◀── catalog ◀── inventory, pricing, reviews, wishlists, cms
catalog, inventory, pricing, promotions ◀── carts ◀── checkout ◀── orders ◀── payments, shipping, returns
notifications, analytics: consume events from any app (called via on_commit tasks); nothing depends on them
```

### Critical service functions (explicit, transactional)
| Service | Location | Guarantees |
|---|---|---|
| `reserve_stock(lines, owner, ttl)` | inventory.services | `SELECT … FOR UPDATE` on `StockLevel` rows in a deterministic order (variant id) to avoid deadlocks. Raises `OutOfStock`. |
| `release_reservation(reservation)` | inventory.services | Idempotent. Also run by a beat task for expired reservations. |
| `quote_checkout(cart, address, coupon, payment_method)` | checkout.services | Pure recomputation from DB: prices, promotions, shipping, COD fee, GST split. Returns a `Quote` and a hash. |
| `place_order(checkout_session, idempotency_key)` | orders.services | One transaction: re-quote, compare hash, convert reservations, create the Order + immutable OrderLine snapshots, redeem the coupon, create the Payment intent. A duplicate key returns the existing order. |
| `confirm_payment(provider_payload)` | payments.services | Signature verified, amount and currency matched to the order, state transition `pending → paid`, stock committed, invoice queued. Idempotent. |
| `process_webhook(event)` | payments.services | Dedupe by event id, then dispatch to `confirm_payment` / `mark_failed` / `apply_refund_update`. |
| `cancel_order(order, actor, reason)` | orders.services | Allowed states only. Releases or restocks stock and triggers `initiate_refund` if paid. |
| `initiate_refund(payment, amount, reason, idempotency_key)` | payments.services | Refund total ≤ captured minus already refunded (checked under lock). Calls the provider with an idempotent receipt. |
| `approve_return / receive_return` | returns.services | Restock (`return` movement) and refund on inspection pass. |
| `adjust_stock(variant, delta, reason, actor)` | inventory.services | Writes an append-only `StockMovement`. Triggers a low-stock alert task. |

### Cross-cutting
- **Money:** integer paise (`BigIntegerField`) everywhere, wrapped in a `common.money.Money` value object. INR only (a currency field is stored for future-proofing).
- **IDs:** UUIDv7 primary keys on public resources, plus human-readable numbers for orders, returns and invoices.
- **Logging:** structlog JSON in production, with a request id (`X-Request-ID` propagated from Caddy) and user id bound to every log line. No PII in logs (emails and phones masked).
- **Rate limiting:** DRF throttles backed by Redis for login, OTP, coupon apply, pincode check and newsletter.
- **Security:** Argon2 password hashing, `SECURE_*` headers, CSRF, session rotation on login, admin 2FA (Phase 8), object-level permissions on customer resources, and a staff role → permission matrix (`accounts/roles.py`).
- **Search:** PostgreSQL full-text search (`SearchVector` on name, description and attributes, weighted, GIN index) plus `pg_trgm` for typo-tolerant suggestions. This can be swapped for Meilisearch later behind `catalog.search` selectors without changing the API.

## 4. Authentication & authorisation

- Customers: email + password (and optional phone OTP login in Phase 7 via the SMS provider). Django sessions (Redis-cached DB sessions), `SameSite=Lax`, `HttpOnly`, `Secure`.
- SPA calls: `GET /api/v1/auth/csrf/` sets the CSRF cookie, and mutating requests send `X-CSRFToken`.
- Guest checkout is supported. A guest cart is keyed by an anonymous session and merged on login.
- Staff roles (Django Groups + model permissions, checked by DRF `DjangoModelPermissions` plus custom role checks): **Owner, Store Manager, Catalogue Manager, Inventory Manager, Order Operations, Customer Support, Content Editor, Marketing, Analyst (read-only)**.
- Next.js `/admin` routes are protected by middleware, which checks `GET /api/v1/auth/me/` → `is_staff`. The API enforces permissions independently. The frontend gate is UX only.

## 5. Frontend (Next.js)

### Stack
Next.js (App Router, latest stable), React, TypeScript `strict`, Tailwind CSS v4, Framer Motion (`motion`), React Bits (via the shadcn registry), shadcn/ui (Radix), TanStack Query (client mutations and cart), React Hook Form + Zod, and `openapi-typescript` + `openapi-fetch` for the typed API client. Tests use Vitest, Testing Library and Playwright.

### Layout
```
frontend/
  src/
    app/
      (storefront)/  layout.tsx page.tsx
        [category]/ ...  products/[slug]/  collections/[slug]/  search/
        cart/  checkout/  account/ (orders, addresses, wishlist, measurements, returns)
      (admin)/admin/ layout.tsx  dashboard/ products/ inventory/ orders/ customers/
        returns/ promotions/ reviews/ cms/ settings/ ...
      api/revalidate/route.ts     # Django → ISR tag revalidation (shared secret)
      sitemap.ts robots.ts
    components/ ui/ commerce/ editorial/ motion/ admin/
    lib/ api/ (schema.d.ts generated, client.ts, server.ts) format/ seo/ analytics/
    config/ brand.ts
    styles/ tokens.css themes/
  tests/ e2e/
```

- Server Components by default. Client components only for interactivity (cart, filters, gallery, motion).
- PLP filter and sort state lives in URL search params (shareable, SEO-crawlable canonical rules).
- The cart is server-side (Django). The client caches it with TanStack Query and uses optimistic updates for quantity changes.
- SEO: `generateMetadata` per route, JSON-LD (`Product`, `Offer`, `BreadcrumbList`, `Organization`), canonical URLs, `sitemap.ts` fed from the API.

## 6. Infrastructure

- Docker Compose for dev (`docker-compose.yml`) and production (`docker-compose.prod.yml`, Phase 8).
- Services: `caddy`, `frontend`, `backend`, `worker`, `beat`, `postgres`, `redis`, `mailpit` (dev), `s3` (dev, SeaweedFS) + `s3-init` (bucket policy).
- Media: S3-compatible (AWS S3, Cloudflare R2 or DigitalOcean Spaces in production, SeaweedFS in dev, since MinIO no longer publishes container images). Admin uploads go **direct to S3 via presigned POST**, and Django then records the asset and generates renditions asynchronously.
- Config: all of it from environment (`django-environ`). `.env.example` is the canonical list.

## 7. Integration abstractions

Each one is a `Protocol` with a registry selected by setting, plus a `console`/`fake` implementation for dev and tests:
- `PaymentGateway`: `RazorpayGateway`, `CodGateway`
- `ShippingProvider`: `check_serviceability`, `create_shipment`, `get_label`, `track`, `cancel`. Implementations: `ManualProvider` (dev/initial ops) and a real aggregator adapter (e.g. Shiprocket / Delhivery) in Phase 7.
- `EmailProvider`: SMTP (Mailpit in dev), with SES/Postmark/Resend adapters
- `SmsProvider`: console, with an MSG91 or similar DLT-compliant adapter (Indian SMS needs DLT template registration)

## 8. Architectural decision log

| ID | Decision | Status |
|---|---|---|
| ADR-001 | Modular monolith (Django + Next.js), Docker Compose, no microservices | Accepted |
| ADR-002 | Same-origin via Caddy, session cookie auth + CSRF (no JWT) | Accepted |
| ADR-003 | Money as integer paise and a `Money` value object | Accepted |
| ADR-004 | Service layer for all writes. `import-linter` enforces app boundaries. | Accepted |
| ADR-005 | PostgreSQL FTS + trigram for search, with an abstraction for a future engine | Accepted |
| ADR-006 | GST via data-driven `TaxRule` slabs, prices GST-inclusive (B2C MRP convention) | Accepted |
| ADR-007 | OpenAPI (drf-spectacular) is the contract, and the frontend types are generated from it, with a CI diff check | Accepted |
| ADR-008 | Next.js admin is primary and Django Admin is superuser break-glass at `/django-admin/` | Accepted |
| ADR-009 | Unsloth excluded from the stack | Accepted |
| ADR-010 | Brand identity is runtime config, and production refuses the dev identity | Accepted |
| ADR-012 | Python 3.14 (stdlib `uuid.uuid7`) and Django 6.1. Email uses the new `MAILERS` setting, since `EMAIL_*` settings are deprecated in 6.1. | Accepted |
| ADR-013 | Dev seeding lives in a top-level `devtools` app outside the domain packages (it touches every app). It refuses to run in production. | Accepted |
| ADR-011 | Dev object storage is SeaweedFS (Apache-2.0). MinIO images are no longer published. Only standard S3 APIs are used (boto3 / django-storages, bucket policy), so production can be any S3-compatible service. | Accepted |

## 9. Reference resource evaluation

**React Bits** (reactbits.dev): a library of 200+ animated React components, installable via `npx shadcn@latest add @react-bits/<Name>-<JS|TS>-<CSS|TW>`. We use the TS + Tailwind variants. The selection and rejection reasoning is in `design-system.md` §6. Per-component dependencies (some use GSAP, motion, OGL or three.js) are confirmed at install time, and WebGL/GSAP components load lazily on the client only.

**MotionSites** (motionsites.ai): a catalogue of AI website *prompts* and design inspiration, with categories including Fashion and Ecommerce. Its gallery renders client-side, so this review did not catalogue individual examples. The brief says to take inspiration, not copy. Our motion language (thread line, curtain wipe, fabric hover, split-text campaign reveals) is original and defined in the design system. Fashion-category references will be reviewed visually during Phase 3 design, and the takeaways recorded here, as patterns only and never assets or layouts lifted wholesale.

**Unsloth** (github.com/unslothai/unsloth): an open-source library for fast, memory-efficient fine-tuning and RL of open LLMs (Llama, Qwen, Gemma, Mistral, etc.). It mainly targets NVIDIA GPUs. **Verdict: not relevant to the commerce runtime, and not installed.** Possible future, *offline-only* uses, in a separate repository: fine-tuning a small model to draft product descriptions from structured attributes (always human-reviewed), or classifying support and return reasons. Any such output would enter the platform only as admin-reviewed content through the normal APIs.
