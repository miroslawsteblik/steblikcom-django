# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run dev server
run:
    uv run python manage.py runserver

run-dev:
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml up

run-prod:
    docker compose -f infra/compose.yaml -f infra/compose.prod.yaml up -d

# add app
add app="":
    uv run python manage.py startapp {{app}}

# Make migrations for all apps or a specific app: `just mm sources`
mm app="":
    uv run python manage.py makemigrations {{app}}

# Apply migrations
migrate:
    # uv run python manage.py migrate
    docker compose -f infra/compose.yaml -f infra/compose.dev.yaml exec web uv run python apps/web/manage.py migrate


# Open Django shell
shell:
    uv run python manage.py shell_plus

# Create superuser
superuser:
    uv run python manage.py createsuperuser

# Run tests
test:
    uv run python manage.py test

# Lint + format
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Bring up the full stack (later, when you add docker)
up:
    docker compose up -d

down:
    docker compose down

# Tail celery worker logs (later)
celery:
    uv run celery -A config worker -l info

beat:
    uv run celery -A config beat -l info
