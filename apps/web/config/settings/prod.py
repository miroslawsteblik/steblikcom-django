"""Production settings. Loaded only when DJANGO_SETTINGS_MODULE=config.settings.prod."""

from .base import *  # noqa
from .base import env  # noqa: F401

DEBUG = False

# ALLOWED_HOSTS comes from base via env; assert it is non-empty so a
# misconfigured deploy fails loudly rather than serving traffic openly.
assert ALLOWED_HOSTS, "DJANGO_ALLOWED_HOSTS must be set in production"  # noqa: F405

# HTTPS / cookies
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS — ramp up after you're confident TLS is stable on every host you serve.
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days; raise to 1 year once stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # flip to True only after preload list submission

# Logging — keep server logs in line with the 14-day retention promise.
# In Compose, this means your log driver / volume rotation must enforce 14d.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
