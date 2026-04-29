
# ---- builder ----------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps first for layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
# Copy the rest of the source.
COPY . .

# Install the project itself (without dev deps).
RUN uv sync --frozen --no-dev

# Build static files into /app/staticfiles.
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=build \
    DJANGO_ALLOWED_HOSTS=build \
    DATABASE_URL=sqlite:///build.sqlite3 \
    RESEND_API_KEY=build \
    BLOG_POSTS_DIR=/tmp \
    EMAIL_HOST=build \
    EMAIL_HOST_USER=build \
    EMAIL_HOST_PASSWORD=build \
    uv run python apps/web/manage.py collectstatic --noinput


# ---- runtime ----------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app


# Copy the venv and the source from the builder stage.
COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--chdir", "apps/web", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-"]
