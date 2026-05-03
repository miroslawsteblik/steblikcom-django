from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "steblik.accounts"
    label = "accounts"

    def ready(self) -> None:
        from allauth.account.signals import email_confirmed
        from django.dispatch import receiver

        @receiver(email_confirmed, dispatch_uid="accounts.send_welcome_on_confirm")
        def on_email_confirmed(sender, request, email_address, **kwargs) -> None:
            from steblik.emailing.senders import send_welcome

            send_welcome(email_address.user)
