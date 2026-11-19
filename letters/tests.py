"""Test suite for the To My Love letters app.

Run with:  python manage.py test
"""

import json
import shutil
import tempfile
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import BackgroundMusic, LetterPhoto, LetterTheme, LetterView, LoveLetter, User


def make_image(name="photo.jpg", size=(900, 700), color=(230, 120, 150), fmt="JPEG"):
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt)
    content_type = "image/png" if fmt == "PNG" else "image/jpeg"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class MediaTestCase(TestCase):
    """Base test case with an isolated MEDIA_ROOT."""

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp(prefix="tomylove-test-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)

    def setUp(self):
        cache.clear()


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class BaseDataTestCase(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="lover", password="Sup3rSecret!42", email="lover@example.com",
            display_name="Marco",
        )
        cls.other = User.objects.create_user(
            username="stranger", password="Sup3rSecret!42", email="other@example.com",
            display_name="Nina",
        )
        cls.theme = LetterTheme.objects.create(
            name="Blush and Gold", slug="blush-and-gold",
            primary_color="#e46b8f", secondary_color="#c69a5b",
            accent_color="#d94f79", paper_color="#fff8f3", ink_color="#4b2b3a",
        )

    def make_letter(self, owner=None, **kwargs):
        defaults = {
            "owner": owner or self.user,
            "theme": self.theme,
            "title": "The ordinary days I keep",
            "recipient_name": "Isabel",
            "sender_name": "Marco",
            "message": "There are a thousand little reasons why you matter to me.",
            "closing_note": "Always, in every version of this life.",
            "is_public": False,
        }
        defaults.update(kwargs)
        return LoveLetter.objects.create(**defaults)

    def publish(self, letter):
        letter.publish()
        return letter


class ModelTests(BaseDataTestCase):
    def test_slug_is_unique_and_unguessable(self):
        first = self.make_letter()
        second = self.make_letter()
        self.assertTrue(first.slug.startswith("to-my-love-"))
        self.assertEqual(len(first.slug.split("-")[-1]), 12)
        self.assertNotEqual(first.slug, second.slug)

    def test_publish_and_unpublish_timestamps(self):
        letter = self.make_letter()
        self.assertEqual(letter.status, LoveLetter.Status.DRAFT)
        self.assertIsNone(letter.published_at)

        letter.publish()
        letter.refresh_from_db()
        self.assertTrue(letter.is_published)
        self.assertIsNotNone(letter.published_at)

        published_at = letter.published_at
        letter.unpublish()
        letter.refresh_from_db()
        self.assertFalse(letter.is_published)
        self.assertEqual(letter.published_at, published_at)

    def test_password_is_hashed_and_verified(self):
        letter = self.make_letter()
        letter.set_access_password("forever")
        self.assertNotEqual(letter.access_password, "forever")
        self.assertTrue(letter.has_password)
        self.assertTrue(letter.check_access_password("forever"))
        self.assertFalse(letter.check_access_password("wrong"))

    def test_unlocked_letters_accept_any_password(self):
        letter = self.make_letter()
        self.assertFalse(letter.has_password)
        self.assertTrue(letter.check_access_password(""))

    def test_first_photo_and_music_source(self):
        letter = self.make_letter()
        self.assertIsNone(letter.first_photo)

        photo = LetterPhoto.objects.create(letter=letter, image=make_image(), order=0)
        self.assertEqual(letter.first_photo, photo)

        music = BackgroundMusic.objects.create(
            title="Quiet song", audio_url="https://example.com/song.mp3"
        )
        letter.music = music
        letter.save()
        self.assertTrue(letter.has_music)
        self.assertEqual(letter.music_source, "https://example.com/song.mp3")


class AuthTests(BaseDataTestCase):
    def test_signup_creates_user_and_redirects_to_editor(self):
        response = self.client.post(
            reverse("letters:signup"),
            {
                "username": "newlover",
                "display_name": "Ari",
                "email": "ari@example.com",
                "password1": "An0therSecret!42",
                "password2": "An0therSecret!42",
            },
        )
        self.assertRedirects(response, reverse("letters:editor_create"))
        user = User.objects.get(username="newlover")
        self.assertEqual(user.display_name, "Ari")
        self.assertEqual(user.email, "ari@example.com")

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("letters:signup"),
            {
                "username": "another",
                "email": "lover@example.com",
                "password1": "An0therSecret!42",
                "password2": "An0therSecret!42",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")

    def test_login_and_logout(self):
        response = self.client.post(
            reverse("letters:login"),
            {"username": "lover", "password": "Sup3rSecret!42"},
        )
        self.assertRedirects(response, reverse("letters:dashboard"))

        response = self.client.post(reverse("letters:logout"))
        self.assertRedirects(response, reverse("letters:home"))

    def test_login_throttles_repeated_failures(self):
        for _ in range(10):
            self.client.post(
                reverse("letters:login"),
                {"username": "lover", "password": "incorrect"},
            )
        response = self.client.post(
            reverse("letters:login"),
            {"username": "lover", "password": "Sup3rSecret!42"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many attempts")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("letters:dashboard"))
        self.assertRedirects(
            response, f"{reverse('letters:login')}?next={reverse('letters:dashboard')}"
        )


class DashboardTests(BaseDataTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_dashboard_only_lists_own_letters(self):
        own = self.make_letter(title="Mine")
        self.make_letter(owner=self.other, title="Theirs")
        response = self.client.get(reverse("letters:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own.title)
        self.assertNotContains(response, "Theirs")

    def test_dashboard_search_and_status_filter(self):
        draft = self.make_letter(title="A quiet draft", status=LoveLetter.Status.DRAFT)
        published = self.make_letter(
            title="A loud confession", status=LoveLetter.Status.PUBLISHED
        )
        response = self.client.get(reverse("letters:dashboard"), {"q": "quiet"})
        self.assertContains(response, draft.title)
        self.assertNotContains(response, published.title)

        response = self.client.get(reverse("letters:dashboard"), {"status": "published"})
        self.assertContains(response, published.title)
        self.assertNotContains(response, draft.title)

    def test_stats_are_scoped_to_owner(self):
        self.make_letter(status=LoveLetter.Status.PUBLISHED)
        self.make_letter(owner=self.other, status=LoveLetter.Status.PUBLISHED)
        response = self.client.get(reverse("letters:dashboard"))
        self.assertEqual(response.context["stats"]["total"], 1)
        self.assertEqual(response.context["stats"]["published"], 1)


class EditorTests(BaseDataTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def form_data(self, **overrides):
        data = {
            "title": "A letter for you",
            "recipient_name": "Isabel",
            "sender_name": "Marco",
            "message": "Every ordinary day with you is a day I want to keep.",
            "closing_note": "Always yours.",
            "occasion": LoveLetter.Occasion.JUST_BECAUSE,
            "special_date": "",
            "theme": self.theme.pk,
            "font_style": LoveLetter.FontStyle.HANDWRITTEN,
            "backdrop": LoveLetter.Backdrop.THEME,
            "animation": LoveLetter.Animation.HEARTS,
            "music": "",
            "music_url": "",
            "action": "draft",
        }
        data.update(overrides)
        return data

    def test_create_draft(self):
        response = self.client.post(reverse("letters:editor_create"), self.form_data())
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertEqual(letter.status, LoveLetter.Status.DRAFT)
        self.assertRedirects(
            response, reverse("letters:editor_update", kwargs={"slug": letter.slug})
        )

    def test_create_and_publish_letter(self):
        response = self.client.post(
            reverse("letters:editor_create"), self.form_data(action="publish")
        )
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertTrue(letter.is_published)
        self.assertIsNotNone(letter.published_at)
        self.assertRedirects(
            response,
            reverse("letters:editor_update", kwargs={"slug": letter.slug})
            + "?published=1",
        )

    def test_short_message_is_rejected(self):
        response = self.client.post(
            reverse("letters:editor_create"), self.form_data(message="too short")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A few more words")
        self.assertFalse(LoveLetter.objects.exists())

    def test_password_is_saved_hashed(self):
        self.client.post(
            reverse("letters:editor_create"),
            self.form_data(password="forever", password_confirm="forever"),
        )
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertTrue(letter.has_password)
        self.assertNotEqual(letter.access_password, "forever")
        self.assertTrue(letter.check_access_password("forever"))

    def test_password_confirmation_must_match(self):
        response = self.client.post(
            reverse("letters:editor_create"),
            self.form_data(password="forever", password_confirm="never"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two passwords do not match.")
        self.assertFalse(LoveLetter.objects.exists())

    def test_publish_action_sets_live_status(self):
        letter = self.make_letter()
        response = self.client.post(
            reverse("letters:publish", kwargs={"slug": letter.slug})
        )
        letter.refresh_from_db()
        self.assertTrue(letter.is_published)
        self.assertRedirects(
            response,
            reverse("letters:editor_update", kwargs={"slug": letter.slug})
            + "?published=1",
        )

    def test_unpublish_returns_letter_to_drafts(self):
        letter = self.publish(self.make_letter())
        self.client.post(reverse("letters:unpublish", kwargs={"slug": letter.slug}))
        letter.refresh_from_db()
        self.assertFalse(letter.is_published)

    def test_edit_and_delete_are_owner_only(self):
        letter = self.make_letter()
        url = reverse("letters:editor_update", kwargs={"slug": letter.slug})

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.post(reverse("letters:delete", kwargs={"slug": letter.slug})).status_code,
            404,
        )
        self.assertTrue(LoveLetter.objects.filter(pk=letter.pk).exists())

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(
            reverse("letters:delete", kwargs={"slug": letter.slug})
        )
        self.assertRedirects(response, reverse("letters:dashboard"))
        self.assertFalse(LoveLetter.objects.filter(pk=letter.pk).exists())

    def test_duplicate_letter_copies_content_and_photos(self):
        letter = self.publish(self.make_letter(is_public=True))
        LetterPhoto.objects.create(letter=letter, image=make_image(), order=0)

        self.client.post(reverse("letters:duplicate", kwargs={"slug": letter.slug}))
        copy = LoveLetter.objects.exclude(pk=letter.pk).get(owner=self.user)
        self.assertEqual(copy.title, letter.title + " (copy)")
        self.assertEqual(copy.status, LoveLetter.Status.DRAFT)
        self.assertFalse(copy.is_public)
        self.assertEqual(copy.photos.count(), 1)
        self.assertEqual(copy.view_count, 0)

    def test_upload_photos(self):
        response = self.client.post(
            reverse("letters:editor_create"),
            self.form_data(photos=[make_image("one.jpg"), make_image("two.png", fmt="PNG")]),
        )
        self.assertEqual(response.status_code, 302)
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertEqual(letter.photos.count(), 2)
        self.assertEqual(list(letter.photos.values_list("order", flat=True)), [0, 1])
        for photo in letter.photos.all():
            self.assertTrue(photo.image.storage.exists(photo.image.name))

    def test_rejects_unsafe_photo_extension(self):
        bad = SimpleUploadedFile("payload.txt", b"<script>alert(1)</script>", content_type="text/plain")
        response = self.client.post(
            reverse("letters:editor_create"), self.form_data(photos=[bad])
        )
        self.assertEqual(response.status_code, 302)
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertEqual(letter.photos.count(), 0)

    @override_settings(MAX_PHOTO_SIZE=512)
    def test_rejects_oversized_photo(self):
        response = self.client.post(
            reverse("letters:editor_create"),
            self.form_data(photos=[make_image(size=(1200, 1200))]),
        )
        self.assertEqual(response.status_code, 302)
        letter = LoveLetter.objects.get(owner=self.user)
        self.assertEqual(letter.photos.count(), 0)

    def test_reorder_photos(self):
        letter = self.make_letter()
        photos = [
            LetterPhoto.objects.create(letter=letter, image=make_image(f"{i}.jpg"), order=i)
            for i in range(3)
        ]
        order = [photos[2].pk, photos[0].pk, photos[1].pk]
        response = self.client.post(
            reverse("letters:photo_reorder", kwargs={"slug": letter.slug}),
            data=json.dumps({"order": order}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(letter.photos.values_list("pk", flat=True)), order
        )

    def test_reorder_rejects_incomplete_order(self):
        letter = self.make_letter()
        photo = LetterPhoto.objects.create(letter=letter, image=make_image(), order=0)
        response = self.client.post(
            reverse("letters:photo_reorder", kwargs={"slug": letter.slug}),
            data=json.dumps({"order": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        photo.refresh_from_db()
        self.assertEqual(photo.order, 0)

    def test_delete_photo_ajax(self):
        letter = self.make_letter()
        photo = LetterPhoto.objects.create(letter=letter, image=make_image(), order=0)
        response = self.client.post(
            reverse(
                "letters:photo_delete",
                kwargs={"slug": letter.slug, "photo_id": photo.pk},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"ok": True})
        self.assertFalse(LetterPhoto.objects.filter(pk=photo.pk).exists())


class PublicLetterTests(BaseDataTestCase):
    def test_published_letter_is_public(self):
        letter = self.publish(self.make_letter())
        response = self.client.get(letter.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "letters/letter_detail.html")
        self.assertContains(response, letter.title)
        self.assertContains(response, letter.recipient_name)

    def test_draft_is_hidden_from_visitors_but_visible_to_owner(self):
        letter = self.make_letter()
        url = letter.get_absolute_url()

        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "letters/letter_unavailable.html")

    def test_view_count_is_deduplicated_per_session(self):
        letter = self.publish(self.make_letter())

        self.client.get(letter.get_absolute_url())
        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 1)
        self.assertEqual(LetterView.objects.filter(letter=letter).count(), 1)

        self.client.get(letter.get_absolute_url())
        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 1)

        other_visitor = Client()
        other_visitor.get(letter.get_absolute_url())
        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 2)
        self.assertEqual(LetterView.objects.filter(letter=letter).count(), 2)
        self.assertIsNotNone(letter.last_opened_at)

    def test_owner_views_are_not_counted(self):
        letter = self.publish(self.make_letter())
        self.client.force_login(self.user)
        self.client.get(letter.get_absolute_url())
        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 0)

    def test_ip_is_hashed_not_stored_raw(self):
        letter = self.publish(self.make_letter())
        self.client.get(letter.get_absolute_url(), REMOTE_ADDR="203.0.113.9")
        view = LetterView.objects.get(letter=letter)
        self.assertNotIn("203.0.113.9", view.ip_hash)
        self.assertEqual(len(view.ip_hash), 64)

    def test_password_locked_letter(self):
        letter = self.publish(self.make_letter())
        letter.set_access_password("forever")
        letter.save()
        url = letter.get_absolute_url()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "letters/letter_locked.html")

        response = self.client.post(url, {"password": "wrong"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "not the right password", status_code=403)

        response = self.client.post(url, {"password": "forever"})
        self.assertRedirects(response, url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "letters/letter_detail.html")

        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 1)

    def test_password_attempts_are_throttled(self):
        letter = self.publish(self.make_letter())
        letter.set_access_password("forever")
        letter.save()
        url = letter.get_absolute_url()

        for _ in range(8):
            self.client.post(url, {"password": "nope"})
        response = self.client.post(url, {"password": "forever"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Too many attempts", status_code=403)
        letter.refresh_from_db()
        self.assertEqual(letter.view_count, 0)

    def test_qr_code_png(self):
        letter = self.publish(self.make_letter())
        response = self.client.get(reverse("letters:qr", kwargs={"slug": letter.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(
            response["Content-Disposition"],
            f'inline; filename="love-letter-{letter.slug}.png"',
        )

    def test_qr_code_hides_drafts_from_visitors(self):
        letter = self.make_letter()
        url = reverse("letters:qr", kwargs={"slug": letter.slug})
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_owner_preview_works_for_drafts(self):
        letter = self.make_letter(title="Still a draft")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("letters:preview", kwargs={"slug": letter.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "letters/letter_detail.html")
        self.assertContains(response, "Preview mode")


class DiscoveryTests(BaseDataTestCase):
    def test_explore_lists_only_public_published_letters(self):
        public = self.publish(self.make_letter(title="A public promise", is_public=True))
        self.publish(self.make_letter(title="A private promise", is_public=False))
        self.make_letter(title="An unfinished promise", is_public=True)

        response = self.client.get(reverse("letters:explore"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, public.title)
        self.assertNotContains(response, "A private promise")
        self.assertNotContains(response, "An unfinished promise")

    def test_explore_search(self):
        match = self.publish(
            self.make_letter(title="Letters for Ana", recipient_name="Ana", is_public=True)
        )
        other = self.publish(
            self.make_letter(title="Letters for Bea", recipient_name="Bea", is_public=True)
        )
        response = self.client.get(reverse("letters:explore"), {"q": "Ana"})
        self.assertContains(response, match.title)
        self.assertNotContains(response, other.title)

    def test_home_featured_letters_are_public_only(self):
        public = self.publish(self.make_letter(title="A public letter", is_public=True))
        self.publish(self.make_letter(title="A hidden letter", is_public=False))
        response = self.client.get(reverse("letters:home"))
        self.assertContains(response, public.title)
        self.assertNotContains(response, "A hidden letter")

    def test_health_endpoint(self):
        response = self.client.get(reverse("letters:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_unknown_letter_returns_404(self):
        response = self.client.get("/letter/to-my-love-doesnotexist/")
        self.assertEqual(response.status_code, 404)
