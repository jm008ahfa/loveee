from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .utils import generate_share_slug
from .validators import validate_audio_size, validate_image_size


class User(AbstractUser):
    """Platform member. Extends Django's auth user with a friendly name."""

    display_name = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.display_name or self.get_username()

    @property
    def friendly_name(self) -> str:
        return self.display_name or self.first_name or self.get_username()

    @property
    def initial(self) -> str:
        return self.friendly_name[:1].upper()


class LetterTheme(models.Model):
    """A romantic visual theme selectable in the letter creator."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    tagline = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=200, blank=True)

    primary_color = models.CharField(max_length=9, default="#e46b8f")
    secondary_color = models.CharField(max_length=9, default="#9b6bd6")
    accent_color = models.CharField(max_length=9, default="#d94f79")
    paper_color = models.CharField(max_length=9, default="#fff8f3")
    ink_color = models.CharField(max_length=9, default="#4b2b3a")
    background_css = models.CharField(
        max_length=400,
        default="linear-gradient(160deg,#fde8ef 0%,#f7d3e3 45%,#e8d8ff 100%)",
        help_text="Any CSS background value used behind the letter.",
    )
    heading_font = models.CharField(max_length=120, default="'Cormorant Garamond', serif")
    body_font = models.CharField(max_length=120, default="'Cormorant Garamond', serif")

    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "letter theme"
        verbose_name_plural = "letter themes"

    def __str__(self) -> str:
        return self.name

    @property
    def css_vars(self) -> str:
        return (
            f"--primary:{self.primary_color};--secondary:{self.secondary_color};"
            f"--accent:{self.accent_color};--paper:{self.paper_color};"
            f"--ink:{self.ink_color};"
        )


class BackgroundMusic(models.Model):
    """A royalty-free track in the music library (or an external URL)."""

    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=40, blank=True)
    audio = models.FileField(
        upload_to="music/",
        blank=True,
        validators=[
            FileExtensionValidator(["mp3", "ogg", "wav", "m4a", "aac", "webm"]),
            validate_audio_size,
        ],
    )
    audio_url = models.URLField(
        blank=True,
        help_text="Used when no audio file is uploaded (must be a direct audio link).",
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "background music"
        verbose_name_plural = "background music"

    def __str__(self) -> str:
        return f"{self.title} — {self.artist}" if self.artist else self.title

    @property
    def source(self) -> str:
        if self.audio:
            return self.audio.url
        return self.audio_url


class LoveLetter(models.Model):
    """A personalized love letter that can be saved as a draft or published."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class Occasion(models.TextChoices):
        JUST_BECAUSE = "just-because", "Just because"
        VALENTINE = "valentine", "Valentine's Day"
        ANNIVERSARY = "anniversary", "Anniversary"
        BIRTHDAY = "birthday", "Birthday"
        WEDDING = "wedding", "Wedding"
        APOLOGY = "apology", "I'm sorry"
        PROPOSAL = "proposal", "Will you?"
        LONG_DISTANCE = "long-distance", "Long distance"
        MEMORIAL = "memorial", "In loving memory"
        SURPRISE = "surprise", "Random surprise"

    class FontStyle(models.TextChoices):
        ELEGANT = "elegant", "Elegant serif"
        HANDWRITTEN = "handwritten", "Handwritten"
        ROMANTIC = "romantic", "Romantic script"
        CLASSIC = "classic", "Classic book"
        MODERN = "modern", "Modern & clean"
        TYPEWRITER = "typewriter", "Typewriter"

    class Animation(models.TextChoices):
        HEARTS = "hearts", "Floating hearts"
        PETALS = "petals", "Rose petals"
        SPARKLES = "sparkles", "Golden sparkles"
        STARS = "stars", "Starry night"
        NONE = "none", "Calm (no particles)"

    class Backdrop(models.TextChoices):
        THEME = "theme", "Follow the theme"
        BLUSH = "blush", "Blush clouds"
        ROSE = "rose", "Rose garden"
        LAVENDER = "lavender", "Lavender dusk"
        MIDNIGHT = "midnight", "Midnight romance"
        GOLDEN = "golden", "Golden hour"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="letters"
    )
    slug = models.SlugField(max_length=90, unique=True, blank=True, db_index=True)

    title = models.CharField(max_length=120, default="A letter for you")
    recipient_name = models.CharField(max_length=60)
    sender_name = models.CharField(max_length=60)
    message = models.TextField(
        help_text="Write from the heart. Line breaks are preserved."
    )
    closing_note = models.CharField(
        max_length=200, default="You will always be special to me."
    )
    occasion = models.CharField(
        max_length=20, choices=Occasion.choices, default=Occasion.JUST_BECAUSE
    )
    special_date = models.DateField(
        null=True,
        blank=True,
        help_text="Adds a live countdown to your letter.",
    )

    theme = models.ForeignKey(
        LetterTheme, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="letters",
    )
    music = models.ForeignKey(
        BackgroundMusic, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="letters",
    )
    music_file = models.FileField(
        upload_to="letters/music/",
        blank=True,
        validators=[
            FileExtensionValidator(["mp3", "ogg", "wav", "m4a", "aac", "webm"]),
            validate_audio_size,
        ],
    )
    music_url = models.URLField(blank=True, help_text="Optional direct audio link.")

    font_style = models.CharField(
        max_length=20, choices=FontStyle.choices, default=FontStyle.HANDWRITTEN
    )
    backdrop = models.CharField(
        max_length=20, choices=Backdrop.choices, default=Backdrop.THEME
    )
    animation = models.CharField(
        max_length=20, choices=Animation.choices, default=Animation.HEARTS
    )

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Show this letter in the public 'Letters of love' gallery.",
    )
    access_password = models.CharField(max_length=128, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    view_count = models.PositiveIntegerField(default=0, editable=False)
    last_opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["status", "is_public", "-published_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} → {self.recipient_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"to-my-love"
            self.slug = generate_share_slug(base, self.__class__)
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("letters:letter", kwargs={"slug": self.slug})

    # -- Access helpers -----------------------------------------------------
    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def has_password(self) -> bool:
        return bool(self.access_password)

    def set_access_password(self, raw_password: str) -> None:
        from django.contrib.auth.hashers import make_password

        self.access_password = make_password(raw_password) if raw_password else ""

    def check_access_password(self, raw_password: str) -> bool:
        from django.contrib.auth.hashers import check_password

        if not self.has_password:
            return True
        return check_password(raw_password or "", self.access_password)

    @property
    def first_photo(self):
        photos = list(self.photos.all()[:1])
        return photos[0] if photos else None

    @property
    def music_source(self) -> str:
        from django.templatetags.static import static

        if self.music_file:
            return self.music_file.url
        if self.music_url:
            return self.music_url
        if self.music and self.music.source:
            return self.music.source
        return static("audio/romantic-ambient.wav")

    @property
    def has_music(self) -> bool:
        if self.music_file or self.music_url:
            return True
        return bool(self.music and self.music.source)


    @property
    def color_theme(self) -> LetterTheme | None:
        return self.theme

    def occasion_emoji(self) -> str:
        return {
            "just-because": "💌",
            "valentine": "💘",
            "anniversary": "💞",
            "birthday": "🎂",
            "wedding": "💍",
            "apology": "🌷",
            "proposal": "💎",
            "long-distance": "✈️",
            "memorial": "🕊️",
            "surprise": "🎁",
        }.get(self.occasion, "💌")

    def publish(self) -> None:
        if not self.slug:
            self.slug = generate_share_slug("to-my-love", self.__class__)
        self.status = self.Status.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=["slug", "status", "published_at", "updated_at"])

    def unpublish(self) -> None:
        self.status = self.Status.DRAFT
        self.save(update_fields=["status", "updated_at"])


def photo_upload_path(instance: "LetterPhoto", filename: str) -> str:
    import uuid
    from pathlib import Path

    ext = Path(filename).suffix.lower().lstrip(".") or "jpg"
    return f"letters/photos/{instance.letter_id}/{uuid.uuid4().hex}.{ext}"


class LetterPhoto(models.Model):
    letter = models.ForeignKey(
        LoveLetter, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(
        upload_to=photo_upload_path,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"]),
            validate_image_size,
        ],
    )
    caption = models.CharField(max_length=140, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.caption or f"Photo for {self.letter.recipient_name}"


class LetterView(models.Model):
    """One recorded open of a published letter (privacy-friendly: hashed IP)."""

    letter = models.ForeignKey(
        LoveLetter, on_delete=models.CASCADE, related_name="views"
    )
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    referrer = models.CharField(max_length=300, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-viewed_at"]
        verbose_name = "letter view"
        verbose_name_plural = "letter views"

    def __str__(self) -> str:
        return f"{self.letter.title} viewed {self.viewed_at:%Y-%m-%d %H:%M}"
