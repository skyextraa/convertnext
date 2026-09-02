# ConvertNest — Turnstile setup

This build keeps the Cloudflare Turnstile site key out of the source code and reads it from Render environment variables.

## Render environment variables

Add BOTH variables to the ConvertNest web service:

- `TURNSTILE_SITE_KEY` = your Cloudflare Turnstile Site Key
- `TURNSTILE_SECRET_KEY` = your Cloudflare Turnstile Secret Key

Do not put the secret key in HTML, JavaScript, GitHub, or `render.yaml` as a literal value.

## Cloudflare Turnstile widget

In Cloudflare Turnstile, make sure the widget's allowed hostnames include the exact hostname where ConvertNest is running, for example:

`convertnext-1.onrender.com`

If you later use a custom domain, add that hostname too.

## Deploy

1. Replace the project files with this ZIP.
2. Commit and push the changed files to GitHub.
3. In Render, confirm both Turnstile environment variables exist.
4. Trigger a new deploy.
5. Open the live site in a private/incognito window.
6. The Turnstile widget should appear inside the YouTube downloader card.
7. Complete verification, then click Download.

The Flask backend verifies `cf-turnstile-response` with Cloudflare before the YouTube info/download endpoints run. If either the site key or secret is missing, YouTube actions fail closed instead of silently bypassing verification.
