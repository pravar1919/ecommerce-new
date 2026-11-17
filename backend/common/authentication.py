from rest_framework.authentication import SessionAuthentication


class CsrfEnforcedSessionAuthentication(SessionAuthentication):
    """Session auth that enforces CSRF on unsafe methods for anonymous requests too.

    DRF's default only checks CSRF once a user is authenticated, which would leave
    login/register open to login-CSRF. Webhook views opt out with authentication_classes = [].
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None and request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            self.enforce_csrf(request)
        return result


try:  # describe the auth scheme in OpenAPI
    from drf_spectacular.authentication import SessionScheme

    class CsrfEnforcedSessionScheme(SessionScheme):
        target_class = "common.authentication.CsrfEnforcedSessionAuthentication"
except ImportError:  # pragma: no cover
    pass
