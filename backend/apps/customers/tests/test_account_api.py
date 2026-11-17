import pytest
from django.db import IntegrityError

from apps.customers.models import Address

pytestmark = pytest.mark.django_db

ADDRESS = {
    "full_name": "Asha Rao",
    "phone": "9812345678",
    "line1": "12 MG Road",
    "city": "Pune",
    "state_code": "27",
    "pincode": "411001",
}


def test_first_address_becomes_default_and_switching_default(auth_api, user):
    a1 = auth_api.post("/api/v1/account/addresses/", ADDRESS).json()
    assert a1["is_default_shipping"] and a1["is_default_billing"] and a1["phone"] == "+919812345678"
    assert a1["state_name"] == "Maharashtra"
    a2 = auth_api.post(
        "/api/v1/account/addresses/", {**ADDRESS, "line1": "9 Park St", "is_default_shipping": True}
    )
    assert a2.status_code == 201
    rows = {a["id"]: a for a in auth_api.get("/api/v1/account/addresses/").json()}
    assert rows[a2.json()["id"]]["is_default_shipping"] and not rows[a1["id"]]["is_default_shipping"]
    r = auth_api.post(f"/api/v1/account/addresses/{a1['id']}/set-default/")
    assert r.json()["is_default_shipping"]
    assert Address.objects.filter(customer__user=user, is_default_shipping=True).count() == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("pincode", "011001"),
        ("pincode", "41100"),
        ("phone", "5812345678"),
        ("state_code", "99"),
        ("gstin", "BADGSTIN"),
    ],
)
def test_address_validation(auth_api, field, value):
    r = auth_api.post("/api/v1/account/addresses/", {**ADDRESS, field: value})
    assert r.status_code == 400
    assert field in r.json()["error"]["fields"]


def test_cannot_access_another_customers_address(api, user, other_user):
    api.force_authenticate(other_user)
    theirs = api.post("/api/v1/account/addresses/", ADDRESS).json()["id"]
    api.force_authenticate(user)
    assert api.get(f"/api/v1/account/addresses/{theirs}/").status_code == 404
    assert api.patch(f"/api/v1/account/addresses/{theirs}/", {"city": "X"}).status_code == 404
    assert api.delete(f"/api/v1/account/addresses/{theirs}/").status_code == 404
    assert api.post(f"/api/v1/account/addresses/{theirs}/set-default/").status_code == 404
    assert api.get("/api/v1/account/addresses/").json() == []


def test_one_default_address_enforced_by_db(user):
    profile = user.customer_profile
    Address.objects.create(
        customer=profile, **{**ADDRESS, "phone": "+919812345678"}, is_default_shipping=True
    )
    with pytest.raises(IntegrityError):
        Address.objects.create(
            customer=profile, **{**ADDRESS, "phone": "+919812345678"}, is_default_shipping=True
        )


def test_anonymous_cannot_access_account(api):
    assert api.get("/api/v1/account/addresses/").status_code == 403
    assert api.get("/api/v1/account/profile/").json()["error"]["code"] == "not_authenticated"


def test_profile_update(auth_api, user):
    r = auth_api.patch("/api/v1/account/profile/", {"first_name": "Asha M", "marketing_email_opt_in": True})
    assert r.status_code == 200 and r.json()["first_name"] == "Asha M"
    user.refresh_from_db()
    assert user.first_name == "Asha M" and user.customer_profile.marketing_email_opt_in


def test_measurement_profile_validated_against_definitions(auth_api, catalog):
    ok = auth_api.post(
        "/api/v1/account/measurements/",
        {"label": "Wedding fitting", "body_measurements": {"chest": "101.6", "waist": 86}},
    )
    assert ok.status_code == 201, ok.json()
    assert ok.json()["body_measurements"] == {"chest": "101.6", "waist": "86.0"}

    bad = auth_api.post(
        "/api/v1/account/measurements/", {"label": "x", "body_measurements": {"chest": 20, "elbow": 30}}
    )
    assert bad.status_code == 400
    fields = bad.json()["error"]["fields"]
    assert set(fields) == {"chest", "elbow"}
