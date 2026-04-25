import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

import frontmatter
import markdown

POSTS_DIR = Path(__file__).parent / "posts"

MD = markdown.Markdown(
    extensions=["fenced_code", "codehilite", "tables", "toc"],
    extension_configs={"codehilite": {"guess_lang": False, "css_class": "highlight"}},
)


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: date
    tags: tuple[str, ...]
    summary: str
    html: str
    draft: bool
    card_image_url: str = field(default="")  # thumbnail shown on list cards
    banner_image_url: str = field(default="")  # full-width banner on detail page


def _asset_url(slug: str, filename: str) -> str:
    return f"/blog/{slug}/assets/{filename}"


def _rewrite_image_srcs(html: str, slug: str) -> str:
    """Rewrite relative img src attributes to post asset URLs."""

    def replace(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith(("http://", "https://", "/")):
            return m.group(0)
        return f'src="{_asset_url(slug, src)}"'

    return re.sub(r'src="([^"]*)"', replace, html)


def _load_post(path: Path) -> Post:
    if path.is_dir():
        md_path = path / "index.md"
        is_dir_post = True
    else:
        md_path = path
        is_dir_post = False

    fm = frontmatter.load(str(md_path))
    slug = str(fm["slug"])

    MD.reset()
    html = MD.convert(fm.content)
    if is_dir_post:
        html = _rewrite_image_srcs(html, slug)

    def _resolve(raw: str) -> str:
        if raw and not raw.startswith(("http://", "https://", "/")):
            return _asset_url(slug, raw)
        return raw

    card_image_url = _resolve(str(fm.get("card_image", "")))
    banner_image_url = _resolve(str(fm.get("banner_image", "")))

    return Post(
        slug=slug,
        title=str(fm["title"]),
        date=fm["date"],  # type: ignore[arg-type]  # frontmatter parses YAML dates correctly
        tags=tuple(str(t) for t in (fm.get("tags") or [])),  # type: ignore[union-attr]
        summary=str(fm.get("summary", "")),
        draft=bool(fm.get("draft", False)),
        html=html,
        card_image_url=card_image_url,
        banner_image_url=banner_image_url,
    )


@lru_cache(maxsize=1)
def all_posts() -> list[Post]:
    posts: list[Post] = []
    for entry in POSTS_DIR.iterdir():
        if (entry.is_dir() and (entry / "index.md").exists()) or (
            entry.is_file() and entry.suffix == ".md"
        ):
            posts.append(_load_post(entry))
    return sorted([p for p in posts if not p.draft], key=lambda p: p.date, reverse=True)


def get_post(slug: str) -> Post | None:
    return next((p for p in all_posts() if p.slug == slug), None)


def recent_posts(n: int = 3) -> list[Post]:
    return all_posts()[:n]


def posts_by_tag(tag: str) -> list[Post]:
    return [p for p in all_posts() if tag in p.tags]


def all_tags() -> list[tuple[str, int]]:
    """Return sorted list of (tag, post_count) pairs."""
    counts: dict[str, int] = {}
    for post in all_posts():
        for tag in post.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items())
