import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_health_ok(api):
    r = api.get("/api/v1/health/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "checks": {"database": "ok", "cache": "ok"}}


def test_request_id_generated_and_propagated(api):
    r = api.get("/api/v1/health/live/")
    assert len(r["X-Request-ID"]) == 32
    r = api.get("/api/v1/health/live/", HTTP_X_REQUEST_ID="caddy-req-12345678")
    assert r["X-Request-ID"] == "caddy-req-12345678"
    r = api.get("/api/v1/health/live/", HTTP_X_REQUEST_ID="bad id with spaces")
    assert r["X-Request-ID"] != "bad id with spaces"


def test_error_envelope_shape(api):
    r = api.get("/api/v1/catalog/products/does-not-exist/", HTTP_X_REQUEST_ID="req-abcdef123")
    assert r.status_code == 404
    body = r.json()["error"]
    assert body["code"] == "not_found"
    assert body["request_id"] == "req-abcdef123"


def test_openapi_schema_valid(tmp_path):
    out = tmp_path / "schema.yml"
    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(out))
    assert out.read_text().startswith("openapi: 3")


def test_production_refuses_dev_brand(settings):
    from common.checks import brand_identity_approved

    settings.ENVIRONMENT = "production"
    settings.BRAND_NAME = settings.DEV_BRAND_NAME
    assert [e.id for e in brand_identity_approved(None)] == ["common.E001"]
    settings.BRAND_NAME = "Approved Name"
    assert brand_identity_approved(None) == []
