"""Tests for the email senders (high-level helpers)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from steblik.emailing import senders

User = get_user_model()


@pytest.fixture(autouse=True)
def _backend_settings(settings) -> None:
    settings.EMAIL_BACKEND = "steblik.emailing.backend.ResendEmailBackend"
    settings.RESEND_API_KEY = "test_key"
    settings.DEFAULT_FROM_EMAIL = "noreply@steblik.com"


@pytest.mark.django_db
class TestSenders:
    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_verification_tags_correctly(self, mock_send):
        mock_send.return_value = {"id": "id"}

        user = User.objects.create_user(email="user@example.com", password="x")
        senders.send_verification(user, verification_url="https://steblik.com/v/abc")

        params = mock_send.call_args[0][0]
        assert params["to"] == ["user@example.com"]
        assert "Verify" in params["subject"]
        # Both bodies rendered.
        assert "text" in params and "html" in params

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_password_reset_tags_correctly(self, mock_send):
        mock_send.return_value = {"id": "id"}

        user = User.objects.create_user(email="user@example.com", password="x")
        senders.send_password_reset(user, reset_url="https://steblik.com/r/xyz")

        params = mock_send.call_args[0][0]
        assert "Reset" in params["subject"]

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_newsletter_includes_list_unsubscribe(self, mock_send):
        mock_send.return_value = {"id": "id"}

        sub = User.objects.create_user(email="reader@example.com", password="x")
        senders.send_newsletter(
            subscriber=sub,
            subject="Issue #1",
            body_markdown="Hello world",
            unsubscribe_url="https://steblik.com/u/token",
        )

        params = mock_send.call_args[0][0]
        assert "List-Unsubscribe" in params["headers"]
        assert "https://steblik.com/u/token" in params["headers"]["List-Unsubscribe"]
        assert params["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
