import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, F, Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    LetterPasswordForm,
    LetterPhotoForm,
    LetterSearchForm,
    LoginForm,
    LoveLetterForm,
    SignupForm,
)
from .models import BackgroundMusic, LetterPhoto, LetterTheme, LetterView, LoveLetter
from .utils import (
    absolute_url,
    client_ip,
    font_stack,
    hash_ip,
    lighten_hex,
    optimize_photo_field,
)

DEFAULT_THEME = {
    "primary_color": "#e46b8f",
    "secondary_color": "#9b6bd6",
    "accent_color": "#d94f79",
    "paper_color": "#fff8f3",
    "ink_color": "#4b2b3a",
    "background_css": "linear-gradient(160deg,#fde8ef 0%,#f7d3e3 45%,#e8d8ff 100%)",
    "heading_font": "'Cormorant Garamond', serif",
}


# ---------------------------------------------------------------------------
# Landing & discovery
# ---------------------------------------------------------------------------
def home(request):
    featured = (
        LoveLetter.objects.filter(status=LoveLetter.Status.PUBLISHED, is_public=True)
        .select_related("theme")
        .prefetch_related("photos")[:3]
    )
    themes = LetterTheme.objects.filter(is_active=True)[:8]
    stats = {
        "letters": LoveLetter.objects.filter(status=LoveLetter.Status.PUBLISHED).count(),
        "views": LoveLetter.objects.aggregate(total=Sum("view_count"))["total"] or 0,
        "people": LoveLetter.objects.values("owner").distinct().count(),
    }
    return render(
        request,
        "letters/home.html",
        {"featured": featured, "themes": themes, "stats": stats},
    )


def explore(request):
    letters = (
        LoveLetter.objects.filter(status=LoveLetter.Status.PUBLISHED, is_public=True)
        .select_related("theme", "owner")
        .prefetch_related("photos")
    )
    query = request.GET.get("q", "").strip()[:80]
    if query:
        letters = letters.filter(recipient_name__icontains=query) | letters.filter(
            title__icontains=query
        )
    paginator = Paginator(letters, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "letters/explore.html", {"page": page, "query": query})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def signup(request):
    if request.user.is_authenticated:
        return redirect("letters:dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.display_name = form.cleaned_data.get("display_name") or form.cleaned_data["username"]
        user.save()
        auth_login(request, user)
        messages.success(request, "Welcome to To My Love. Your first letter is waiting to be written.")
        return redirect("letters:editor_create")
    return render(request, "letters/auth/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("letters:dashboard")
    if request.method == "POST":
        ip = hash_ip(client_ip(request))[:16]
        attempts_key = f"login-attempts:{ip}"
        attempts = cache.get(attempts_key, 0)
        if attempts >= 10:
            messages.error(request, "Too many attempts. Please wait a few minutes and try again.")
            return render(request, "letters/auth/login.html", {"form": LoginForm(request)})
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            cache.delete(attempts_key)
            auth_login(request, form.get_user())
            nxt = request.POST.get("next") or request.GET.get("next")
            if nxt and nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            messages.success(request, "Welcome back. Your letters are right here.")
            return redirect("letters:dashboard")
        cache.set(attempts_key, attempts + 1, 300)
    else:
        form = LoginForm(request)
    return render(
        request, "letters/auth/login.html", {"form": form, "next": request.GET.get("next", "")}
    )


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been signed out. Come back soon.")
    return redirect("letters:home")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    base = LoveLetter.objects.filter(owner=request.user)
    form = LetterSearchForm(request.GET or None)
    letters = base.select_related("theme").prefetch_related("photos")
    query = request.GET.get("q", "").strip()[:80]
    status = request.GET.get("status", "")
    if query:
        letters = letters.filter(recipient_name__icontains=query) | letters.filter(
            title__icontains=query
        )
    if status in {"published", "draft"}:
        letters = letters.filter(status=status)

    stats = {
        "total": base.count(),
        "published": base.filter(status=LoveLetter.Status.PUBLISHED).count(),
        "drafts": base.filter(status=LoveLetter.Status.DRAFT).count(),
        "views": base.aggregate(total=Sum("view_count"))["total"] or 0,
        "photos": LetterPhoto.objects.filter(letter__owner=request.user).count(),
    }
    paginator = Paginator(letters, 9)
    page = paginator.get_page(request.GET.get("page"))
    themes = LetterTheme.objects.filter(is_active=True)
    return render(
        request,
        "letters/dashboard.html",
        {
            "page": page,
            "form": form,
            "stats": stats,
            "themes": themes,
            "query": query,
            "status": status,
        },
    )


# ---------------------------------------------------------------------------
# Creator / editor
# ---------------------------------------------------------------------------
def _collect_photo_uploads(request, letter, existing_count: int):
    """Validate & attach uploaded photos. Returns (added, errors)."""
    files = request.FILES.getlist("photos")
    if not files:
        return 0, []

    from django import forms as django_forms
    from django.core.exceptions import ValidationError
    from pathlib import Path

    image_field = django_forms.ImageField()
    limit = getattr(settings, "MAX_PHOTOS_PER_LETTER", 12)
    size_limit = getattr(settings, "MAX_PHOTO_SIZE", 5 * 1024 * 1024)
    allowed_ext = {"jpg", "jpeg", "png", "webp", "gif"}
    added, errors = 0, []
    idx = existing_count
    for upload in files:
        if idx >= limit:
            errors.append(f"You can add up to {limit} photos per letter.")
            break
        ext = Path(upload.name or "").suffix.lower().lstrip(".")
        if ext not in allowed_ext:
            errors.append(f"{upload.name}: only JPG, PNG, WEBP or GIF images are allowed.")
            continue
        if upload.size and upload.size > size_limit:
            errors.append(f"{upload.name}: photos must be smaller than {size_limit // (1024 * 1024)} MB.")
            continue
        try:
            image_field.clean(upload)
        except ValidationError as exc:
            errors.append(f"{upload.name}: {' '.join(exc.messages)}")
            continue
        photo = LetterPhoto(letter=letter, order=idx)
        photo.image = upload
        optimize_photo_field(photo.image)
        photo.save()
        idx += 1
        added += 1
    return added, errors


def _editor_context(request, letter, form, just_published=False):
    photos = letter.photos.all() if letter and letter.pk else []
    return {
        "letter": letter,
        "form": form,
        "photos": photos,
        "themes": LetterTheme.objects.filter(is_active=True),
        "music_library": BackgroundMusic.objects.filter(is_active=True),
        "fonts": LoveLetter.FontStyle.choices,
        "just_published": just_published,
        "max_photos": getattr(settings, "MAX_PHOTOS_PER_LETTER", 12),
        "preview_url": (
            reverse("letters:preview", kwargs={"slug": letter.slug}) if letter and letter.pk else ""
        ),
    }


@login_required
def editor_create(request):
    form = LoveLetterForm(
        request.POST or None,
        request.FILES or None,
        initial={"sender_name": request.user.friendly_name},
    )
    if request.method == "POST":
        action = request.POST.get("action", "draft")
        if action == "preview":
            # Drafts are always previewable by their owner.
            form.instance.status = LoveLetter.Status.DRAFT
        if form.is_valid():
            letter = form.save(commit=False)
            letter.owner = request.user
            if not letter.sender_name:
                letter.sender_name = request.user.friendly_name
            letter.save()
            added, errors = _collect_photo_uploads(request, letter, 0)
            for error in errors:
                messages.warning(request, error)
            if added:
                messages.success(request, f"{added} photo{'s' if added != 1 else ''} added.")
            if action == "publish":
                letter.publish()
                messages.success(request, "Your letter is live. Share the link with someone you love.")
                return redirect(reverse("letters:editor_update", kwargs={"slug": letter.slug}) + "?published=1")
            if action == "preview":
                return redirect("letters:preview", slug=letter.slug)
            messages.success(request, "Draft saved. You can come back and finish it anytime.")
            return redirect("letters:editor_update", slug=letter.slug)
    return render(request, "letters/editor.html", _editor_context(request, None, form))


@login_required
def editor_update(request, slug):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    form = LoveLetterForm(request.POST or None, request.FILES or None, instance=letter)
    if request.method == "POST":
        action = request.POST.get("action", "draft")
        if form.is_valid():
            letter = form.save()
            added, errors = _collect_photo_uploads(request, letter, letter.photos.count())
            for error in errors:
                messages.warning(request, error)
            if added:
                messages.success(request, f"{added} photo{'s' if added != 1 else ''} added.")
            if action == "publish":
                letter.publish()
                messages.success(request, "Your letter is live. Share the link with someone you love.")
                return redirect(reverse("letters:editor_update", kwargs={"slug": letter.slug}) + "?published=1")
            if action == "preview":
                if letter.status == LoveLetter.Status.DRAFT:
                    return redirect("letters:preview", slug=letter.slug)
                return redirect("letters:letter", slug=letter.slug)
            messages.success(request, "Your letter has been saved.")
            return redirect("letters:editor_update", slug=letter.slug)
    return render(
        request,
        "letters/editor.html",
        _editor_context(request, letter, form, just_published=request.GET.get("published") == "1"),
    )


@login_required
@require_POST
def letter_publish(request, slug):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    if not letter.message.strip():
        messages.error(request, "Write a few words before publishing.")
        return redirect("letters:editor_update", slug=letter.slug)
    letter.publish()
    messages.success(request, "Your love letter is published. Share it with your favourite person.")
    return redirect(reverse("letters:editor_update", kwargs={"slug": letter.slug}) + "?published=1")


@login_required
@require_POST
def letter_unpublish(request, slug):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    letter.unpublish()
    messages.success(request, "Your letter is back in drafts. Nobody can open the link right now.")
    return redirect("letters:dashboard")


@login_required
@require_POST
def letter_delete(request, slug):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    title = letter.title
    letter.delete()
    messages.success(request, f"“{title}” has been deleted.")
    return redirect("letters:dashboard")


@login_required
@require_POST
def letter_duplicate(request, slug):
    from django.core.files.base import ContentFile

    source = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    original_pk = source.pk
    source.pk = None
    source.slug = ""
    source.status = LoveLetter.Status.DRAFT
    source.is_public = False
    source.published_at = None
    source.view_count = 0
    source.last_opened_at = None
    source.title = f"{source.title} (copy)"
    source.save()
    for photo in LetterPhoto.objects.filter(letter_id=original_pk):
        photo.pk = None
        photo.letter = source
        with photo.image.open("rb") as fh:
            photo.image.save(
                photo.image.name.rsplit("/", 1)[-1], ContentFile(fh.read()), save=False
            )
        photo.save()
    messages.success(request, "A copy has been made. Make it yours.")
    return redirect("letters:editor_update", slug=source.slug)


@login_required
@require_POST
def photo_delete(request, slug, photo_id):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    photo = get_object_or_404(LetterPhoto, pk=photo_id, letter=letter)
    photo.delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    messages.success(request, "Photo removed.")
    return redirect("letters:editor_update", slug=letter.slug)


@login_required
@require_POST
def photo_reorder(request, slug):
    letter = get_object_or_404(LoveLetter, slug=slug, owner=request.user)
    try:
        data = json.loads(request.body.decode("utf-8"))
        order = data.get("order", [])
        ids = {photo.id for photo in letter.photos.all()}
        if not isinstance(order, list) or set(order) != ids:
            raise ValueError
    except (ValueError, AttributeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid photo order.")
    for index, photo_id in enumerate(order):
        LetterPhoto.objects.filter(pk=photo_id, letter=letter).update(order=index)
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Public recipient experience
# ---------------------------------------------------------------------------
def _theme_context(letter):
    theme = letter.theme
    data = {
        "primary": getattr(theme, "primary_color", DEFAULT_THEME["primary_color"]),
        "secondary": getattr(theme, "secondary_color", DEFAULT_THEME["secondary_color"]),
        "accent": getattr(theme, "accent_color", DEFAULT_THEME["accent_color"]),
        "paper": getattr(theme, "paper_color", DEFAULT_THEME["paper_color"]),
        "ink": getattr(theme, "ink_color", DEFAULT_THEME["ink_color"]),
        "background": getattr(theme, "background_css", DEFAULT_THEME["background_css"]),
        "heading_font": getattr(theme, "heading_font", DEFAULT_THEME["heading_font"]),
    }
    data["soft"] = lighten_hex(data["primary"], 0.72)
    data["soft_secondary"] = lighten_hex(data["secondary"], 0.76)
    data["letter_font"] = font_stack(letter.font_style)
    return data


def _record_view(request, letter):
    """Count an open once per visitor session per 30 minutes."""
    key = f"letter-seen:{letter.pk}"
    now = timezone.now().timestamp()
    last = request.session.get(key)
    if last and now - float(last) < 1800:
        return
    request.session[key] = now
    LetterView.objects.create(
        letter=letter,
        ip_hash=hash_ip(client_ip(request)),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
    )
    LoveLetter.objects.filter(pk=letter.pk).update(
        view_count=F("view_count") + 1, last_opened_at=timezone.now()
    )


def letter_detail(request, slug):
    letter = get_object_or_404(
        LoveLetter.objects.select_related("theme", "music", "owner").prefetch_related("photos"),
        slug=slug,
    )

    is_owner = request.user.is_authenticated and request.user == letter.owner
    if not letter.is_published:
        if is_owner:
            return render(request, "letters/letter_unavailable.html", {"letter": letter, "owner_view": True})
        raise Http404("This letter is not available.")

    unlock_key = f"letter-unlocked:{letter.pk}"
    unlocked = request.session.get(unlock_key, False)
    form = LetterPasswordForm()

    if letter.has_password and not unlocked:
        if request.method == "POST":
            form = LetterPasswordForm(request.POST)
            ip = hash_ip(client_ip(request))[:16]
            attempt_key = f"letter-unlock:{letter.pk}:{ip}"
            attempts = cache.get(attempt_key, 0)
            if attempts >= 8:
                form.add_error(
                    "password",
                    "Too many attempts. Please wait a few minutes and try again.",
                )
            elif form.is_valid():
                if letter.check_access_password(form.cleaned_data["password"]):
                    request.session[unlock_key] = True
                    request.session.modified = True
                    cache.delete(attempt_key)
                    return redirect("letters:letter", slug=letter.slug)
                cache.set(attempt_key, attempts + 1, 600)
                form.add_error("password", "That is not the right password. Try again, my love.")
        return render(
            request,
            "letters/letter_locked.html",
            {
                "letter": letter,
                "form": form,
                "theme": _theme_context(letter),
                "meta_description": "A private letter, protected by a secret word.",
            },
            status=403 if request.method == "POST" and form.errors else 200,
        )

    if not is_owner:
        _record_view(request, letter)
    letter.refresh_from_db(fields=["view_count"])

    theme = _theme_context(letter)
    share_url = absolute_url(request, letter.get_absolute_url())
    gallery_photos = list(letter.photos.all())
    return render(
        request,
        "letters/letter_detail.html",
        {
            "letter": letter,
            "theme": theme,
            "photos": gallery_photos,
            "share_url": share_url,
            "preview": False,
            "has_music": letter.has_music,
            "music_source": letter.music_source if letter.has_music else "",
            "meta_description": f"A love letter for {letter.recipient_name}.",
            "og_image": (
                absolute_url(request, gallery_photos[0].image.url) if gallery_photos else ""
            ),
        },
    )


@login_required
def preview_letter(request, slug):
    letter = get_object_or_404(
        LoveLetter.objects.select_related("theme", "music").prefetch_related("photos"),
        slug=slug,
        owner=request.user,
    )
    theme = _theme_context(letter)
    return render(
        request,
        "letters/letter_detail.html",
        {
            "letter": letter,
            "theme": theme,
            "photos": list(letter.photos.all()),
            "share_url": absolute_url(request, letter.get_absolute_url()),
            "preview": True,
            "has_music": letter.has_music,
            "music_source": letter.music_source if letter.has_music else "",
            "meta_description": "A private preview of a love letter.",
            "og_image": "",
        },
    )


def letter_qr(request, slug):
    """Generate a themed QR code PNG for a published letter."""
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    letter = get_object_or_404(LoveLetter, slug=slug)
    is_owner = request.user.is_authenticated and request.user == letter.owner
    if not letter.is_published and not is_owner:
        raise Http404

    target = absolute_url(request, letter.get_absolute_url())
    accent = (getattr(letter.theme, "accent_color", "#d94f79") or "#d94f79").lstrip("#")
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(target)
    qr.make(fit=True)
    image = qr.make_image(fill_color=f"#{accent}", back_color="#fffaf6").convert("RGB")
    buffer = __import__("io").BytesIO()
    image.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    response["Content-Disposition"] = f'inline; filename="love-letter-{letter.slug}.png"'
    return response


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
def health(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})


def custom_404(request, exception):
    return render(request, "404.html", status=404)


def custom_500(request):
    return render(request, "500.html", status=500)
