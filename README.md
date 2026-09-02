# ConvertNest

ConvertNest is a lightweight Flask web app for common online conversion tasks:

- PDF to JPG
- JPG/PNG/WEBP to PDF
- YouTube to MP3 for eligible public videos

## YouTube MP3

The YouTube tool is intentionally MP3-only. It uses yt-dlp for extraction and FFmpeg for MP3 conversion. Download only content you own or have permission to process, and follow YouTube's terms.

Some YouTube videos may still be unavailable to a server because of privacy, region, authentication, age, membership, anti-abuse, or other access restrictions. The app now fails those requests quickly instead of cycling through multiple clients.

## SEO pages

- `/pdf-to-jpg`
- `/jpg-to-pdf`
- `/pdf-maker`
- `/youtube-to-mp3`

The app also serves `/robots.txt` and `/sitemap.xml`.

## Environment variables

- `TURNSTILE_SITE_KEY` — public Cloudflare Turnstile site key.
- `TURNSTILE_SECRET_KEY` — private Turnstile secret.
- `SITE_URL` — optional fixed canonical domain.

Do not put the Turnstile secret in HTML or JavaScript.

## Deployment

The included `start_render.sh` works with Render. The included `Dockerfile` provides a portable container for hosts that support Docker.
