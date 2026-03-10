# project/apps/seo/templatetags/seo_tags.py
from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def absurl(request, path: str) -> str:
    """
    Build absolute URL from a request + relative path.

    Usage in templates:
        {{ request|absurl:"/catalog/" }}
        {{ request|absurl:crumb.url }}
    """
    if request is None:
        return path or ""
    if not path:
        return request.build_absolute_uri("/")
    return request.build_absolute_uri(path)
