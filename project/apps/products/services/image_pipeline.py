#project/apps/products/services/image_pipeline.py
import io
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def make_webp(
    *,
    uploaded_file,
    filename: str,
    max_size: int,
    quality: int = 82,
) -> ContentFile:
    """
    Берёт загруженный файл (UploadedFile/ImageFieldFile.file),
    делает WEBP, ресайзит по max_size (ограничение по длинной стороне),
    возвращает ContentFile.
    """
    uploaded_file.seek(0)

    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)

    # RGBA если есть альфа, иначе RGB
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size))

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=quality, method=6)
    out.seek(0)

    if not filename.lower().endswith(".webp"):
        filename = f"{filename}.webp"

    return ContentFile(out.getvalue(), name=filename)
