import mimetypes

from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from .services import POSTS_DIR, all_posts, all_tags, get_post, posts_by_tag


def post_list(request: HttpRequest) -> HttpResponse:
    return render(request, "blog/list.html", {"posts": all_posts(), "tags": all_tags()})


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_post(slug)
    if post is None:
        raise Http404
    return render(request, "blog/detail.html", {"post": post})


def tag_list(request: HttpRequest, tag: str) -> HttpResponse:
    return render(
        request,
        "blog/list.html",
        {"posts": posts_by_tag(tag), "tags": all_tags(), "active_tag": tag},
    )


def post_asset(_request: HttpRequest, slug: str, filename: str) -> FileResponse:
    post_dir = (POSTS_DIR / slug).resolve()
    asset_path = (post_dir / filename).resolve()
    # Prevent path traversal outside the post directory
    if not str(asset_path).startswith(str(post_dir) + "/"):
        raise Http404
    if not asset_path.is_file():
        raise Http404
    content_type, _ = mimetypes.guess_type(asset_path.name)
    return FileResponse(asset_path.open("rb"), content_type=content_type or "application/octet-stream")
