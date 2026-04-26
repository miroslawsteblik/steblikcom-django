# steblik.com

Personal website, blog, and data engineering lab. Live at [steblik.com](https://steblik.com).

## Stack

| Layer | Choice |
|---|---|
| Framework | Django 5.1 |
| Auth | django-allauth (email-only, mandatory verification) |
| Blog | File-based Markdown with YAML frontmatter |
| Email | Resend (SMTP in prod, console in dev) |
| Static files | WhiteNoise |
| Database | SQLite (WAL mode) |
| Proxy / TLS | Caddy |
| Deployment | Docker Compose |
| Python tooling | uv, ruff |

## Local development

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/miroslawsteblik/steblikcom-django.git
cd steblikcom-django
uv sync
cp .env.example .env          # edit values
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Site at `http://localhost:8000` · Admin at `http://localhost:8000/manage/`

## Writing a blog post

Posts live in `apps/blog/posts/` as a directory with `index.md`:

```yaml
---
title: My Post Title
slug: my-new-post
date: 2026-04-26
tags: [python, dbt]
summary: One sentence shown on the list page.
draft: false
premium: false      # true = login required
card_image: cover.png
---
```

A server restart is required in production to pick up new posts (LRU cache).

## Sending announcements

Newsletters are sent via the Django admin (`/manage/` → Announcements).

To announce a new post, set **Post slug** to the post's slug — the email template renders automatically. Requires `RESEND_API_KEY` in production; simulated locally.

```bash
# CLI alternative
python manage.py send_announcement <id> --dry-run
python manage.py send_announcement <id>
```

## Project structure

```
apps/
  accounts/    — custom User model, announcements, email service
  blog/        — file-based blog (Markdown posts, views, services)
  pages/       — static pages (home, about, experience)
config/        — settings, URLs, context processors
static/css/    — CSS layers: tokens → base → layout → prose → components
templates/
  emails/      — transactional + newsletter HTML templates
  admin/       — Django admin overrides
```

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate: `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG` | Yes | `False` in prod |
| `ALLOWED_HOSTS` | Yes | Comma-separated |
| `CSRF_TRUSTED_ORIGINS` | Yes | Comma-separated, needed behind Caddy |
| `SITE_DOMAIN` | Yes | Used in email links (`steblik.com` in prod) |
| `DATABASE_NAME` | No | Defaults to `db.sqlite3` |
| `RESEND_API_KEY` | Prod | Set as host env var, not in `.env` |
| `EMAIL_HOST` | Prod | `smtp.resend.com` |
| `EMAIL_HOST_USER` | Prod | `resend` |
| `EMAIL_HOST_PASSWORD` | Prod | Resend API key |
| `DEFAULT_FROM_EMAIL` | No | Default `data@steblik.com` |

## Deployment

```bash
git pull
docker compose up -d --build
```

## Linting

```bash
uv run ruff check .
uv run ruff format .
```
