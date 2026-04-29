from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("tag/<slug:tag>/", views.tag_list, name="tag_list"),
    path("<slug:slug>/assets/<path:filename>", views.post_asset, name="post_asset"),
    path("<slug:slug>/", views.post_detail, name="post_detail"),
]
