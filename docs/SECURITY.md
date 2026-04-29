# Security policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in steblik.com or
any code in this repository, please email **security@steblik.com** with:

- A description of the issue and its potential impact.
- Steps to reproduce, or a proof-of-concept where possible.
- Any relevant logs, screenshots, or output.

Please do **not** open a public GitHub issue for security-related
reports. Reports are acknowledged within 5 working days. Responsible
disclosure is welcomed and credit will be given (with permission) once
the issue is resolved.

## Scope

In scope:
- The web application at https://steblik.com
- The source code in this repository

Out of scope:
- Third-party services (Resend, the hosting provider, etc.) — please
  report directly to the vendor.
- Social engineering of the operator or users.
- Physical security.
- Denial-of-service testing without prior written agreement.

## Security commitments

Mirroring the Privacy Policy:

- All connections use TLS.
- Passwords are hashed with PBKDF2 (Django default) and salted.
- The database is encrypted at rest by the hosting provider.
- Production access is restricted to the operator and protected by
  multi-factor authentication.
- Personal data breaches likely to result in risk to user rights are
  reported to the ICO within 72 hours and to affected users where the
  risk is high.

## Supported versions

Only the version currently deployed at https://steblik.com is supported.
There are no LTS branches.
