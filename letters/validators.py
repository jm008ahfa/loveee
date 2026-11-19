"""Upload validators. Extensions are checked by the fields; size is checked here."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_image_size(value: UploadedFile) -> None:
    limit = getattr(settings, "MAX_PHOTO_SIZE", 5 * 1024 * 1024)
    if value.size and value.size > limit:
        raise ValidationError(
            f"Photos must be smaller than {limit // (1024 * 1024)} MB."
        )


def validate_audio_size(value: UploadedFile) -> None:
    limit = getattr(settings, "MAX_MUSIC_SIZE", 15 * 1024 * 1024)
    if value.size and value.size > limit:
        raise ValidationError(
            f"Music files must be smaller than {limit // (1024 * 1024)} MB."
        )
