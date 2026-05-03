from __future__ import annotations

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """
    Routes allauth transactional emails through our styled senders
    instead of allauth's plain-text defaults.
    """

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        # Import here to avoid circular imports at module load time.
        from steblik.emailing import senders

        user = context.get("user")

        if template_prefix in (
            "account/email/email_confirmation_signup",
            "account/email/email_confirmation",
        ):
            if user:
                senders.send_verification(
                    user,
                    verification_url=context.get("activate_url", ""),
                )
                return

        elif template_prefix == "account/email/password_reset_key" and user:
            senders.send_password_reset(
                user,
                reset_url=context.get("password_reset_url", ""),
            )
            return

        # Fall through to allauth's default plain-text handler for any
        # template prefix we don't explicitly handle above (e.g. email-change
        # notifications, login codes if MFA is ever enabled, etc.).
        super().send_mail(template_prefix, email, context)
