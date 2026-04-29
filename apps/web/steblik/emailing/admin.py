from django.contrib import admin

from .models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "email_type", "status", "recipient", "subject")
    list_filter = ("status", "email_type", "created_at")
    search_fields = ("recipient", "subject", "provider_message_id")
    readonly_fields = (
        "recipient",
        "subject",
        "email_type",
        "status",
        "provider_message_id",
        "error",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
