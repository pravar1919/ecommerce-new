# Testing Strategy

A task is **not complete** until its tests pass and the result is recorded in `PROJECT_STATUS.md`.

## Backend (pytest + pytest-django, factory_boy)
| Layer | What | Target |
|---|---|---|
| Models | Constraints actually enforced by the DB (`IntegrityError` tests), state-machine transitions | Every `CheckConstraint` / `UniqueConstraint` |
| Services | **Primary focus.** Pricing, GST split, discount allocation, reservations, order placement, payment confirmation, webhooks, refunds, returns, cancellations | ≥ 90% branch coverage on `services.py` in checkout, orders, payments, inventory, pricing and promotions |
| Concurrency | `TransactionTestCase` with threads: two customers buying the last unit, concurrent coupon redemptions at the limit, concurrent refunds exceeding the captured amount | Exactly-one-wins assertions |
| Idempotency | Duplicate place-order / verify / webhook / refund calls → single effect | |
| API | Status codes, error envelope codes, permissions (anon / customer / other customer / each staff role), no price accepted from the client | Every endpoint |
| Security | Razorpay signature tampering, webhook replay, IDOR on orders/addresses, CSRF required on unsafe methods | |
| Contract | `manage.py spectacular --validate --fail-on-warn`. Schema snapshot diff in CI. | |
| Tasks | Celery tasks run eagerly in tests and call services | |

Golden-file tests for GST: a fixture table of (price, qty, discount, intra/inter-state) → expected taxable/CGST/SGST/IGST in paise.

Tooling: `ruff check`, `ruff format --check`, `mypy` (django-stubs, strict on `services.py`), `import-linter` (app boundaries), `pytest --cov`.

## Frontend
| Layer | Tool | What |
|---|---|---|
| Static | `tsc --noEmit`, ESLint (next/core-web-vitals, jsx-a11y), Prettier | Zero errors |
| Unit | Vitest + Testing Library | Formatting (INR, dates), filter/URL state, size selector logic, reduced-motion fallbacks, form validation |
| Component a11y | `vitest-axe` | Primitives and commerce components |
| E2E | Playwright (Chromium + WebKit mobile viewport) | Browse → PLP filter → PDP select size → add to bag → checkout (Razorpay test mode / stubbed gateway) → order confirmation. COD flow. Login/merge cart. Return request. Admin: create product + variant + stock, publish, see on storefront. CMS: edit hero, publish, revalidate. |
| Visual | Playwright screenshots of key templates at 375 / 768 / 1440 | Reviewed on change |
| Performance | Lighthouse CI on home, PLP, PDP (mobile) | Budgets in `design-system.md` §9 |

## Environments & data
- Tests use factories, never the dev seed. The dev seed (`manage.py seed_dev`) is idempotent, refuses to run when `ENVIRONMENT=production`, and labels all placeholder media `DEV PLACEHOLDER`.
- External providers in tests: fake gateways (`FakeRazorpayGateway`, `FakeShippingProvider`, `ConsoleEmail`, `ConsoleSms`). One opt-in, nightly Razorpay **test-mode** integration suite runs with real test keys.

## Commands
```
make test-backend     # pytest + coverage inside the backend container (forces config.settings.test)
make lint-backend     # ruff check + ruff format --check + import-linter (mypy planned)
make schema           # regenerate + validate backend/schema/openapi.yaml
make check-backend    # all of the above + makemigrations --check + schema drift
make test-frontend    # npm run typecheck && npm run lint && npm run test
make check-frontend   # + prettier, API types and cn tables drift
make e2e              # npx playwright test (compose stack through Caddy)
make lighthouse       # mobile budgets (design-system.md §9) on a production build in .next-lighthouse
make check            # all of the above, used before marking a milestone complete
```

## Milestone gate
After every phase: backend tests, frontend checks and E2E smoke all green. Manual verification in the browser at mobile and desktop widths. `PROJECT_STATUS.md` updated with results and known issues.
