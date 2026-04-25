"""Markdown rendering with HTML sanitization.

Called once on model save; output is stored in the DB. Safe to trust
the cached HTML on render because bleach runs here.
"""
import bleach
import markdown2

ALLOWED_TAGS = [
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "em", "strong", "del", "ins",
    "code", "pre",
    "blockquote", "hr", "br",
    "img",
    "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "code": ["class"],  # for syntax highlighting classes
    "pre": ["class"],
    "th": ["align"],
    "td": ["align"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown_safe(text: str) -> str:
    """Render markdown to sanitized HTML. Safe to mark |safe in templates."""
    if not text:
        return ""
    html = markdown2.markdown(
        text,
        extras=[
            "fenced-code-blocks",
            "tables",
            "strike",
            "task_list",
            "header-ids",
            "code-friendly",
        ],
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )