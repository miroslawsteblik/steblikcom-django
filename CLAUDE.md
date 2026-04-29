# CLAUDE.md

Repo-level instructions for Claude Code. Read this file in full at the start
of every session. Anything in this file overrides general defaults.

A personal, gitignored counterpart lives at `CLAUDE.local.md` — read it too
when present, but do not assume collaborators have the same content.

---

## 1. Project

This is a **monorepo** containing:

- `apps/web/` — the public-facing site at **steblik.com**, a Django web
  application with member accounts, transactional email, and (planned)
  premium content + newsletter.
- `apps/pipelines/` — data engineering pipelines, primarily dbt + Python,
  for investment and financial data.
- `infra/` — infrastructure-as-code, Docker Compose definitions, deployment
  scripts, server provisioning notes.

The site is operated by Miroslaw Steblik, a UK sole trader, acting as data
controller under UK/EU GDPR. **Public legal commitments are listed in
`docs/PRIVACY_INVARIANTS.md` and must be honoured by every change made to
this repo.** If a proposed change conflicts with an invariant, stop and
flag it before writing code.


---

## 2. Stack — non-negotiable

These are deliberate choices. Do not substitute. If a request implies a
different tool, propose an in-stack alternative and ask before deviating.

### Python
- **Package manager:** `uv` only. Never `pip`, `poetry`, `pipenv`, or
  `conda`. Lockfile is `uv.lock`.
- **Data manipulation:** **Polars**, not pandas. If a library hard-requires
  pandas at the boundary, isolate the conversion and convert back to
  Polars immediately.
- **Filesystem:** **`pathlib`**, not `os.path`. No string concatenation
  for paths.
- **HTTP client:** `httpx` (sync or async as appropriate), not `requests`.
- **Settings/env:** `django-environ` reading from `.env`. Never hardcode
  secrets, URLs, or credentials. Never read `os.environ` directly in
  application code outside `settings.py`.
- **Type hints:** required on all new functions and methods. Use modern
  syntax (`list[str]`, `X | None`, not `List[str]`, `Optional[X]`).
- **Formatting/linting:** `ruff format` and `ruff check`. No `black`,
  `isort`, `flake8`, or `pylint`.

### Web (apps/web)
- **Framework:** Django (LTS).
- **Database:** Postgres. No SQLite outside tests.
- **Frontend:** HTMX + Tailwind. **No React, Vue, Svelte, or any SPA
  framework.** No client-side build tooling beyond Tailwind.
- **Templates:** Django templates. Inheritance via `base.html`. Keep
  business logic out of templates.
- **Forms:** Django forms or `django-htmx`-friendly views. No JS-only forms.
- **Email:** Resend, via the project's email backend wrapper. Never call
  Resend's API directly from a view; always go through the wrapper so
  logging and retention rules are applied uniformly.

### Data pipelines (apps/pipelines)
- **Transformation:** dbt (project lives in `apps/pipelines/dbt/`).
- **Python orchestration:** plain Python scripts + cron / systemd timers
  on the home lab unless a real scheduler is justified.
- **Dataframes:** Polars. Lazy frames (`pl.scan_*`) by default for any
  pipeline reading a file; collect only when materialising output.
- **File formats:** Parquet for intermediate and final tabular data;
  CSV only at external boundaries.

### Shell
- Scripts target **bash on Ubuntu Server** (the home lab) and **CMD/
  PowerShell** on Windows where relevant. Mark which shell a script
  expects in its top comment. Prefer Python over shell once a script
  exceeds ~30 lines.

### Infrastructure
- **Containers:** Docker + Docker Compose. No Kubernetes for this project.
- **OS target:** Ubuntu Server LTS.
- **Deployment:** [TODO: confirm — Hetzner VPS + Docker Compose]. Document
  changes to deployment in `infra/README.md`.

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

### Branching & commits
- Trunk: `main`. Feature branches: `feat/<short-name>`,
  `fix/<short-name>`, `chore/<short-name>`.
- Commit style: Conventional Commits (`feat:`, `fix:`, `docs:`,
  `chore:`, `refactor:`, `test:`).
- Never commit directly to `main` for code changes. Documentation typo
  fixes are acceptable.

### Tests
- Tests are **required for new features and bug fixes**. Retrofitting
  tests onto untested legacy code is not required unless the area is
  being modified.
- Web: `pytest` + `pytest-django`. Tests live next to the app they cover
  (`apps/web/<app>/tests/`).
- Pipelines: dbt tests (schema + data tests) for models; pytest for
  Python helpers.
- Always run the relevant test subset before declaring a change done.
  Run the full suite if the change touches shared code.

### Database migrations
- Every model change ships with a Django migration in the same commit.
- Never edit a migration that has been applied to production.
- For destructive migrations (drops, renames), write a reversible plan
  in the PR description.

## 4. Privacy & legal guardrails — hard rules

These mirror the published Privacy Policy, Terms of Service, and Legal
page. Violating them in code violates a public commitment. Treat as
non-negotiable.

1. **No third-party tracking, analytics, or advertising scripts** in any
   rendered template. This includes Google Analytics, GTM, Meta Pixel,
   Hotjar, Plausible Cloud, Mixpanel, Segment, and any social-media
   embed that loads external JavaScript.
2. **No external font CDNs.** Fonts are self-hosted. Never add
   `fonts.googleapis.com`, `fonts.gstatic.com`, or any other font
   host to a template, stylesheet, or `Content-Security-Policy`.
3. **No third-party JS in `<script>` tags** without prior approval.
   First-party JS only. HTMX is loaded as a self-hosted asset.
4. **Cookies are limited to `sessionid` and `csrftoken`.** Adding a new
   cookie requires (a) updating the Privacy Policy *first*, (b) a clear
   justification of strict necessity or a proper consent mechanism, and
   (c) approval before merge.
5. **Server logs retention: 14 days.** Any log-handling change must
   preserve this. If a provider's default retention exceeds 14 days,
   configure rotation/deletion explicitly.
6. **Account data deletion: within 30 days of request, including
   propagation to backups within the documented backup window.** Any
   change to account-deletion logic must keep this guarantee.
7. **Email is sent only via the Resend wrapper.** Do not introduce a
   second email provider without updating the Privacy Policy first.
8. **Marketing email requires explicit opt-in.** The opt-in checkbox
   must not be pre-ticked, must be separate from account-creation
   consent, and every marketing email must contain a one-click
   unsubscribe link plus the operator's postal address (PECR).
9. **Personal data minimisation.** The site collects email + hashed
   password + registration date + last login. Adding a new personal
   data field (name, country, IP-derived location, etc.) requires
   updating the Privacy Policy first and justifying the lawful basis.
10. **No automated decision-making or profiling** without prior approval
    and a Privacy Policy update. This includes behavioural personalisation
    of newsletter content.
11. **No transfers to new sub-processors** without updating the Privacy
    Policy's sub-processor list and adding the relevant SCC/IDTA note
    if the processor is outside the UK/EEA.
12. **Passwords:** Django's default PBKDF2 hasher minimum. Never log,
    print, or store plaintext passwords. Never include a password in
    an email body, even on reset.
13. **No "right to be forgotten" workarounds.** Soft-delete is fine for
    referential integrity, but PII must be nulled or pseudonymised at
    the point of deletion request, not merely flagged inactive.

If you are unsure whether a change touches one of these rules, **ask
before writing code**. The list in `docs/PRIVACY_INVARIANTS.md` is the
checkable form of the same commitments.

## 5. Security guardrails

- **Secrets:** never in the repo, never in templates, never in logs.
  `.env` is gitignored; `.env.example` lists keys with placeholder values.
- **CSRF:** every state-changing view requires CSRF protection. No
  exemption without written justification in the PR.
- **`DEBUG = True` is forbidden in any committed settings file other
  than `settings/dev.py`.** Production settings inherit from base and
  set `DEBUG = False` explicitly.
- **`ALLOWED_HOSTS`** must be set from environment, never hardcoded to
  `["*"]`.
- **TLS** is mandatory in production. `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` all True in production
  settings.
- **Dependency updates:** `uv lock --upgrade` only on a dedicated
  branch with the test suite green.

## 6. Working style for Claude

- **Read before writing.** When asked to modify a file, read its current
  contents first; do not regenerate from memory.
- **Plan before coding** for any change touching more than one file.
  Surface the plan, get acknowledgement, then implement.
- **Small, reviewable diffs.** Prefer multiple focused commits over one
  sprawling change.
- **Do not silently expand scope.** If a fix reveals a related bug,
  flag it as a follow-up rather than fixing in the same PR.
- **No "helpful" extras.** Don't add analytics, error-reporting SaaS,
  feature flag services, or any external dependency without explicit
  request.
- **When uncertain about a privacy or legal implication, stop and
  ask.** This is the single most important rule in this file.

## 7. Useful commands

```bash
# Python deps
uv sync                          # install
uv add <package>                 # add a dep
uv lock --upgrade                # upgrade locks (separate branch)

# Django (apps/web)
uv run python apps/web/manage.py runserver
uv run python apps/web/manage.py migrate
uv run python apps/web/manage.py makemigrations
uv run python apps/web/manage.py createsuperuser

# Tests
uv run pytest                    # full suite
uv run pytest apps/web/accounts  # one app
uv run pytest -k <pattern>

# Lint / format
uv run ruff format .
uv run ruff check . --fix

# dbt (apps/pipelines/dbt)
cd apps/pipelines/dbt && uv run dbt build

# Privacy invariant check (see docs/PRIVACY_INVARIANTS.md)
./scripts/check_privacy_invariants.sh
```

## 8. References

- `docs/PRIVACY_INVARIANTS.md` — testable list of privacy commitments.
- `docs/SECURITY.md` — security policy and disclosure process.
- `apps/web/templates/legal/` — Privacy Policy, Terms of Service, Legal.
- `infra/README.md` — deployment notes.
- `CLAUDE.local.md` — personal notes (gitignored).

### Marking existing users as verified (shell)
```python
from allauth.account.models import EmailAddress
EmailAddress.objects.filter(verified=False).update(verified=True, primary=True)
```

---

## Blog System

Posts are Markdown files in `content/posts/`. Each post is either:
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



## Site Domain / Allauth

`SITE_DOMAIN` in `.env` controls the domain used in email verification links.
- Dev: `localhost:8000`
- Prod: `steblik.com`

The `PagesConfig.ready()` hook keeps the `django.contrib.sites` Site model in sync
on every `migrate` run.

---


