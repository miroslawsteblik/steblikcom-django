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
        assert "text" in params and "html" in params

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_password_reset_tags_correctly(self, mock_send):
        mock_send.return_value = {"id": "id"}

        user = User.objects.create_user(email="user@example.com", password="x")
        senders.send_password_reset(user, reset_url="https://steblik.com/r/xyz")

        params = mock_send.call_args[0][0]
        assert "Reset" in params["subject"]
        assert "text" in params and "html" in params

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_welcome_email_sent(self, mock_send):
        mock_send.return_value = {"id": "id"}

        user = User.objects.create_user(email="new@example.com", password="x")
        senders.send_welcome(user)

        params = mock_send.call_args[0][0]
        assert params["to"] == ["new@example.com"]
        assert "Welcome" in params["subject"]
        assert "text" in params and "html" in params

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_welcome_uses_first_name_in_html(self, mock_send):
        mock_send.return_value = {"id": "id"}

        user = User.objects.create_user(email="named@example.com", password="x", first_name="Alice")
        senders.send_welcome(user)

        params = mock_send.call_args[0][0]
        assert "Alice" in params["html"]

    @patch("steblik.emailing.backend.resend.Emails.send")
    def test_newsletter_includes_list_unsubscribe(self, mock_send):
        mock_send.return_value = {"id": "id"}

        sub = User.objects.create_user(email="reader@example.com", password="x")
        senders.send_newsletter(
            subscriber=sub,
            subject="Issue #1",
            body_markdown="Hello world",
            unsubscribe_url="https://steblik.com/me/unsubscribe/some-token/",
        )

        params = mock_send.call_args[0][0]
        assert "List-Unsubscribe" in params["headers"]
        assert (
            "https://steblik.com/me/unsubscribe/some-token/"
            in params["headers"]["List-Unsubscribe"]
        )
        assert params["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


@pytest.mark.django_db
class TestUnsubscribeView:
    def test_get_shows_confirmation_page(self, client):
        user = User.objects.create_user(email="u@example.com", password="x")
        response = client.get(f"/me/unsubscribe/{user.unsubscribe_token}/")
        assert response.status_code == 200
        assert b"Unsubscribe" in response.content

    def test_post_sets_marketing_consent_false(self, client):
        user = User.objects.create_user(email="u@example.com", password="x", marketing_consent=True)
        response = client.post(f"/me/unsubscribe/{user.unsubscribe_token}/")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.marketing_consent is False

    def test_post_invalid_token_returns_404(self, client):
        import uuid

        response = client.post(f"/me/unsubscribe/{uuid.uuid4()}/")
        assert response.status_code == 404

    def test_post_idempotent_when_already_unsubscribed(self, client):
        user = User.objects.create_user(
            email="u@example.com", password="x", marketing_consent=False
        )
        response = client.post(f"/me/unsubscribe/{user.unsubscribe_token}/")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.marketing_consent is False
