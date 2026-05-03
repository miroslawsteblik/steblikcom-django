"""
Base settings shared by every environment.
Reads from environment variables via django-environ.
Never set DEBUG = True here. Never put secrets here.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # apps/web/
ROOT_DIR = BASE_DIR.parent.parent  # repo root


env = environ.Env()
# Read .env from repo root if present (dev). In prod, env vars come from the
# host/compose file, so a missing .env is fine.
env_file = ROOT_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
BLOG_POSTS_DIR = env("BLOG_POSTS_DIR", default=str(ROOT_DIR / "content" / "posts"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_extensions",
    # third-party
    "django_htmx",
    # local
    "steblik.pages",
    "steblik.blog",
    "steblik.accounts",
    "steblik.emailing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.site_meta",
            ],
        },
    },
]

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
LOGIN_REDIRECT_URL = "/me/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
AUTH_USER_MODEL = "accounts.User"
ACCOUNT_ADAPTER = "steblik.accounts.adapter.AccountAdapter"
ACCOUNT_SIGNUP_FORM_CLASS = "steblik.accounts.forms.CustomSignupForm"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = ROOT_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email goes through the Resend wrapper (steblik.emailing).
EMAIL_BACKEND = "steblik.emailing.backend.ResendEmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@steblik.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
RESEND_API_KEY = env("RESEND_API_KEY", default="")

# Session and CSRF — strictly necessary cookies only (per privacy policy).
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days, matches policy
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Django's default; required for the token to work
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Security defaults — overridden per environment as needed.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# Content-Security-Policy (django-csp 4.0)
# All assets are self-hosted; no CDNs, no external fonts, no inline scripts.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
    }
}
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Site-wide metadata exposed to templates via context processor
SITE_META = {
    "name": "steblik.com",
    "full_name": "Miroslaw Steblik",
    "tagline": "Data engineer. Homelab tinkerer.",
    "email": "data@steblik.com",
    "github": "https://github.com/miroslawsteblik",
    "linkedin": "https://linkedin.com/in/miroslawsteblik",
    "mastodon": "",  # leave empty to hide
    "rss_url": "",  # leave empty to hide
}

SITE_ID = 1
SITE_DOMAIN = env.str("SITE_DOMAIN", default="localhost:8000")
