# Developer shortcuts. Backend commands run inside the compose `backend` container.
DC  := docker compose
RUN := $(DC) exec -T backend uv run --no-sync

.PHONY: up up-app down logs migrate seed shell test-backend lint-backend schema check-backend \
        test-frontend check-frontend e2e lighthouse check

up:            ## infrastructure only (postgres, redis, s3, mailpit)
	$(DC) up -d --wait postgres redis s3 mailpit && $(DC) up s3-init
up-app:        ## infrastructure + backend, worker, beat
	$(DC) --profile app up -d --wait backend worker beat
down:
	$(DC) --profile app down
logs:
	$(DC) --profile app logs -f --tail=100 backend worker beat
migrate:
	$(RUN) python manage.py migrate
seed:          ## idempotent dev data with labelled placeholder images
	$(RUN) python manage.py seed_dev
shell:
	$(RUN) python manage.py shell

test-backend:
	$(RUN) pytest -q --cov --cov-report=term-missing:skip-covered
lint-backend:
	$(RUN) ruff check . && $(RUN) ruff format --check . && $(RUN) lint-imports
schema:        ## regenerate the OpenAPI contract (commit the result)
	$(RUN) python manage.py spectacular --validate --fail-on-warn --file schema/openapi.yaml
check-backend: lint-backend test-backend schema
	$(RUN) python manage.py makemigrations --check --dry-run
	git diff --exit-code -- backend/schema/openapi.yaml

# Frontend commands run on the host (Playwright browsers and Lighthouse's Chrome live there).
FE := cd frontend &&

test-frontend: ## typecheck, lint, unit tests
	$(FE) npm run typecheck && npm run lint && npm run test
check-frontend: test-frontend ## + formatting and generated-file drift (API types, cn tables)
	$(FE) npm run format:check && npm run api:check && npm run cn:check
e2e:           ## Playwright against the compose stack through Caddy (make up-app first)
	$(FE) npx playwright test
lighthouse:    ## mobile budgets (design-system.md §9) against a local production build
	$(FE) export NEXT_DIST_DIR=.next-lighthouse && npm run build && \
	  (npx next start -p 3100 & echo $$! > .lh.pid; sleep 3) && \
	  LH_BASE_URL=http://localhost:3100 npm run lighthouse; s=$$?; kill $$(cat .lh.pid); rm -f .lh.pid; exit $$s

check: check-backend check-frontend
