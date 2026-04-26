from django.conf import settings


def site_meta(request):
    return {
        "site_meta": settings.SITE_META,
        "nav_items": [
            {"label": "Blog", "url_name": "blog:post_list"},
            {"label": "About", "url_name": "pages:about"},
            {"label": "Experience", "url_name": "pages:experience"},
        ],
    }
