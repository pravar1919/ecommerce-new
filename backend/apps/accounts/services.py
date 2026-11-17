from django.conf import settings
from django.contrib.auth import authenticate, login, logout, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from common.exceptions import DomainError

from .models import User


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    status_code = 400
    default_message = "Email or password is incorrect."


class EmailTaken(DomainError):
    code = "email_taken"
    status_code = 409
    default_message = "An account with this email already exists."


class InvalidResetToken(DomainError):
    code = "invalid_token"
    default_message = "This reset link is invalid or has expired."


def create_user(*, email: str, password: str, first_name: str = "", last_name: str = "", phone=None) -> User:
    email = email.strip().lower()
    if User.objects.filter(email__iexact=email).exists():
        raise EmailTaken()
    user = User(email=email, first_name=first_name.strip(), last_name=last_name.strip(), phone=phone or None)
    password_validation.validate_password(password, user)
    user.set_password(password)
    user.save()
    return user


def login_user(request, *, email: str, password: str) -> User:
    user = authenticate(request, username=email.strip().lower(), password=password)
    if user is None or not user.is_active:
        raise InvalidCredentials()
    login(request, user)  # rotates the session key (session-fixation safe)
    return user


def logout_user(request) -> None:
    logout(request)


def request_password_reset(*, email: str) -> None:
    """Always succeeds from the caller's perspective (no account enumeration)."""
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.PASSWORD_RESET_URL}?uid={uid}&token={token}"
    from .tasks import send_password_reset_email

    transaction.on_commit(lambda: send_password_reset_email.delay(user.email, link))


def confirm_password_reset(*, uid: str, token: str, new_password: str) -> User:
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as exc:
        raise InvalidResetToken() from exc
    if not default_token_generator.check_token(user, token):
        raise InvalidResetToken()
    password_validation.validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
