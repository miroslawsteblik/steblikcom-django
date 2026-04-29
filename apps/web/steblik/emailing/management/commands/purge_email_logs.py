"""
Purge email delivery logs older than the configured retention window.

Run from cron / systemd timer:
    uv run python apps/web/manage.py purge_email_logs

Default retention is 30 days. Override with EMAIL_LOG_RETENTION_DAYS
in settings, or pass --days on the command line.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from steblik.emailing.models import EmailLog


class Command(BaseCommand):
    help = "Delete email logs older than EMAIL_LOG_RETENTION_DAYS (default 30)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=getattr(settings, "EMAIL_LOG_RETENTION_DAYS", 30),
            help="Retention window in days (default: 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without deleting.",
        )

    def handle(self, *args, days: int, dry_run: bool, **options):
        cutoff = timezone.now() - timedelta(days=days)
        qs = EmailLog.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        if dry_run:
            self.stdout.write(
                f"[dry-run] Would delete {count} email logs older than {cutoff.isoformat()}."
            )
            return
        deleted, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} email logs older than {cutoff.isoformat()}.")
        )
