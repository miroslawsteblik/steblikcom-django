from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Announcement
from apps.accounts.services import send_announcement


class Command(BaseCommand):
    help = "Send a saved Announcement to all active verified members."

    def add_arguments(self, parser):
        parser.add_argument("announcement_id", type=int, help="PK of the Announcement to send")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print recipients without sending",
        )

    def handle(self, *args, **options):
        try:
            announcement = Announcement.objects.get(pk=options["announcement_id"])
        except Announcement.DoesNotExist:
            raise CommandError(f"Announcement {options['announcement_id']} not found.")

        if announcement.is_sent:
            raise CommandError("This announcement has already been sent.")

        if options["dry_run"]:
            from allauth.account.models import EmailAddress
            recipients = list(
                EmailAddress.objects.filter(
                    verified=True, primary=True, user__is_active=True
                ).values_list("email", flat=True)
            )
            self.stdout.write(f"Subject: {announcement.subject}")
            self.stdout.write(f"Recipients ({len(recipients)}):")
            for addr in recipients:
                self.stdout.write(f"  {addr}")
            self.stdout.write(self.style.SUCCESS("Dry run — no emails sent."))
            return

        sent, failed = send_announcement(announcement)
        self.stdout.write(
            self.style.SUCCESS(f"Done — sent: {sent}, failed: {failed}")
        )
