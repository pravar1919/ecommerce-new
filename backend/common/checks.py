from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def brand_identity_approved(app_configs, **kwargs):
    """Production must never ship with the temporary development identity."""
    if settings.ENVIRONMENT == "production" and settings.BRAND_NAME == settings.DEV_BRAND_NAME:
        return [
            Error(
                "BRAND_NAME is the development identity. Set the approved brand before deploying.",
                id="common.E001",
            )
        ]
    return []


@register(Tags.security, deploy=True)
def no_dev_secret_in_production(app_configs, **kwargs):
    if settings.ENVIRONMENT == "production" and "dev-only" in settings.SECRET_KEY:
        return [Error("DJANGO_SECRET_KEY is a development placeholder.", id="common.E002")]
    return []
