# To My Love

A Django platform for writing, publishing and opening personalized multimedia love letters. Creators shape a letter in a four-step editor, publish it to an unguessable share URL, and send their person into a small cinematic experience: an animated envelope, falling petals or hearts, a typewritten message, photos, music, a countdown and a closing note.

The design is deliberately warm and editorial rather than "SaaS dashboard": cream paper, blush gradients, glass panels, script typography, and motion that stays out of the way of the words.

---

## Features

**For the sender**
- Four-step creator: words, look, photos & music, sharing
- Live letter preview that updates as you type
- Eight themes, six typography styles, six backdrops, five particle effects
- Photo gallery uploads (JPEG/PNG/WEBP/GIF), reordering, deletion and captions
- Background music library, uploaded audio, or a direct audio URL
- Optional secret password, public gallery opt-in, special-date countdown
- Drafts, publish/unpublish, duplicate, edit and delete
- Dashboard stats, search and status filters
- Copy link, themed QR code PNG, and owner-only full previews

**For the recipient**
- Envelope opening animation with GSAP (with reduced-motion and no-JS fallbacks)
- Typewriter message with a "read it all at once" control
- Floating hearts, rose petals, sparkles or stars
- Polaroid photo gallery with keyboard-accessible lightbox
- Ambient audio with a persistent play/pause dock
- Password-protected letter screen with throttled attempts
- Mobile-first layout from 320 px upward

**Under the hood**
- Custom user model and Django authentication
- Hashed letter passwords, session-based unlocks
- Re-encoded uploads (EXIF/GPS stripped, images resized to 1920 px)
- Session-deduplicated view counts and hashed visitor IPs
- CSRF protection, upload validation, owner-scoped querysets
- SQLite by default; PostgreSQL or MySQL through `DATABASE_URL`
- WhiteNoise static files, security headers when `DEBUG=False`
- 43 automated tests

---

## Quick start (local)

Requirements: Python 3.12+ (tested on 3.14), pip.

```bash
git clone https://github.com/jm008ahfa/loveee.git loveee
cd loveee

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux

python manage.py migrate
python manage.py seed_love
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

`seed_love` is idempotent. It creates the eight themes, three ambient tracks and (while `DEBUG=True`) a demo account and public demo letter, then prints the letter URL. In production use `python manage.py seed_love --no-demo`; the command refuses to create the known-password demo account when `DEBUG=False` unless you explicitly pass `--with-demo` on a staging environment.

Demo account (shown on the login page only while `DEBUG=True`):

```
username: demo
password: LoveLetter2026!
```

The dashboard also contains a password-protected sample letter; its secret word is `forever`. In production, `seed_love` skips all demo content unless you pass `--with-demo` on a staging environment.

Useful commands:

```bash
python manage.py test                 # full suite
python manage.py check                # framework checks
python manage.py createsuperuser      # /admin/ access
python manage.py collectstatic        # production static build
python scripts/generate_music.py      # regenerate the ambient WAVs
python scripts/screenshots.py         # Playwright visual smoke test (optional)
```

---

## Project layout

```
config/                 Django project settings, URLs, WSGI/ASGI
letters/
  models.py             User, LetterTheme, BackgroundMusic, LoveLetter,
                        LetterPhoto, LetterView
  views.py              Landing, explore, auth, dashboard, editor,
                        public letter, password unlock, QR, health
  forms.py              Signup/login, letter editor, search, password
  validators.py         Upload size validation
  utils.py              Slug generation, IP hashing, image optimisation
  tests.py              43 tests across models, auth, editor, sharing, security
  management/commands/
    seed_love.py        Themes, music, demo account and demo letter
templates/
  base.html             Marketing/auth/dashboard shell
  letters/
    base_letter.html    Immersive recipient shell
    letter_detail.html  Envelope, letter, countdown, gallery, closing
    letter_locked.html  Password screen
    letter_unavailable.html
    editor.html         Four-step creator + live preview
    dashboard.html      Letter cards, filters, QR modal
    home.html, explore.html, auth/
  404.html, 500.html
static/
  css/main.css          Design system, marketing, dashboard, editor
  css/letter.css        Recipient experience
  js/main.js            Navigation, reveals, copy, QR modal, hero canvas
  js/editor.js          Steps, live preview, photo upload/reorder
  js/letter.js          GSAP envelope, typewriter, particles, gallery, audio
  audio/                Generated ambient tracks
media/                  User uploads (not committed in production)
scripts/                Music generation and screenshot harness
```

---

## Configuration

All settings are environment-driven. See `.env.example` for the full list.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | dev key | **Must** be set in production |
| `DJANGO_DEBUG` | `True` | Turns on dev media serving and verbose errors |
| `DJANGO_ALLOWED_HOSTS` | localhost, 127.0.0.1 | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | e.g. `https://letters.example.com` |
| `SITE_URL` | empty | Public origin used for QR codes and share links |
| `SITE_NAME` | `To My Love` | Brand name in metadata/footer |
| `DATABASE_URL` | empty (SQLite) | `postgres://…` or `mysql://…` |
| `DB_SSL` | `False` | Require SSL for PostgreSQL |
| `REDIS_URL` | empty | Shared cache for throttling across workers |
| `DJANGO_TIME_ZONE` | `UTC` | Display timezone |
| `EMAIL_*` | console backend | SMTP delivery settings |

### PostgreSQL

```bash
pip install "psycopg[binary]"
# .env
DATABASE_URL=postgres://tomylove:secret@localhost:5432/tomylove
```

### MySQL / MariaDB

```bash
sudo apt install libmysqlclient-dev   # Debian/Ubuntu
pip install mysqlclient
# .env
DATABASE_URL=mysql://tomylove:secret@localhost:3306/tomylove
```

Run `python manage.py migrate` after changing databases. For any deployment with more than one worker, configure `REDIS_URL` so login/password throttling is shared rather than per-process.

---

## Production deployment

The repository includes a `Dockerfile`, `docker-compose.yml` and `Procfile`.

### Docker Compose

1. Edit the passwords and hostnames in `docker-compose.yml`.
2. Set a real `DJANGO_SECRET_KEY`.
3. If you serve over HTTPS, remove `DJANGO_SECURE_SSL_REDIRECT: "False"` and set `SITE_URL`/`DJANGO_CSRF_TRUSTED_ORIGINS` to your domain.
4. Run:

```bash
docker compose up --build -d
docker compose exec web python manage.py seed_love --no-demo
```

The container migrates on start, collects static files at build time, and serves the app with Gunicorn. Uploaded media lives in the `media_data` volume; PostgreSQL data lives in `postgres_data`.

### Manual Gunicorn + Nginx

```bash
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key as k; print(k())')"
export DJANGO_ALLOWED_HOSTS=letters.example.com
export DJANGO_CSRF_TRUSTED_ORIGINS=https://letters.example.com
export SITE_URL=https://letters.example.com
export DATABASE_URL=postgres://user:pass@host:5432/tomylove

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_love --no-demo

gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 --workers 3 --timeout 60
```

Nginx should proxy `/` to Gunicorn and serve `/media/` directly from the persistent media directory:

```nginx
server {
    listen 443 ssl;
    server_name letters.example.com;

    client_max_body_size 30M;

    location /static/ { alias /srv/tomylove/staticfiles/; }
    location /media/  { alias /srv/tomylove/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Media persistence:** `media/` contains user photos and uploaded music. It must survive deploys. Back it up with the database, or point `STORAGES["default"]` at S3-compatible object storage.

**Static files:** WhiteNoise serves the collected files; `collectstatic` runs automatically in the Docker image. In manual deployments, rerun it after every deploy.

---

## Security notes

- Set a strong `DJANGO_SECRET_KEY`; it salts session and IP hashing.
- With `DEBUG=False`, the app enables HTTPS redirect, HSTS, secure cookies, `nosniff`, and `X-Frame-Options: DENY`.
- Share slugs contain a 12-character random token (`to-my-love-<token>`), so links are not enumerable.
- Letter passwords are hashed with Django's password hasher; unlocks are stored server-side in the session.
- Login attempts (10 / 5 min per IP) and letter unlock attempts (8 / 10 min per IP) are throttled through the cache.
- Uploads are checked by extension, size, and Pillow's image parser. Non-animated images are re-encoded to strip metadata; animated GIFs are passed through.
- Drafts are only visible to their owner; QR codes and previews enforce the same ownership rules.
- View counts are deduplicated per session for 30 minutes. Raw IPs are never stored, only salted SHA-256 hashes.

For a public deployment, also consider:
- A shared Redis cache (throttling is otherwise per worker).
- Object storage/CDN for media.
- A Web Application Firewall or reverse-proxy rate limit.
- Regular `pg_dump` + media backups.

---

## Customisation

- **Themes:** edit or add rows in `LetterTheme` via `/admin/`, or extend `THEMES` in `letters/management/commands/seed_love.py`.
- **Fonts:** update `_FONT_STACKS` in `letters/utils.py` and the Google Fonts link in the base templates.
- **Music:** drop files into the library via `/admin/`, or upload per letter. `scripts/generate_music.py` synthesises the bundled royalty-free tracks.
- **Limits:** `MAX_PHOTO_SIZE`, `MAX_MUSIC_SIZE`, `MAX_PHOTOS_PER_LETTER` live in `config/settings.py`.
- **Copy:** all user-facing text is in `templates/`; the visual system is in `static/css/main.css` and `static/css/letter.css`.

---

## Tests and QA

```bash
python manage.py test
python manage.py check
python manage.py check --deploy   # with DJANGO_DEBUG=False
```

The suite covers slug uniqueness, publishing, password hashing and throttling, view deduplication, owner-only editing/deleting, photo validation/reordering, QR generation, search/explore visibility, and the draft/preview rules.

For a visual pass, start the server and run `python scripts/screenshots.py`; screenshots are written to `%TEMP%\loveee_shots` on Windows. The harness uses JavaScript clicks for the envelope because headless Chrome's locator stability checks can stall on continuously animated pages.

---

## License

The application code is provided for personal and commercial use. The bundled ambient audio is synthesised locally and carries no third-party licence obligations. Photos created by `seed_love` are synthetic placeholders.
