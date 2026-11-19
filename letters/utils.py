"""Small helpers shared across the letters app."""

import hashlib
import io
import secrets
import string

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify


ALPHABET = string.ascii_lowercase + string.digits


def generate_share_slug(base: str, model, length: int = 12) -> str:
    """Return a unique, unguessable, human-friendly share slug."""
    base = slugify(base) or "to-my-love"
    for _ in range(12):
        token = "".join(secrets.choice(ALPHABET) for _ in range(length))
        slug = f"{base}-{token}"[:90]
        if not model.objects.filter(slug=slug).exists():
            return slug
    # Extremely unlikely fallback; token_hex is still unpredictable.
    return f"{base}-{secrets.token_hex(8)}"[:90]


def hash_ip(ip: str) -> str:
    """Hash an IP address so raw addresses are never stored."""
    if not ip:
        return ""
    salted = f"{settings.SECRET_KEY}:{ip}".encode()
    return hashlib.sha256(salted).hexdigest()


def client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def absolute_url(request, path: str) -> str:
    """Build an absolute URL, honouring SITE_URL for deployed environments."""
    if settings.SITE_URL:
        return f"{settings.SITE_URL}{path}"
    return request.build_absolute_uri(path)


def human_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


_FONT_STACKS = {
    "elegant": "'Cormorant Garamond', 'Times New Roman', serif",
    "handwritten": "'Caveat', 'Segoe Script', cursive",
    "romantic": "'Great Vibes', 'Brush Script MT', cursive",
    "classic": "'Libre Baskerville', Georgia, serif",
    "modern": "'Outfit', 'Helvetica Neue', sans-serif",
    "typewriter": "'Courier Prime', 'Courier New', monospace",
}


def font_stack(style: str) -> str:
    return _FONT_STACKS.get(style, _FONT_STACKS["elegant"])


def optimize_photo_field(field_file, max_dimension: int = 1920) -> None:
    """Strip metadata (EXIF/GPS), honour orientation and shrink huge photos.

    Re-encoding through Pillow also removes any embedded payloads that are not
    part of the actual image. Animated GIFs are left untouched.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover - Pillow is a hard dependency
        return

    try:
        img = Image.open(field_file)
        if getattr(img, "is_animated", False):
            return
        img.load()
        fmt = (img.format or "JPEG").upper()
        img = ImageOps.exif_transpose(img)
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        if fmt in {"JPEG", "JPG"}:
            if img.mode not in {"RGB", "L"}:
                img = img.convert("RGB")
            fmt = "JPEG"
        elif fmt == "PNG":
            if img.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                img = img.convert("RGBA")
        buffer = io.BytesIO()
        save_kwargs = {"optimize": True}
        if fmt == "JPEG":
            save_kwargs.update({"quality": 88, "progressive": True})
        img.save(buffer, format=fmt, **save_kwargs)
        name = field_file.name
        field_file.save(name, ContentFile(buffer.getvalue()), save=False)
    except Exception:
        # If optimisation fails for an exotic-but-valid image, keep the
        # original upload (Django's ImageField has already verified it).
        return


def lighten_hex(hex_color: str, amount: float = 0.35) -> str:
    """Mix a hex colour toward white. Used for soft theme accents."""
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) != 6:
        return "#f7d3e3"
    try:
        r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return "#f7d3e3"
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"
