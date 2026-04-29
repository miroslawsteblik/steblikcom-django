"""
Email delivery log.

Stores ONLY operational metadata: recipient, subject, type tag, status,
provider message id, timestamp. NEVER stores the message body.
Retention is enforced by the `purge_email_logs` management command.

This file deliberately has no `body` field. If you find yourself wanting
to add one, update `docs/PRIVACY_INVARIANTS.md` and the Privacy Policy
first.
"""

from __future__ import annotations

from django.db import models


class EmailLog(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    recipient = models.EmailField(max_length=254)
    subject = models.CharField(max_length=200, blank=True)
    email_type = models.CharField(
        max_length=64,
        default="unspecified",
        db_index=True,
        help_text="Dotted tag, e.g. 'transactional.verification', 'marketing.newsletter'.",
    )
    status = models.CharField(max_length=16, choices=Status.choices, db_index=True)
    provider_message_id = models.CharField(max_length=120, blank=True)
    error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at", "status"])]

    def __str__(self) -> str:
        return f"{self.email_type} -> {self.recipient} [{self.status}]"
