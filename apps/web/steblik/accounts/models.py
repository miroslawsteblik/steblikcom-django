import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # type: ignore[assignment]  # email is the identifier
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore[assignment]

    marketing_consent = models.BooleanField(
        default=False,
        help_text="User has explicitly opted in to marketing email (PECR).",
    )
    unsubscribe_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Stable token for one-click unsubscribe links (RFC 8058).",
    )


class Announcement(models.Model):
    subject = models.CharField(max_length=255)
    post_slug = models.CharField(
        max_length=200,
        blank=True,
        help_text="Blog post slug to announce. Renders the 'new post' email template.",
    )
    body_text = models.TextField(help_text="Plain-text email body (required).")
    body_html = models.TextField(
        blank=True, help_text="HTML override — leave blank to auto-render from post_slug."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    total_sent = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.subject

    @property
    def is_sent(self) -> bool:
        return self.sent_at is not None


class AnnouncementRecipient(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    email = models.EmailField()
    status = models.CharField(max_length=10, choices=Status.choices)
    resend_email_id = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return f"{self.email} — {self.status}"
