# ConvertNest

ConvertNest is a lightweight Flask web app for common online conversion tasks:

- PDF to JPG
- JPG/PNG/WEBP to PDF
- Eligible public YouTube video to MP3

## SEO implementation

The site includes dedicated, useful landing pages for each supported conversion rather than generating thin keyword pages:

- `/pdf-to-jpg`
- `/jpg-to-pdf`
- - `/youtube-to-mp3`

Each page has a unique title, meta description, canonical URL, Open Graph/Twitter metadata, semantic headings, internal links, FAQ content, BreadcrumbList, WebSite, SoftwareApplication and FAQ structured data where appropriate.

The app also serves:

- `/robots.txt`
- `/sitemap.xml`

The canonical host is derived from the current request host. If a fixed canonical domain is required, set `SITE_URL` in the environment.

## Search strategy

Do not create hundreds of near-identical pages solely to target keywords. Build genuinely useful tool pages, add original instructions and FAQs, earn relevant links, and monitor indexing and queries in Google Search Console.

## Render

The YouTube stack requires FFmpeg, Node 22, yt-dlp with its default dependencies, and the bgutil PO-token provider. The project includes a Dockerfile and start script suitable for a container host. The YouTube feature is MP3-only.

After connecting the custom domain, verify the canonical URLs and sitemap in Google Search Console.

## YouTube extraction reliability

The current build uses Node 22 for yt-dlp EJS challenges and bgutil-ytdlp-pot-provider 1.3.2 for video-bound PO tokens. The primary client is `mweb`, matching current yt-dlp guidance; `web_safari` and `web_embedded` are used as fallbacks. The Render start command waits for the provider health endpoint before starting Gunicorn.


## Cloudflare Turnstile

YouTube download endpoints require Cloudflare Turnstile verification. Create a Turnstile widget in Cloudflare, allow your deployed hostname and any custom domain, then add these environment variables:

- `TURNSTILE_SITE_KEY` — public sitekey used by the browser.
- `TURNSTILE_SECRET_KEY` — private secret used by Flask for server-side Siteverify validation.

The secret must never be placed in HTML or JavaScript. Turnstile is an anti-abuse layer; it does not override YouTube access restrictions.
