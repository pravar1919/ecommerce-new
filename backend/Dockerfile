# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------- base
FROM python:3.14-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# ---------------------------------------------------------------- dev (compose: code is bind-mounted)
FROM base AS dev
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen
COPY . .
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------------------------------------------------------------- production build
FROM base AS build
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
COPY . .
RUN DJANGO_SECRET_KEY=collectstatic-only DATABASE_URL=sqlite:///tmp/x.db \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    /app/.venv/bin/python manage.py collectstatic --noinput -v0

# ---------------------------------------------------------------- production runtime (non-root)
FROM python:3.14-slim-bookworm AS prod
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production
RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app
COPY --from=build --chown=app:app /app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live/').status==200 else 1)"
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--access-logfile", "-"]
