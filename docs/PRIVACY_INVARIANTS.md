# Privacy invariants

This document is the **checkable form** of the public commitments in the
Privacy Policy, Terms of Service, and Legal page. Each invariant is
phrased so it can be verified by inspection or by an automated check.

If any of these invariants becomes false, the public policy is being
violated. Either the code must change, or the policy must change *first*
and then the code may follow.

## Site behaviour

| # | Invariant | How to check |
|---|-----------|--------------|
| P1 | No third-party tracking/analytics scripts in any rendered page | Grep templates for `googletagmanager`, `google-analytics`, `gtag(`, `fbq(`, `hotjar`, `mixpanel`, `plausible.io`, `segment.com`, `clarity.ms` |
| P2 | No external font CDN references | Grep templates and CSS for `fonts.googleapis.com`, `fonts.gstatic.com`, `use.typekit.net`, `fonts.bunny.net` |
| P3 | No third-party JavaScript loaded from a CDN | Grep templates for `<script src="https://` and confirm each match is self-hosted or explicitly approved |
| P4 | Only `sessionid` and `csrftoken` cookies are set on a vanilla request | Hit the home page in a clean browser; inspect `Set-Cookie` headers |
| P5 | `DEBUG = False` in production settings | Inspect `apps/web/config/settings/prod.py` |
| P6 | `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` are True in production | Same file |
| P7 | `ALLOWED_HOSTS` is read from environment, not hardcoded `["*"]` | Same file |

## Data handling

| # | Invariant | How to check |
|---|-----------|--------------|
| D1 | Personal data fields on `User` are limited to: email, hashed password, date_joined, last_login | Inspect the user model; any extra PII field requires a Privacy Policy update |
| D2 | Passwords are hashed with PBKDF2 or stronger | `PASSWORD_HASHERS` in settings |
| D3 | Plaintext passwords are never logged | Grep for `password` in logging calls; review login/signup views |
| D4 | Account deletion removes PII from the live database within 30 days | Manual test of the deletion flow |
| D5 | Backup retention does not exceed 30 days | Provider configuration; documented in `infra/README.md` |
| D6 | Server logs are deleted after 14 days | Logrotate / provider configuration |
| D7 | All email is sent via the Resend wrapper (`apps/web/email/__init__.py`) | Grep for direct Resend SDK imports outside the wrapper |
| D8 | Marketing emails require an explicit, separate opt-in | Inspect signup form and any newsletter signup form |
| D9 | Every marketing email includes an unsubscribe link and postal address | Inspect email templates in `apps/web/templates/email/` |

## Sub-processors

| # | Invariant | How to check |
|---|-----------|--------------|
| S1 | The set of third parties processing personal data matches the Privacy Policy's sub-processor list exactly | Manual review on every dependency or vendor change |
| S2 | Each non-UK/EEA sub-processor has SCCs / IDTA in place | Vendor documentation; record in `docs/SUBPROCESSORS.md` |

## When an invariant must change

1. Update the relevant public policy page (`apps/web/templates/legal/`).
2. Update this file.
3. Update the automated check in `scripts/check_privacy_invariants.sh`
   if applicable.
4. Notify users by email if the change is material (the Privacy Policy
   commits to this).
5. Bump the "Last updated" date on the policy page.

The order matters: **policy first, then code**.
