"""Dev settings. DEBUG = True is OK here, and only here."""

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"]  # nosec B104

# Friendlier email backend in dev — write emails to the console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]

# Looser cookies in dev (HTTP, not HTTPS).
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Serve static files directly without hashing or compression in dev.
# The production backend (CompressedManifestStaticFilesStorage) requires
# collectstatic and hashed filenames, which breaks live CSS editing.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

INSTALLED_APPS = INSTALLED_APPS + ["django_browser_reload"]
MIDDLEWARE = MIDDLEWARE + ["django_browser_reload.middleware.BrowserReloadMiddleware"]
