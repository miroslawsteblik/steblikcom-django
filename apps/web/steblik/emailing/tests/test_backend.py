"""Tests for the Resend email backend."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.mail import EmailMultiAlternatives, send_mail
from steblik.emailing.models import EmailLog


@pytest.fixture(autouse=True)
def _backend_settings(settings) -> None:
    settings.EMAIL_BACKEND = "steblik.emailing.backend.ResendEmailBackend"
    settings.RESEND_API_KEY = "test_key"
    settings.DEFAULT_FROM_EMAIL = "noreply@steblik.com"


@pytest.mark.django_db
class TestResendBackend:
    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_send_logs_success(self, mock_send):
        mock_send.return_value = {"id": "msg_abc123"}

        sent = send_mail(
            subject="Hello",
            message="text body",
            from_email="noreply@steblik.com",
            recipient_list=["user@example.com"],
        )

        assert sent == 1
        log = EmailLog.objects.get()
        assert log.recipient == "user@example.com"
        assert log.status == EmailLog.Status.SENT
        assert log.provider_message_id == "msg_abc123"
        assert log.email_type == "unspecified"

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_send_logs_failure(self, mock_send):
        mock_send.side_effect = RuntimeError("upstream down")

        with pytest.raises(RuntimeError):
            send_mail(
                subject="Hello",
                message="text body",
                from_email="noreply@steblik.com",
                recipient_list=["user@example.com"],
                fail_silently=False,
            )

        log = EmailLog.objects.get()
        assert log.status == EmailLog.Status.FAILED
        assert "upstream down" in log.error
        assert log.provider_message_id == ""

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_send_extracts_html_alternative(self, mock_send):
        mock_send.return_value = {"id": "msg_xyz"}

        msg = EmailMultiAlternatives(
            subject="HTML test",
            body="text body",
            from_email="noreply@steblik.com",
            to=["user@example.com"],
            headers={"X-Email-Type": "transactional.test"},
        )
        msg.attach_alternative("<p>html body</p>", "text/html")
        msg.send()

        params = mock_send.call_args[0][0]
        assert params["text"] == "text body"
        assert params["html"] == "<p>html body</p>"
        # X-Email-Type is consumed, not forwarded.
        assert "X-Email-Type" not in params.get("headers", {})

        log = EmailLog.objects.get()
        assert log.email_type == "transactional.test"

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_forwards_other_extra_headers(self, mock_send):
        mock_send.return_value = {"id": "msg_xyz"}

        msg = EmailMultiAlternatives(
            subject="Newsletter",
            body="hi",
            from_email="noreply@steblik.com",
            to=["user@example.com"],
            headers={
                "X-Email-Type": "marketing.newsletter",
                "List-Unsubscribe": "<https://steblik.com/u/tok>",
            },
        )
        msg.send()

        params = mock_send.call_args[0][0]
        assert params["headers"] == {"List-Unsubscribe": "<https://steblik.com/u/tok>"}

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_does_not_persist_body(self, mock_send):
        """Privacy invariant: message body must not appear in EmailLog."""
        mock_send.return_value = {"id": "msg_id"}

        secret = "RESET_TOKEN_VERY_SECRET_abc123"
        send_mail(
            subject="Reset your password",
            message=f"Click here: {secret}",
            from_email="noreply@steblik.com",
            recipient_list=["user@example.com"],
        )

        log = EmailLog.objects.get()
        # Structural guarantee — the model does not have a body field.
        assert not hasattr(log, "body")
        # Defensive — secret must not leak via subject either.
        assert secret not in log.subject
