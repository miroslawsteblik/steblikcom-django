"""
Custom Django email backend that delivers via Resend.

This module is the SINGLE point of egress for all outgoing email.
The privacy policy commits to this — see docs/PRIVACY_INVARIANTS.md (D7).
The privacy invariant check greps for direct `from resend` imports
outside this app and fails the build if any are found.

Bodies are NEVER persisted. Only operational metadata is logged.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.core.mail.message import EmailMessage

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Send EmailMessage objects via the Resend HTTP API."""

    def __init__(self, fail_silently: bool = False, **kwargs) -> None:
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._api_key: str | None = getattr(settings, "RESEND_API_KEY", None)
        if not self._api_key and not fail_silently:
            raise RuntimeError("RESEND_API_KEY is not configured.")

    def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        if not email_messages:
            return 0
        # Set per-call to avoid leaking state across threads/processes.
        resend.api_key = self._api_key
        sent = 0
        for message in email_messages:
            if self._send_one(message):
                sent += 1
        return sent

    def _send_one(self, message: EmailMessage) -> bool:
        # Local import to avoid app-loading order issues.
        from steblik.emailing.models import EmailLog

        recipients = list(message.to or [])
        cc = list(message.cc or [])
        bcc = list(message.bcc or [])
        if not (recipients or cc or bcc):
            return False

        text_body, html_body = _extract_bodies(message)

        # Type tag is read but not forwarded to Resend.
        headers_in = dict(message.extra_headers or {})
        email_type = headers_in.pop("X-Email-Type", "unspecified")

        params: dict = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": recipients,
            "subject": message.subject,
        }
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        if message.reply_to:
            params["reply_to"] = list(message.reply_to)
        if text_body:
            params["text"] = text_body
        if html_body:
            params["html"] = html_body
        if headers_in:
            params["headers"] = headers_in

        try:
            response = resend.Emails.send(params)
        except Exception as exc:  # noqa: BLE001 — SDK raises various types
            EmailLog.objects.create(
                recipient=_first(recipients) or _first(cc) or _first(bcc) or "",
                subject=(message.subject or "")[:200],
                email_type=email_type,
                status=EmailLog.Status.FAILED,
                provider_message_id="",
                error=str(exc)[:500],
            )
            logger.warning("Resend delivery failed: %s", exc)
            if not self.fail_silently:
                raise
            return False

        provider_id = ""
        if isinstance(response, dict):
            provider_id = str(response.get("id", ""))[:120]

        EmailLog.objects.create(
            recipient=_first(recipients) or _first(cc) or _first(bcc) or "",
            subject=(message.subject or "")[:200],
            email_type=email_type,
            status=EmailLog.Status.SENT,
            provider_message_id=provider_id,
            error="",
        )
        return True


def _extract_bodies(message: EmailMessage) -> tuple[str | None, str | None]:
    """Return (text_body, html_body) from EmailMessage or EmailMultiAlternatives."""
    text: str | None = None
    html: str | None = None

    if getattr(message, "content_subtype", "plain") == "html":
        html = message.body or None
    else:
        text = message.body or None

    for content, mimetype in getattr(message, "alternatives", None) or []:
        if mimetype == "text/html":
            html = content
        elif mimetype == "text/plain":
            text = content

    return text, html


def _first(seq: list) -> object | None:
    return seq[0] if seq else None
