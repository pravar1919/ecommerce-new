# Implementation Roadmap

Small, buildable increments. Each phase ends with the milestone gate in `testing-strategy.md`.

## Phase 1: Initialisation, architecture, brand & design system ✅ (Direction B approved 2026-11-17)
- Requirements audit, architecture, database design, API conventions, commerce workflows
- Three brand directions, configurable brand metadata, dev identity
- Design system: tokens, type, grid, motion, React Bits selection, a11y, perf budgets
- Repo init, `.env.example`, `docker-compose.yml` (infra services), Caddyfile, README, PROJECT_STATUS
- **Exit:** docs reviewed, infra stack boots (`docker compose up -d`), brand direction chosen

## Phase 2: Django foundation, models, auth, catalogue ✅ (2026-11-17)
1. `uv init` backend, settings split, Dockerfile, health endpoint, structlog, error envelope, drf-spectacular
2. `common` kernel: base models, Money, exceptions, pagination, idempotency store
3. `accounts` (custom user, roles), `customers` (profile, addresses, measurement profiles)
4. `categories`, `attributes`, `catalog` (products, variants, media, size charts, measurement definitions)
5. `inventory` (levels, ledger, reservations), `pricing` (tax classes and rules, quote primitives)
6. Catalogue read API with filters, facets, sorting, FTS search and suggestions
7. Django Admin registrations, `seed_dev` command with labelled placeholder data
- **Exit:** migrations clean, ≥ 90% service coverage for inventory/pricing, OpenAPI validates, catalogue API manually verified

## Phase 3: Frontend design system, homepage, navigation ✅ (2026-11-17)
1. Next.js scaffold, Tailwind v4 tokens, themes, fonts, typed API client generation
2. UI primitives (shadcn/ui restyled), motion wrappers, React Bits installs
3. Header / mega-menu / mobile nav / announcement bar / footer
4. `cms` app (SiteSettings, pages, versions, blocks, media assets) + public CMS API
5. Homepage composed from CMS blocks (all 14 sections)
- **Exit:** Lighthouse mobile within budgets, axe clean, reduced-motion verified

## Phase 4: Discovery & product pages
Category editorial pages, PLP grid, filter sheet/rail, sort, search with suggestions, quick view, PDP (gallery, zoom, colour/size, size guide, MTM entry point, pincode check, related products, complete the look), wishlist, reviews display, SEO metadata + JSON-LD + sitemap.

## Phase 5: Cart, checkout, payments, orders
Cart API and drawer, guest/merge, promotions and coupons, checkout session + quotes + reservations, Razorpay (orders, verify, webhooks), COD, order placement, confirmation, account order history, invoices (PDF), cancellations.
- **Exit:** concurrency and idempotency suites green, Razorpay test-mode E2E green

## Phase 6: Administration, inventory, CMS
Next.js `/admin`: dashboard and sales analytics, products/variants/media workflow (presigned upload, renditions, reorder, colour mapping), bulk import with dry run, categories, collections, attributes, inventory (levels, adjustments, ledger, low stock), orders (timeline, transitions, refunds), customers, promotions/coupons, reviews moderation, CMS page builder with draft/schedule/publish and preview, staff and roles, audit log.

## Phase 7: Shipping, returns, notifications, SEO
Shipping provider adapter (aggregator), pincode import, shipments and labels, tracking, returns/RMA flow, credit notes, refunds, email templates (MJML-built) and SMS (DLT), notification log, abandoned cart, phone OTP login, SEO polish (canonical rules for filters, structured data validation, OG images).

## Phase 8: Hardening & production
Security review (OWASP ASVS L2 checklist, admin 2FA, CSP), load tests on catalogue and checkout, query optimisation and indexes, caching, image CDN, analytics partitions, Sentry, backups and restore drill, `docker-compose.prod.yml`, staging go-live, Razorpay live checklist, runbooks.

## Dependencies on the business (blocking items)
| Needed | Blocks | Owner |
|---|---|---|
| Brand direction + name approval | Phase 3 visual finalisation (dev identity is used meanwhile) | Founder |
| Real product photography + catalogue data | Production launch (dev uses labelled placeholders) | Merchandising |
| GSTIN, legal entity, registered address, CA sign-off on tax rules | Invoices, production | Finance |
| Razorpay account + KYC | Live payments | Finance |
| Shipping aggregator account | Phase 7 real integration | Ops |
| Return / exchange / MTM policy text | Phase 7 | Founder / Legal |
| SMS DLT registration (entity + templates) | SMS in production | Ops |
