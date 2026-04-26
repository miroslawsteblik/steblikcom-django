from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.blog.services import all_posts


@login_required
def my_profile(request):
    premium_posts = [p for p in all_posts() if p.premium]
    return render(request, "accounts/profile.html", {
        "user": request.user,
        "premium_posts": premium_posts,
    })
