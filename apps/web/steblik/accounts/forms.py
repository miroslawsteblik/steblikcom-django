from __future__ import annotations

from django import forms


class CustomSignupForm(forms.Form):
    """Extra fields injected into the allauth signup flow.

    allauth calls signup(request, user) after the core User is created.
    Do not inherit from allauth's SignupForm — that causes a circular import
    because allauth.account.forms is still loading when it imports this class.
    """

    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="First name",
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    marketing_consent = forms.BooleanField(
        required=False,
        label=("Email me about new posts and upcoming courses. You can unsubscribe at any time."),
    )

    def signup(self, request, user) -> None:  # type: ignore[override]
        user.first_name = self.cleaned_data.get("first_name", "").strip()
        user.marketing_consent = self.cleaned_data.get("marketing_consent", False)
        user.save(update_fields=["first_name", "marketing_consent"])
