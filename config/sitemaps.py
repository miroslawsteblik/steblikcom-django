from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.services import all_posts


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["pages:home", "pages:about"]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return all_posts()

    def location(self, post):
        return reverse("blog:post_detail", args=[post.slug])

    def lastmod(self, post):
        return post.date
