from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from .sitemaps import BlogSitemap, StaticViewSitemap

sitemaps = {
    "blog": BlogSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("manage/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("blog/", include("steblik.blog.urls")),
    path("me/", include("steblik.accounts.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("", include("steblik.pages.urls")),  # catch-all last
]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
