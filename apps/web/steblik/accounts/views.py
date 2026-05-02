from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from apps.web.steblik.blog.services import all_posts

from .models import User


@login_required
def my_profile(request: HttpRequest) -> HttpResponse:
    premium_posts = [p for p in all_posts() if p.premium]
    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "premium_posts": premium_posts,
        },
    )


@require_http_methods(["GET", "POST"])
def unsubscribe(request: HttpRequest, token: str) -> HttpResponse:
    """
    GET  — show a confirmation page (user-initiated click from email footer).
    POST — immediately opt out, no further confirmation required.
           Also handles RFC 8058 one-click unsubscribe from mail clients.
    """
    user = get_object_or_404(User, unsubscribe_token=token)

    if request.method == "POST":
        if user.marketing_consent:
            user.marketing_consent = False
            user.save(update_fields=["marketing_consent"])
        return render(request, "accounts/unsubscribed.html")

    return render(request, "accounts/unsubscribe_confirm.html", {"token": token})
