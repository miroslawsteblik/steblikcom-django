#!/usr/bin/env bash
# Checks the privacy invariants documented in docs/PRIVACY_INVARIANTS.md.
# Exits non-zero if any forbidden pattern is found in templates or assets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$ROOT/apps/web/templates"
STATIC="$ROOT/apps/web/static"

# Patterns that should never appear in rendered HTML, CSS, or JS.
FORBIDDEN=(
  "googletagmanager"
  "google-analytics"
  "gtag("
  "fbq("
  "hotjar"
  "mixpanel"
  "segment.com"
  "clarity.ms"
  "fonts.googleapis.com"
  "fonts.gstatic.com"
  "use.typekit.net"
  "fonts.bunny.net"
)

fail=0
for pattern in "${FORBIDDEN[@]}"; do
  # rg returns 0 if matches found, 1 if not. We want to fail on matches.
  if rg --no-messages -n -F "$pattern" "$TEMPLATES" "$STATIC" 2>/dev/null; then
    echo "FORBIDDEN: '$pattern' found in templates or static assets." >&2
    fail=1
  fi
done

# Direct Resend SDK use outside the email wrapper.
if rg --no-messages -n "from resend" "$ROOT/apps/web" \
    | rg -v "apps/web/email/" >/dev/null 2>&1; then
  echo "FORBIDDEN: direct 'from resend' import outside apps/web/email/." >&2
  fail=1
fi

# DEBUG = True in non-dev settings.
if rg --no-messages -n "^DEBUG\s*=\s*True" "$ROOT/apps/web/config/settings" \
    | rg -v "settings/dev.py" >/dev/null 2>&1; then
  echo "FORBIDDEN: DEBUG = True outside settings/dev.py." >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Privacy invariant check failed." >&2
  exit 1
fi

echo "Privacy invariants OK."
