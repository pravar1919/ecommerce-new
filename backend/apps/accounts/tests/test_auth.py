import re

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.db import IntegrityError

from apps.accounts.models import User
from conftest import PASSWORD

pytestmark = pytest.mark.django_db


def prime_csrf(client) -> str:
    r = client.get("/api/v1/auth/csrf/")
    assert r.status_code == 200
    return client.cookies["csrftoken"].value


def test_register_login_me_logout_flow_with_csrf(csrf_api):
    token = prime_csrf(csrf_api)
    r = csrf_api.post(
        "/api/v1/auth/register/",
        {"email": "Groom@Example.com", "password": PASSWORD, "first_name": "Arjun", "phone": "98123 45678"},
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 201, r.json()
    assert r.json()["email"] == "groom@example.com"
    user = User.objects.get(email="groom@example.com")
    assert user.phone == "+919812345678"
    assert user.customer_profile is not None

    assert csrf_api.get("/api/v1/auth/me/").json()["first_name"] == "Arjun"  # registered = logged in
    token = csrf_api.cookies["csrftoken"].value  # rotated on login
    assert csrf_api.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code == 204
    assert csrf_api.get("/api/v1/auth/me/").status_code == 403

    token = prime_csrf(csrf_api)
    r = csrf_api.post(
        "/api/v1/auth/login/", {"email": "GROOM@example.com", "password": PASSWORD}, HTTP_X_CSRFTOKEN=token
    )
    assert r.status_code == 200
    assert csrf_api.get("/api/v1/auth/me/").json()["email"] == "groom@example.com"


def test_login_requires_csrf_even_when_anonymous(csrf_api, user):
    r = csrf_api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "permission_denied"


def test_login_rotates_session_key(api, user):
    api.get("/api/v1/auth/csrf/")
    api.cookies["sessionid"] = "attacker-fixed-session"
    api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD})
    assert api.cookies["sessionid"].value != "attacker-fixed-session"


def test_bad_credentials(api, user):
    r = api.post("/api/v1/auth/login/", {"email": user.email, "password": "wrong-password-1"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_duplicate_email_is_case_insensitive(api, user):
    r = api.post(
        "/api/v1/auth/register/", {"email": user.email.upper(), "password": PASSWORD, "first_name": "X"}
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "email_taken"


def test_weak_password_rejected_with_field_error(api):
    r = api.post("/api/v1/auth/register/", {"email": "a@b.com", "password": "1234567890", "first_name": "X"})
    assert r.status_code == 400
    assert "password" in r.json()["error"]["fields"]


def test_invalid_phone_rejected(api):
    r = api.post(
        "/api/v1/auth/register/",
        {"email": "a@b.com", "password": PASSWORD, "first_name": "X", "phone": "12345"},
    )
    assert r.status_code == 400
    assert "phone" in r.json()["error"]["fields"]


def test_email_unique_constraint_in_db(user):
    with pytest.raises(IntegrityError):
        User.objects.bulk_create([User(email=user.email.upper())])


def test_password_reset_flow(api, user, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        r = api.post("/api/v1/auth/password/reset/", {"email": user.email})
    assert r.status_code == 202
    assert len(mail.outbox) == 1
    uid, token = re.search(r"uid=([^&\s]+)&token=(\S+)", mail.outbox[0].body).groups()

    r = api.post(
        "/api/v1/auth/password/reset/confirm/",
        {"uid": uid, "token": token, "new_password": "a-brand-new-passphrase"},
    )
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.check_password("a-brand-new-passphrase")
    # token is single-use (password hash changed)
    r = api.post(
        "/api/v1/auth/password/reset/confirm/",
        {"uid": uid, "token": token, "new_password": "another-new-passphrase"},
    )
    assert r.json()["error"]["code"] == "invalid_token"


def test_password_reset_does_not_enumerate_accounts(api, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        r = api.post("/api/v1/auth/password/reset/", {"email": "nobody@example.com"})
    assert r.status_code == 202
    assert mail.outbox == []


def test_roles_are_synced_with_permissions():
    roles = {g.name: g for g in Group.objects.prefetch_related("permissions")}
    assert {"Owner", "Catalogue Manager", "Inventory Manager", "Analyst"} <= set(roles)
    analyst = {p.codename for p in roles["Analyst"].permissions.all()}
    assert "view_product" in analyst and not any(
        c.startswith(("add_", "change_", "delete_")) for c in analyst
    )
    assert "change_product" in {p.codename for p in roles["Catalogue Manager"].permissions.all()}
    # ledger is never editable, even by the inventory role
    inv = {p.codename for p in roles["Inventory Manager"].permissions.all()}
    assert "view_stockmovement" in inv and "change_stockmovement" not in inv


def test_me_exposes_roles_for_staff(api, user):
    user.is_staff = True
    user.save()
    user.groups.add(Group.objects.get(name="Analyst"))
    api.force_authenticate(user)
    body = api.get("/api/v1/auth/me/").json()
    assert body["roles"] == ["Analyst"] and "catalog.view_product" in body["permissions"]
