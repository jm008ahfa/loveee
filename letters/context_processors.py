from django.conf import settings


def site_settings(request):
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "To My Love"),
        "SITE_URL": getattr(settings, "SITE_URL", ""),
        "MAX_PHOTOS": getattr(settings, "MAX_PHOTOS_PER_LETTER", 12),
        "DEBUG": settings.DEBUG,
    }
