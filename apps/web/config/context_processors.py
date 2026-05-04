from django.conf import settings


def site_meta(request):
    if request.user.is_authenticated:
        nav_items = [
            {"label": "Members", "url_name": "blog:post_list"},
            {"label": "Dashboard", "url_name": "profile"},
        ]
    else:
        nav_items = [
            {"label": "Blog", "url_name": "blog:post_list"},
            {"label": "About", "url_name": "pages:about"},
            # {"label": "Services", "url_name": "pages:experience"},
        ]

    return {
        "site_meta": settings.SITE_META,
        "nav_items": nav_items,
    }
