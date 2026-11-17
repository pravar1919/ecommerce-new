from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "common"
    verbose_name = "Common kernel"

    def ready(self) -> None:
        from . import checks  # noqa: F401  (registers system checks)
