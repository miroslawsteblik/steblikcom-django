import uuid
from collections.abc import Iterator
from itertools import islice

import resend
from allauth.account.models import EmailAddress
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Announcement, AnnouncementRecipient

_BATCH_SIZE = 100  # Resend batch limit


def _chunks(lst: list, n: int) -> Iterator[list]:
    it = iter(lst)
    while chunk := list(islice(it, n)):
        yield chunk


def _render_html(announcement: Announcement) -> str:
    """Render the email HTML body. Uses new_post template if post_slug is set."""
    if announcement.body_html:
        return announcement.body_html

    if announcement.post_slug:
        from apps.web.steblik.blog.services import get_post

        post = get_post(announcement.post_slug)
        if post is None:
            raise ValueError(f"Post '{announcement.post_slug}' not found.")
        site_url = f"https://{settings.SITE_DOMAIN}"
        return render_to_string(
            "emails/new_post.html",
            {
                "subject": announcement.subject,
                "post": post,
                "post_url": f"{site_url}/blog/{post.slug}/",
                "site_url": site_url,
                "profile_url": f"{site_url}/me/",
            },
        )

    return f"<p>{announcement.body_text}</p>"


def _build_params(announcement: Announcement, html: str, addr: str) -> resend.Emails.SendParams:
    return {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [addr],
        "subject": announcement.subject,
        "html": html,
        "text": announcement.body_text,
        "tags": [{"name": "announcement_id", "value": str(announcement.pk)}],
    }


def send_announcement(announcement: Announcement, sent_by=None) -> tuple[int, int]:
    """Send an announcement to all active verified members via Resend.

    In DEBUG mode (or when RESEND_API_KEY is not set) the send is simulated
    and logged with synthetic IDs so the full admin flow can be tested locally.

    Returns:
        Tuple of (sent_count, failed_count).

    Raises:
        ValueError: If the announcement has already been sent, or post_slug is invalid.
    """
    if announcement.is_sent:
        raise ValueError("This announcement has already been sent.")

    recipient_emails = list(
        EmailAddress.objects.filter(
            verified=True,
            primary=True,
            user__is_active=True,
        ).values_list("email", flat=True)
    )

    html = _render_html(announcement)
    log_entries: list[AnnouncementRecipient] = []
    sent = 0
    failed = 0

    if settings.DEBUG or not settings.RESEND_API_KEY:
        # Simulate sends locally — prints subject + recipient count, no HTTP call.
        print(
            f"[send_announcement DEBUG] subject='{announcement.subject}'"
            f" recipients={len(recipient_emails)}"
        )
        for addr in recipient_emails:
            print(f"  → {addr}")
            log_entries.append(
                AnnouncementRecipient(
                    announcement=announcement,
                    email=addr,
                    status=AnnouncementRecipient.Status.SENT,
                    resend_email_id=f"debug-{uuid.uuid4().hex[:12]}",
                )
            )
            sent += 1
    else:
        resend.api_key = settings.RESEND_API_KEY

        for chunk in _chunks(recipient_emails, _BATCH_SIZE):
            params = [_build_params(announcement, html, addr) for addr in chunk]
            try:
                result = resend.Batch.send(params)
                for addr, item in zip(chunk, result["data"], strict=False):
                    log_entries.append(
                        AnnouncementRecipient(
                            announcement=announcement,
                            email=addr,
                            status=AnnouncementRecipient.Status.SENT,
                            resend_email_id=item.get("id", ""),
                        )
                    )
                    sent += 1
            except Exception as e:
                for addr in chunk:
                    log_entries.append(
                        AnnouncementRecipient(
                            announcement=announcement,
                            email=addr,
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
