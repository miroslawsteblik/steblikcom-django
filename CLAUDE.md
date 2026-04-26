# CLAUDE.md — steblik.com Django Project

## Project Vision

**Currently:** Personal portfolio/blog site for Miroslaw Steblik, Data Engineer.
**Direction:** Evolve into a **Data Engineering Lab** — selling access to courses, consultations,
and freelance services to individuals and corporate clients.

### Audience split
| Audience | What they want | Entry point |
|---|---|---|
| Individual learners | Courses, premium blog content, guides | Public blog → sign up → members area |
| Corporate clients | Freelance engagements, consulting | Services/Experience page → contact |

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Django 5.1 |
| Auth | django-allauth 65.x (email-only, mandatory verification) |
| Templates | Django templates, custom CSS (no Tailwind) |
| Static files | WhiteNoise (dev: CompressedStatic, prod: CompressedManifest) |
| Blog content | Markdown files with YAML frontmatter (`apps/blog/posts/`) |
| Database | SQLite (WAL mode) |
| Proxy / TLS | Caddy |
| Container | Docker Compose (web + caddy services) |
| Email | Resend via SMTP (`smtp.resend.com:587`) — console backend in DEBUG |
| Python tooling | `uv` (venv + deps), `ruff` (lint + format), `pytest` |
| Deployment | Ubuntu Server homelab, Docker Compose |

---

## Repository Layout

```
steblikcom-django/
├── apps/
│   ├── accounts/          # Custom User model, profile view, admin
│   ├── blog/              # Markdown blog (services.py, views.py, posts/)
│   └── pages/             # Static pages (home, about, experience)
├── config/
│   ├── settings.py        # All settings, env-driven
│   ├── urls.py            # Root URL config
│   ├── context_processors.py  # site_meta + auth-aware nav
│   └── sitemaps.py
├── static/css/
│   ├── 01-tokens.css      # Design tokens (colours, fonts, spacing)
│   ├── 02-base.css
│   ├── 03-layout.css      # Header, nav, banner, footer
│   ├── 04-prose.css       # Blog article prose styles
│   ├── 05-components.css  # Cards, auth forms, paywall, profile, badges
│   └── 06-utilities.css
├── templates/
│   ├── base.html          # Site chrome (nav, footer)
│   ├── account/           # Allauth overrides (login, logout, signup, password reset/change)
│   ├── accounts/          # App templates (profile/dashboard)
│   ├── blog/              # list.html, detail.html
│   └── pages/             # home.html, about.html, experience.html
├── docker-compose.yml
├── Dockerfile
├── Caddyfile
├── .env                   # Local env vars (never commit secrets)
└── pyproject.toml
```

---

## URL Map

| URL | View | Auth |
|---|---|---|
| `/` | `pages:home` | Public |
| `/about/` | `pages:about` | Public |
| `/experience/` | `pages:experience` | Public (anon only in nav) |
| `/blog/` | `blog:post_list` | Public |
| `/blog/<slug>/` | `blog:post_detail` | Public; premium posts require login |
| `/me/` | `accounts:profile` | Login required |
| `/accounts/` | allauth | Public |
| `/manage/` | Django admin | Staff only |

---

## Auth & User Model

- Custom `User` model at `apps/accounts/models.py` (extends `AbstractUser`)
- `AUTH_USER_MODEL = "accounts.User"`
- Login method: **email only** (no username)
- Email verification: **mandatory** (allauth)
- `LOGIN_REDIRECT_URL = "/me/"`
- `ACCOUNT_LOGOUT_REDIRECT_URL = "/"`

### Creating users

- **Admin:** `/manage/` → Users → Add User (set verified flag in EmailAddress inline)
- **CLI:** `python manage.py createsuperuser`
- **Self-registration:** `/accounts/signup/` (sends verification email via Resend in prod)

### Marking existing users as verified (shell)
```python
from allauth.account.models import EmailAddress
EmailAddress.objects.filter(verified=False).update(verified=True, primary=True)
```

---

## Blog System

Posts are Markdown files in `apps/blog/posts/`. Each post is either:
- A single `.md` file: `posts/my-post.md`
- A directory with assets: `posts/my-post/index.md`

### Frontmatter fields
```yaml
---
slug: my-post
title: My Post Title
date: 2026-04-26
tags: [python, dbt]
summary: One-line description shown on list cards.
draft: false          # true = hidden from public list
premium: false        # true = login required to read
card_image: image.png
banner_image: banner.png
---
```

The `lru_cache` on `all_posts()` means post changes require a server restart in production.

---

## Premium Content

- `premium: true` in frontmatter gates the post behind login
- Unauthenticated users see title/tags/date + a paywall CTA
- `premium_locked` bool is passed to `blog/detail.html`
- Premium posts show a lock badge on the blog list

---

## Email Configuration

| Setting | Value |
|---|---|
| Provider | Resend (`smtp.resend.com:587`) |
| From domain | `notifications.steblik.com` (subdomain for reputation isolation) |
| From address | `noreply@notifications.steblik.com` |
| Dev backend | Console (emails printed to terminal when `DEBUG=True`) |
| Prod backend | SMTP (active when `DEBUG=False`) |

`EMAIL_HOST_PASSWORD` (Resend API key) is **not** in `.env` — it is set as a host
environment variable and passed into the container via the `environment:` block in
`docker-compose.yml`. Rotate it at resend.com/api-keys if compromised.

---

## Nav Behaviour (auth-aware)

Controlled in `config/context_processors.py`:

| State | Nav items |
|---|---|
| Anonymous | Blog · About · Experience · **Log in** (button) |
| Logged in | Blog · About · **My Account** |

---

## Site Domain / Allauth

`SITE_DOMAIN` in `.env` controls the domain used in email verification links.
- Dev: `localhost:8000`
- Prod: `steblik.com`

The `PagesConfig.ready()` hook keeps the `django.contrib.sites` Site model in sync
on every `migrate` run.

---

## Environment Variables

| Variable | Required in prod | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `False` in prod |
| `ALLOWED_HOSTS` | Yes | Comma-separated |
| `CSRF_TRUSTED_ORIGINS` | Yes | Comma-separated, needed behind Caddy |
| `SITE_DOMAIN` | Yes | Used in email links |
| `DATABASE_NAME` | No | Defaults to `db.sqlite3` |
| `EMAIL_HOST` | Yes (prod) | `smtp.resend.com` |
| `EMAIL_PORT` | No | Default `587` |
| `EMAIL_USE_TLS` | No | Default `True` |
| `EMAIL_USE_SSL` | No | Default `False` |
| `EMAIL_HOST_USER` | Yes (prod) | `resend` |
| `EMAIL_HOST_PASSWORD` | Yes (prod) | Resend API key — set as host env var, not in `.env` |
| `DEFAULT_FROM_EMAIL` | No | Default `data@steblik.com` |

---

## Planned / Future Work

- [ ] **Services page** — reframe Experience page; add consulting/courses/freelance offerings
- [ ] **Homepage** — reposition copy toward data engineering lab
- [ ] **Stripe integration** — paid membership tiers (individual learner vs corporate)
- [ ] **Courses app** — structured content delivery for paid members
- [ ] **Corporate landing** — dedicated page for freelance/consulting enquiries
- [ ] **About page** — decide visibility for logged-in users
- [ ] **RSS feed** — enable in `SITE_META`
