# List available commands
default:
    @just --list

# ── Dependencies ──────────────────────────────────────────────────────────────

install:
    uv sync

# ── Dev (Docker) ──────────────────────────────────────────────────────────────

# Start dev stack (hot reload, runserver, dev settings)
run:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml up

run-dev:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml up

# ── Prod (Docker) ─────────────────────────────────────────────────────────────

# Start prod stack (gunicorn + Caddy)
run-prod:
    docker compose -f infra/compose.yaml -f infra/compose.prod.yaml up -d

# ── Database ──────────────────────────────────────────────────────────────────

# Apply migrations
migrate:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml run --rm web uv run python apps/web/manage.py migrate

# Make migrations for all apps or a specific app: `just mm` or `just mm accounts`
mm app="":
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml run --rm web uv run python apps/web/manage.py makemigrations {{app}}

# ── Django management ─────────────────────────────────────────────────────────

# Open Django shell (requires dev stack to be running)
shell:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml exec web python apps/web/manage.py shell_plus

# Add to justfile
dbshell:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml exec db psql -U steblik steblik

# Create a superuser
superuser:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml run --rm web uv run python apps/web/manage.py createsuperuser

# Add a new Django app
add app="":
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml run --rm web uv run python apps/web/manage.py startapp {{app}}

# ── Tests & linting ───────────────────────────────────────────────────────────

# Run test suite
test:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml run --rm web python -m pytest

# Lint + format (runs locally — ruff doesn't need Django)
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# ── Stack control ─────────────────────────────────────────────────────────────

up:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml up -d

down:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml down
