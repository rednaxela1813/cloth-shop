from __future__ import annotations

import io

from PIL import Image, ImageChops, ImageOps
from django.core.files.base import ContentFile
from django.utils.text import slugify


def _base_name(branding) -> str:
    base = slugify(branding.site_name or "site-logo")[:80] or "site-logo"
    return f"{base}-{branding.pk or 'new'}"


def _delete_file_if_exists(storage, name: str) -> None:
    if not name:
        return
    try:
        if storage.exists(name):
            storage.delete(name)
    except Exception:
        return


def _make_logo_webp(*, uploaded_file, filename: str, max_width: int, max_height: int, quality: int = 88) -> ContentFile:
    uploaded_file.seek(0)

    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)

    # Trim transparent/flat whitespace so the logo doesn't look tiny in the navbar.
    if image.mode in ("RGBA", "LA"):
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            image = image.crop(bbox)
    else:
        background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
        diff = ImageChops.difference(image, background)
        bbox = diff.getbbox()
        if bbox:
            image = image.crop(bbox)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    image.thumbnail((max_width, max_height))

    out = io.BytesIO()
    image.save(out, format="WEBP", quality=quality, method=6)
    out.seek(0)

    if not filename.lower().endswith(".webp"):
        filename = f"{filename}.webp"

    return ContentFile(out.getvalue(), name=filename)


def process_site_branding_after_save(branding) -> None:
    if getattr(branding, "_processing", False):
        return

    if not branding.logo_original:
        if branding.logo_header:
            storage = branding.logo_header.storage
            old_name = branding.logo_header.name
            branding.logo_header.delete(save=False)
            _delete_file_if_exists(storage, old_name)
            branding.__class__.objects.filter(pk=branding.pk).update(logo_header="")
        return

    branding._processing = True
    try:
        old_header = branding.logo_header.name if branding.logo_header else ""
        logo_header = _make_logo_webp(
            uploaded_file=branding.logo_original.file,
            filename=f"{_base_name(branding)}-header.webp",
            max_width=420,
            max_height=120,
            quality=88,
        )
        branding.logo_header.save(logo_header.name, logo_header, save=False)
        branding.save(update_fields=["logo_header"])

        if old_header and old_header != branding.logo_header.name:
            _delete_file_if_exists(branding.logo_header.storage, old_header)
    finally:
        branding._processing = False
