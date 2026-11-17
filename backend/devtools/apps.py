from django.apps import AppConfig


class DevtoolsConfig(AppConfig):
    """Development-only tooling (seed data). Sits outside the domain packages because it
    legitimately touches every app; its commands refuse to run in production."""

    name = "devtools"
