"""Seed themes, royalty-free music and a demo letter.

Usage:  python manage.py seed_love
Safe to run multiple times - existing records are updated, not duplicated.
"""

from __future__ import annotations

import math
import random
import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from letters.models import (
    BackgroundMusic,
    LetterPhoto,
    LetterTheme,
    LoveLetter,
    User,
)

THEMES = [
    {
        "name": "Blush & Gold",
        "slug": "blush-and-gold",
        "tagline": "Soft rose, warm light",
        "description": "Our signature theme: blush pink, cream and a whisper of gold.",
        "primary_color": "#e46b8f",
        "secondary_color": "#c69a5b",
        "accent_color": "#d94f79",
        "paper_color": "#fff8f3",
        "ink_color": "#4b2b3a",
        "background_css": "linear-gradient(160deg,#fde8ef 0%,#f7d3e3 45%,#e8d8ff 100%)",
        "heading_font": "'Cormorant Garamond', serif",
        "body_font": "'Cormorant Garamond', serif",
        "order": 1,
    },
    {
        "name": "Rose Garden",
        "slug": "rose-garden",
        "tagline": "Deep petals at dusk",
        "description": "Romantic rose tones for a love that feels like it has always existed.",
        "primary_color": "#c94f6d",
        "secondary_color": "#7d3b56",
        "accent_color": "#b23a5e",
        "paper_color": "#fff6f4",
        "ink_color": "#46222e",
        "background_css": "linear-gradient(150deg,#fbe4e8 0%,#f3c2cc 50%,#e8b4b4 100%)",
        "heading_font": "'Playfair Display', serif",
        "body_font": "'Cormorant Garamond', serif",
        "order": 2,
    },
    {
        "name": "Lavender Dusk",
        "slug": "lavender-dusk",
        "tagline": "Quiet, dreamy, tender",
        "description": "Lavender and lilac for slow evenings and softer words.",
        "primary_color": "#8d6bc9",
        "secondary_color": "#b98ad4",
        "accent_color": "#7b57b5",
        "paper_color": "#fbf7ff",
        "ink_color": "#3d2f53",
        "background_css": "linear-gradient(165deg,#efe6ff 0%,#e2d4f7 55%,#f7d8ea 100%)",
        "heading_font": "'Cormorant Garamond', serif",
        "body_font": "'Outfit', sans-serif",
        "order": 3,
    },
    {
        "name": "Midnight Romance",
        "slug": "midnight-romance",
        "tagline": "A love letter after dark",
        "description": "Midnight ink and starlight - dramatic, intimate, unforgettable.",
        "primary_color": "#e0a7c0",
        "secondary_color": "#8a7bd6",
        "accent_color": "#e8a2c0",
        "paper_color": "#221a2d",
        "ink_color": "#f6e9f1",
        "background_css": "radial-gradient(circle at 20% 15%, #3a2a52 0%, #191325 45%, #0f0b19 100%)",
        "heading_font": "'Great Vibes', cursive",
        "body_font": "'Cormorant Garamond', serif",
        "order": 4,
    },
    {
        "name": "Sunlit Cream",
        "slug": "sunlit-cream",
        "tagline": "Golden hour, held still",
        "description": "Warm cream, honey and amber for a timeless, classic letter.",
        "primary_color": "#c98a4b",
        "secondary_color": "#e0b07a",
        "accent_color": "#b66a3c",
        "paper_color": "#fffbf0",
        "ink_color": "#4a3524",
        "background_css": "linear-gradient(150deg,#fff7e6 0%,#f9e6c4 50%,#f3d0b0 100%)",
        "heading_font": "'Playfair Display', serif",
        "body_font": "'Cormorant Garamond', serif",
        "order": 5,
    },
    {
        "name": "Cherry Blossom",
        "slug": "cherry-blossom",
        "tagline": "Petals, promises, spring",
        "description": "Pale blossom pinks for brand-new love and fresh beginnings.",
        "primary_color": "#e58fa8",
        "secondary_color": "#f2b8c6",
        "accent_color": "#d36086",
        "paper_color": "#fffaf9",
        "ink_color": "#51303c",
        "background_css": "linear-gradient(160deg,#fff1f2 0%,#ffe0e7 45%,#ffd1df 100%)",
        "heading_font": "'Great Vibes', cursive",
        "body_font": "'Caveat', cursive",
        "order": 6,
    },
    {
        "name": "Ocean of Stars",
        "slug": "ocean-of-stars",
        "tagline": "Distance means nothing",
        "description": "Blue hour water and constellations for the one far away.",
        "primary_color": "#5b7fd4",
        "secondary_color": "#7bc3d9",
        "accent_color": "#4f6cc7",
        "paper_color": "#f6faff",
        "ink_color": "#253451",
        "background_css": "linear-gradient(160deg,#dfeaff 0%,#cfe9f2 55%,#e8e3ff 100%)",
        "heading_font": "'Cormorant Garamond', serif",
        "body_font": "'Outfit', sans-serif",
        "order": 7,
    },
    {
        "name": "Forever Red",
        "slug": "forever-red",
        "tagline": "Loud, brave, certain",
        "description": "A bold red declaration for the love you would choose again.",
        "primary_color": "#b3243c",
        "secondary_color": "#e0626f",
        "accent_color": "#a5162d",
        "paper_color": "#fff7f4",
        "ink_color": "#411620",
        "background_css": "linear-gradient(150deg,#fde5e1 0%,#f6c9c4 55%,#ffe9df 100%)",
        "heading_font": "'Playfair Display', serif",
        "body_font": "'Cormorant Garamond', serif",
        "order": 8,
    },
]

MUSIC = [
    ("Our Quiet Song", "To My Love Studio", "soft piano", "music/quiet-song.wav", "quiet-song.wav"),
    ("Moonlight Waltz", "To My Love Studio", "music box", "music/moonlight-waltz.wav", "moonlight-waltz.wav"),
    ("Rose Petal Lullaby", "To My Love Studio", "warm strings", "music/rose-petal-lullaby.wav", "rose-petal-lullaby.wav"),
]

DEMO_MESSAGE = """My dearest Isabel,

I have been trying to find a way to say this that does not sound too small.

So here it is: you are my favourite part of every ordinary day. The first message I look for in the morning. The story I save up to tell you at night. The reason I notice the colour of the sky.

I love the way you laugh a second before the joke lands. I love how you make a room feel warmer just by walking into it. I love that with you, silence is never empty - it is comfortable, like home.

There is a photograph of us on the kitchen wall, the one where you are mid-laugh and the light is doing something impossible. People think it is a good photo. It is not. It is just you.

If I could give you one thing, it would be the ability to see yourself the way I do - brave, luminous, endlessly kind. Until then, I will keep telling you, in a thousand small ways, for as long as you will let me.

Happy anniversary, my love. Here's to the years behind us, the ones ahead, and every quiet in-between.

All of me, always."""

DEMO_CAPTIONS = [
    "The afternoon we got caught in the rain and didn't run.",
    "Your favourite coffee shop, our favourite corner.",
    "The sky you said looked like a painting. You were right.",
]


class Command(BaseCommand):
    help = "Create the starter themes, music library and (optionally) a demo love letter."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-demo",
            action="store_true",
            help="Only seed themes and music. Recommended in production.",
        )
        parser.add_argument(
            "--with-demo",
            action="store_true",
            help="Create the demo account even when DEBUG is off (staging only).",
        )

    def handle(self, *args, **options):
        themes = {}
        for data in THEMES:
            payload = dict(data)
            slug = payload.pop("slug")
            theme, _ = LetterTheme.objects.update_or_create(
                slug=slug, defaults={**payload, "is_active": True}
            )
            themes[slug] = theme

        music_dir = Path(settings.MEDIA_ROOT) / "music"
        music_dir.mkdir(parents=True, exist_ok=True)
        static_dir = Path(settings.BASE_DIR) / "static" / "audio"

        tracks = []
        for title, artist, mood, media_path, filename in MUSIC:
            target = Path(settings.MEDIA_ROOT) / media_path
            target.parent.mkdir(parents=True, exist_ok=True)
            source = static_dir / filename
            if source.exists() and (not target.exists() or target.stat().st_size != source.stat().st_size):
                shutil.copyfile(source, target)
            track, _ = BackgroundMusic.objects.update_or_create(
                title=title,
                defaults={
                    "artist": artist,
                    "mood": mood,
                    "audio": media_path,
                    "is_active": True,
                    "order": len(tracks) + 1,
                },
            )
            tracks.append(track)
        self.stdout.write(f"[ok] {len(themes)} themes and {len(tracks)} music tracks ready")

        if options["no_demo"]:
            self.stdout.write("[ok] Demo content skipped (--no-demo).")
            return
        if not settings.DEBUG and not options["with_demo"]:
            self.stdout.write(
                self.style.WARNING(
                    "[skip] Demo account not created because DEBUG is off. "
                    "Pass --with-demo only on a staging environment."
                )
            )
            return

        self._seed_demo(themes, tracks)

    def _seed_demo(self, themes, tracks):
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@tomylove.local",
                "display_name": "Marco",
                "first_name": "Marco",
            },
        )
        if created:
            user.set_password("LoveLetter2026!")
            user.save()
            self.stdout.write("[ok] Demo account created: demo / LoveLetter2026!")
        else:
            user.set_password("LoveLetter2026!")
            user.save()
            self.stdout.write("[ok] Demo account ready: demo / LoveLetter2026!")

        demo, _ = LoveLetter.objects.get_or_create(
            owner=user,
            title="The Ordinary Days I Keep",
            defaults={
                "recipient_name": "Isabel",
                "sender_name": "Marco",
                "message": DEMO_MESSAGE,
                "closing_note": "You will always be special to me. Today, tomorrow, and every version of forever.",
                "occasion": LoveLetter.Occasion.ANNIVERSARY,
                "special_date": timezone.localdate() + timedelta(days=21),
                "theme": themes["blush-and-gold"],
                "music": tracks[0],
                "font_style": LoveLetter.FontStyle.HANDWRITTEN,
                "backdrop": LoveLetter.Backdrop.ROSE,
                "animation": LoveLetter.Animation.PETALS,
                "status": LoveLetter.Status.PUBLISHED,
                "is_public": True,
                "published_at": timezone.now(),
                "view_count": 37,
            },
        )
        if demo.status != LoveLetter.Status.PUBLISHED:
            demo.status = LoveLetter.Status.PUBLISHED
            demo.published_at = demo.published_at or timezone.now()
            demo.save()

        LoveLetter.objects.get_or_create(
            owner=user,
            title="A letter I'm still writing",
            defaults={
                "recipient_name": "Someone special",
                "sender_name": "Marco",
                "message": "Every time I try to write this, I end up smiling instead.\n\nI will finish it soon - I promise.",
                "theme": themes["lavender-dusk"],
                "music": tracks[1],
                "font_style": LoveLetter.FontStyle.ELEGANT,
                "backdrop": LoveLetter.Backdrop.LAVENDER,
                "animation": LoveLetter.Animation.SPARKLES,
                "status": LoveLetter.Status.DRAFT,
            },
        )

        locked, _ = LoveLetter.objects.get_or_create(
            owner=user,
            title="A secret just for you",
            defaults={
                "recipient_name": "My Quiet Love",
                "sender_name": "Marco",
                "message": (
                    "Some words are too tender for daylight. This one is for the quiet hours, "
                    "when the world is soft and you are the only thought I keep.\n\n"
                    "If you are reading this, you found the key. Welcome to the part of my heart "
                    "I keep locked."
                ),
                "closing_note": "Always, in every version of this life.",
                "occasion": LoveLetter.Occasion.SURPRISE,
                "theme": themes["midnight-romance"],
                "music": tracks[2],
                "font_style": LoveLetter.FontStyle.ROMANTIC,
                "backdrop": LoveLetter.Backdrop.MIDNIGHT,
                "animation": LoveLetter.Animation.STARS,
                "status": LoveLetter.Status.PUBLISHED,
                "is_public": False,
                "published_at": timezone.now(),
            },
        )
        if not locked.has_password:
            locked.set_access_password("forever")
            locked.save(update_fields=["access_password"])

        self._make_photos(demo)
        self.stdout.write(self.style.SUCCESS(f"[ok] Demo letter ready: /letter/{demo.slug}/"))
        self.stdout.write(
            self.style.SUCCESS(
                f"[ok] Locked sample ready: /letter/{locked.slug}/ (password: forever)"
            )
        )
        self.stdout.write(self.style.SUCCESS("All done. Start the server with: python manage.py runserver"))

    def _make_photos(self, letter):
        if letter.photos.exists():
            return
        try:
            from PIL import Image, ImageDraw, ImageFilter
        except ImportError:
            return

        random.seed(11)
        palette_sets = [
            ("#f7c8d8", "#ef9db5", "#7a4a68"),
            ("#f5dcc0", "#e8b98f", "#6d4b3b"),
            ("#d8cdf3", "#b8a6e6", "#4c3a6b"),
        ]
        folder = Path(settings.MEDIA_ROOT) / "letters" / "demo"
        folder.mkdir(parents=True, exist_ok=True)
        width, height = 1100, 1320

        for index, (start, end, ink) in enumerate(palette_sets):
            img = Image.new("RGB", (width, height), start)
            draw = ImageDraw.Draw(img, "RGBA")

            def blend(c1, c2, t):
                a = tuple(int(c1[i : i + 2], 16) for i in (1, 3, 5))
                b = tuple(int(c2[i : i + 2], 16) for i in (1, 3, 5))
                return tuple(round(a[j] + (b[j] - a[j]) * t) for j in range(3))

            for y in range(height):
                draw.line([(0, y), (width, y)], fill=blend(start, end, y / height))

            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            for _ in range(70):
                r = random.randint(18, 150)
                x = random.randint(-60, width + 60)
                y = random.randint(-60, height + 60)
                alpha = random.randint(10, 45)
                color = random.choice([(255, 255, 255), (255, 220, 230), (255, 245, 220)])
                odraw.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
            img = Image.alpha_composite(img.convert("RGBA"), overlay)

            heart = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            hdraw = ImageDraw.Draw(heart)
            cx, cy, size = width // 2, int(height * 0.62), 150
            points = []
            for step in range(120):
                t = 2 * math.pi * step / 120
                x = 16 * math.sin(t) ** 3
                y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
                points.append((cx + x * size / 17, cy - y * size / 17))
            hdraw.polygon(points, fill=(255, 255, 255, 26))
            hdraw.line(points + [points[0]], fill=(255, 255, 255, 90), width=3)
            img = Image.alpha_composite(img, heart.filter(ImageFilter.GaussianBlur(1.2)))

            grain = Image.effect_noise((width, height), 14).convert("L")
            img = Image.composite(
                img,
                Image.new("RGBA", img.size, (255, 255, 255, 255)),
                grain.point(lambda v: 240 + v // 16),
            )
            img = img.filter(ImageFilter.GaussianBlur(0.4)).convert("RGB")

            filename = f"demo-{index + 1}.jpg"
            path = folder / filename
            img.save(path, "JPEG", quality=88, optimize=True)

            photo = LetterPhoto(letter=letter, caption=DEMO_CAPTIONS[index], order=index)
            with open(path, "rb") as fh:
                photo.image.save(filename, File(fh), save=False)
            photo.save()
