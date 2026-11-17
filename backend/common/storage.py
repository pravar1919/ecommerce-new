from django.conf import settings
from storages.backends.s3 import S3Storage


class PublicMediaStorage(S3Storage):
    """Anonymously readable prefix (bucket policy). URLs point at the public base/CDN."""

    location = "public"
    querystring_auth = False

    def url(self, name, parameters=None, expire=None, http_method=None):
        base = settings.MEDIA_PUBLIC_BASE_URL
        if base:
            return f"{base.rstrip('/')}/{name.lstrip('/')}"
        return super().url(name, parameters, expire, http_method)


class PrivateMediaStorage(S3Storage):
    """Private prefix; always served through short-lived presigned URLs."""

    location = "private"
    querystring_auth = True
    querystring_expire = 300
    file_overwrite = False
