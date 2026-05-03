"""
Senders — the only public API for sending email from application code.

Direct calls to `django.core.mail.send_mail` are discouraged because they
bypass type-tagging and PECR-mandated unsubscribe injection for marketing
mail. If you need a new email type, add a helper here.

Each helper:
  - Renders both plain-text and HTML templates (text first; never
    HTML-only — some clients still need text).
  - Tags the email with X-Email-Type so the backend records the type
    in EmailLog.
  - For marketing email, adds List-Unsubscribe headers (RFC 8058) and
    expects the caller to provide a working unsubscribe URL.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def _send(
    *,
    to: str,
    subject: str,
    template_base: str,
    context: dict,
    email_type: str,
    extra_headers: dict[str, str] | None = None,
) -> None:
    text_body = render_to_string(f"emails/{template_base}.txt", context)
    html_body = render_to_string(f"emails/{template_base}.html", context)

    headers: dict[str, str] = {"X-Email-Type": email_type}
    if extra_headers:
        headers.update(extra_headers)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        headers=headers,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


# ---- Transactional ---------------------------------------------------------


def send_verification(user: object, *, verification_url: str) -> None:
    """Email-address verification link sent at signup or re-send."""
    _send(
        to=user.email,  # type: ignore[union-attr]
        subject="Verify your email — steblik.com",
        template_base="email_verification",
        context={"user": user, "verification_url": verification_url},
        email_type="transactional.verification",
    )


def send_welcome(user: object) -> None:
    """Welcome email sent once after the user's address is verified."""
    _send(
        to=user.email,  # type: ignore[union-attr]
        subject="Welcome to steblik.com",
        template_base="welcome",
        context={"user": user},
        email_type="transactional.welcome",
    )


def send_password_reset(user: object, *, reset_url: str) -> None:
    """Password reset link."""
    _send(
        to=user.email,  # type: ignore[union-attr]
        subject="Reset your password — steblik.com",
        template_base="password_reset",
        context={"user": user, "reset_url": reset_url},
        email_type="transactional.password_reset",
    )


def send_account_deletion_confirmation(user_email: str) -> None:
    """
    Confirmation that the account and PII have been removed.

    Takes the email string rather than a user instance because the user
    record has already been deleted by the time this is called.
    """
    _send(
        to=user_email,
        subject="Your account has been deleted — steblik.com",
        template_base="account_deleted",
        context={"email": user_email},
        email_type="transactional.account_deleted",
    )


# ---- Marketing -------------------------------------------------------------


def send_newsletter(
    *,
    subscriber: object,
    subject: str,
    body_markdown: str,
    unsubscribe_url: str,
) -> None:
    """
    Send a single marketing email via the Django email backend.

    PECR requires:
      - Explicit prior opt-in (caller must verify subscriber.marketing_consent).
      - Sender identity and postal address in the message.
      - A working unsubscribe mechanism in every message.

    RFC 8058 List-Unsubscribe headers are also set so mail clients can
    offer one-click unsubscribe natively.

    For bulk sends to many recipients use send_announcement() in
    accounts.services, which uses the Resend batch API instead.
    """
    headers = {
        "List-Unsubscribe": f"<{unsubscribe_url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }
    _send(
        to=subscriber.email,  # type: ignore[union-attr]
        subject=subject,
        template_base="newsletter",
        context={
            "subscriber": subscriber,
            "subject": subject,
            "body_markdown": body_markdown,
            "unsubscribe_url": unsubscribe_url,
            "operator_name": getattr(settings, "OPERATOR_NAME", "Miroslaw Steblik"),
            "operator_address": getattr(settings, "OPERATOR_POSTAL_ADDRESS", ""),
        },
        email_type="marketing.newsletter",
        extra_headers=headers,
    )
