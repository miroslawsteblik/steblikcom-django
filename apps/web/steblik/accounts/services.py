from __future__ import annotations

import uuid
from collections.abc import Iterator
from itertools import islice

import resend
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Announcement, AnnouncementRecipient

User = get_user_model()

_BATCH_SIZE = 100  # Resend batch limit


def _chunks(lst: list, n: int) -> Iterator[list]:
    it = iter(lst)
    while chunk := list(islice(it, n)):
        yield chunk


def _site_url() -> str:
    return f"https://{settings.SITE_DOMAIN}"


def _unsubscribe_url(user: object) -> str:
    return f"{_site_url()}/me/unsubscribe/{user.unsubscribe_token}/"  # type: ignore[union-attr]


def _display_name(user: object) -> str:
    """Best available name for greeting: first_name, else email prefix."""
    first = getattr(user, "first_name", "").strip()
    if first:
        return first
    email: str = getattr(user, "email", "")
    return email.split("@")[0] if email else "there"


def _render_html(announcement: Announcement, user: object) -> str:
    """Render the per-recipient HTML body."""
    site_url = _site_url()
    ctx: dict = {
        "announcement": announcement,
        "user": user,
        "display_name": _display_name(user),
        "unsubscribe_url": _unsubscribe_url(user),
        "site_url": site_url,
        "profile_url": f"{site_url}/me/",
    }

    if announcement.post_slug:
        from steblik.blog.services import get_post

        post = get_post(announcement.post_slug)
        if post is None:
            raise ValueError(f"Post '{announcement.post_slug}' not found.")
        ctx["post"] = post
        ctx["post_url"] = f"{site_url}/blog/{post.slug}/"
        return render_to_string("emails/new_post.html", ctx)

    if announcement.body_html:
        # Raw HTML override: still inject unsubscribe footer via wrapper template.
        ctx["raw_html"] = announcement.body_html
        return render_to_string("emails/announcement.html", ctx)

    ctx["body_text"] = announcement.body_text
    return render_to_string("emails/announcement.html", ctx)


def _build_params(
    announcement: Announcement,
    html: str,
    user: object,
) -> resend.Emails.SendParams:
    return {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [user.email],  # type: ignore[union-attr]
        "subject": announcement.subject,
        "html": html,
        "text": announcement.body_text,
        "headers": {
            "List-Unsubscribe": f"<{_unsubscribe_url(user)}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
        "tags": [{"name": "announcement_id", "value": str(announcement.pk)}],
    }


def send_announcement(announcement: Announcement, sent_by=None) -> tuple[int, int]:
    """Send an announcement to all opted-in verified members via Resend.

    Only users with marketing_consent=True are included. Each email contains
    a personalised greeting and a per-user one-click unsubscribe link.

    In DEBUG mode (or when RESEND_API_KEY is not set) sends are simulated.

    Returns:
        Tuple of (sent_count, failed_count).

    Raises:
        ValueError: If the announcement has already been sent, or post_slug is invalid.
    """
    if announcement.is_sent:
        raise ValueError("This announcement has already been sent.")

    # Only users who explicitly opted in.
    opted_in_ids = set(
        EmailAddress.objects.filter(
            verified=True,
            primary=True,
            user__is_active=True,
            user__marketing_consent=True,
        ).values_list("user_id", flat=True)
    )
    recipients: list = list(User.objects.filter(pk__in=opted_in_ids))

    log_entries: list[AnnouncementRecipient] = []
    sent = 0
    failed = 0

    if settings.DEBUG or not settings.RESEND_API_KEY:
        print(
            f"[send_announcement DEBUG] subject='{announcement.subject}'"
            f" recipients={len(recipients)}"
        )
        for user in recipients:
            print(f"  → {user.email} ({_display_name(user)})")
            log_entries.append(
                AnnouncementRecipient(
                    announcement=announcement,
                    email=user.email,
                    status=AnnouncementRecipient.Status.SENT,
                    resend_email_id=f"debug-{uuid.uuid4().hex[:12]}",
                )
            )
            sent += 1
    else:
        resend.api_key = settings.RESEND_API_KEY

        for chunk in _chunks(recipients, _BATCH_SIZE):
            params = [_build_params(announcement, _render_html(announcement, u), u) for u in chunk]
            try:
                result = resend.Batch.send(params)
                for user, item in zip(chunk, result["data"], strict=False):
                    log_entries.append(
                        AnnouncementRecipient(
                            announcement=announcement,
                            email=user.email,
                            status=AnnouncementRecipient.Status.SENT,
                            resend_email_id=item.get("id", ""),
                        )
                    )
                    sent += 1
            except Exception as e:
                for user in chunk:
                    log_entries.append(
                        AnnouncementRecipient(
                            announcement=announcement,
                            email=user.email,
                            status=AnnouncementRecipient.Status.FAILED,
                            error=str(e),
                        )
                    )
                    failed += 1

    AnnouncementRecipient.objects.bulk_create(log_entries)
    announcement.sent_at = timezone.now()
    announcement.sent_by = sent_by
    announcement.total_sent = sent
    announcement.total_failed = failed
    announcement.save(update_fields=["sent_at", "sent_by", "total_sent", "total_failed"])

    return sent, failed
