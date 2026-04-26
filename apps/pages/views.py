from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from ..blog.services import recent_posts


@cache_page(60 * 15)
def home(request):
    return render(request, "pages/home.html", {"recent_posts": recent_posts(3)})


@cache_page(60 * 15)
def about(request):
    return render(request, "pages/about.html")

@cache_page(60 * 15)
def blog(request):
    return render(request, "pages/about.html")

@cache_page(60 * 15)
def experience(request):
    return render(request, "pages/experience.html")


@cache_page(60 * 15)
def references(request):
    raise Http404

    refs = [
        {
            "name": "Alice Chen",
            "role": "CTO, Acme Data",
            "quote": "Filip built the most resilient pipeline we've ever deployed.",
            "photo": "img/refs/alice.jpg",
        },
        {
            "name": "Bob Singh",
            "role": "Head of Analytics, Beta Corp",
            "quote": "Turned our reporting chaos into a working dbt project in a month.",
            "photo": "img/refs/bob.jpg",
        },
    ]
    return render(request, "pages/references.html", {"references": refs})


# pages/views.py
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /manage/",
        "Disallow: /accounts/",
        "Disallow: /me/",
        "",
        f"Sitemap: https://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
