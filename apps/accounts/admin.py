from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest
from django.shortcuts import redirect

from allauth.account.models import EmailAddress

from .models import Announcement, AnnouncementRecipient, User
from .services import send_announcement


class EmailAddressInline(admin.TabularInline):
    model = EmailAddress
    extra = 0
    readonly_fields = ("email", "verified", "primary")
    can_delete = False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [EmailAddressInline]
    list_display = ("email", "is_active", "is_staff", "date_joined", "last_login")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email",)
    ordering = ("-date_joined",)


class AnnouncementRecipientInline(admin.TabularInline):
    model = AnnouncementRecipient
    extra = 0
    readonly_fields = ("email", "status", "resend_email_id", "error", "created_at")
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:  # noqa: ARG002
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("subject", "sent_at", "total_sent", "total_failed", "created_at")
    list_filter = ("sent_at",)
    search_fields = ("subject",)
    inlines = [AnnouncementRecipientInline]
    change_form_template = "admin/accounts/announcement/change_form.html"

    def get_readonly_fields(self, request: HttpRequest, obj=None):  # noqa: ARG002
        base = ("sent_at", "sent_by", "total_sent", "total_failed", "created_at")
        if obj and obj.is_sent:
            return base + ("subject", "post_slug", "body_text", "body_html")
        return base

    def response_change(self, request: HttpRequest, obj: Announcement):
        if "_send_now" in request.POST:
            if obj.is_sent:
                self.message_user(request, "This announcement has already been sent.", level=messages.ERROR)
                return redirect(request.path)
            try:
                sent, failed = send_announcement(obj, sent_by=request.user)
                self.message_user(
                    request,
                    f"Announcement sent — {sent} delivered, {failed} failed.",
                    level=messages.SUCCESS if failed == 0 else messages.WARNING,
                )
            except Exception as e:
                self.message_user(request, f"Send failed: {e}", level=messages.ERROR)
            return redirect(request.path)
        return super().response_change(request, obj)
