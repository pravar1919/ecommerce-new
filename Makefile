# Developer shortcuts. Backend commands run inside the compose `backend` container.
DC  := docker compose
RUN := $(DC) exec -T backend uv run --no-sync

.PHONY: up up-app down logs migrate seed shell test-backend lint-backend schema check-backend check

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

check: check-backend
