import os
import re
import shutil
import tempfile
import uuid
import zipfile
import json
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from pathlib import Path

from flask import Flask, render_template, request, send_file, jsonify, Response, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import fitz  # PyMuPDF
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

def verify_turnstile():
    """Validate the Cloudflare Turnstile token for protected actions.

    The secret key is server-only and must be supplied through the
    TURNSTILE_SECRET_KEY environment variable. A missing secret intentionally
    fails closed so YouTube endpoints are never exposed without verification.
    """
    secret = (os.environ.get("TURNSTILE_SECRET_KEY") or os.environ.get("TURNSTILE_SECRET") or "").strip()
    token = request.form.get("cf-turnstile-response", "").strip()

    if not secret:
        return False, "Turnstile is not configured on this server. Add TURNSTILE_SECRET_KEY in your hosting environment."
    if not token:
        return False, "Please complete the human verification before downloading."

    payload = urlencode({
        "secret": secret,
        "response": token,
        "remoteip": request.headers.get("CF-Connecting-IP") or request.remote_addr or "",
    }).encode("utf-8")

    try:
        req = UrlRequest(
            TURNSTILE_SITEVERIFY_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False, "Human verification could not be checked. Please refresh and try again."

    if result.get("success") is not True:
        return False, "Human verification failed or expired. Please verify again."

    return True, ""

BASE = Path(tempfile.gettempdir()) / "convertnest"
BASE.mkdir(exist_ok=True)

ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp"}
YOUTUBE_RE = re.compile(
    r"^https?://(?:(?:www|m)\.)?(?:youtube\.com|youtu\.be)/",
    re.I,
)


def cleanup(path):
    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists():
            p.unlink(missing_ok=True)
    except Exception:
        pass


def safe_media_name(info, fallback="youtube-media"):
    title = secure_filename((info.get("title") or fallback).strip())
    return (title or fallback)[:120]


def _ffmpeg_path():
    """Return a self-contained FFmpeg executable installed by imageio-ffmpeg.

    This removes the requirement for users to manually install FFmpeg or add it
    to Windows PATH. It also works on Render/Linux when the wheel is available.
    """
    configured = os.environ.get("FFMPEG_LOCATION", "").strip()
    if configured:
        return configured
    return imageio_ffmpeg.get_ffmpeg_exe()


def youtube_common_options():
    """Small, predictable yt-dlp configuration for the MP3-only service.

    Keep one extraction attempt instead of cycling through several YouTube
    clients. Repeated client fallbacks made blocked requests slow and caused
    unnecessary server load. yt-dlp handles the normal YouTube extraction and
    Node is available for its JavaScript challenge support.
    """
    return {
        "quiet": True,
        "no_warnings": False,
        "noplaylist": True,
        "restrictfilenames": True,
        "retries": 2,
        "fragment_retries": 2,
        "concurrent_fragment_downloads": 1,
        "socket_timeout": 20,
        "http_chunk_size": 10 * 1024 * 1024,
        "js_runtimes": {"node": {}},
        "ffmpeg_location": _ffmpeg_path(),
    }


def youtube_error_message(exc):
    message = str(exc).lower()
    if "requested format is not available" in message:
        return "YouTube did not expose that exact quality to this server. Try Best available; if it still fails, the video may be restricted or YouTube may not expose a downloadable stream to this connection."
    if "sign in" in message or "age-restricted" in message or "confirm you're not a bot" in message:
        return "YouTube requires access this server does not have for this video. Try a different public video."
    if "private" in message:
        return "This video is private and cannot be downloaded here."
    if "members-only" in message:
        return "Members-only videos cannot be downloaded here."
    if "geo" in message or "country" in message or "region" in message:
        return "This video is region-restricted and is not available to this server."
    if "po token" in message or "proof of origin" in message or "403" in message or "forbidden" in message:
        return "YouTube rejected the media stream (HTTP 403). Try another eligible public video. If many different videos fail, YouTube may be restricting automated access from this server."
    if "javascript runtime" in message or "ejs" in message:
        return "YouTube's JavaScript challenge could not be solved. The server needs Node.js and a current yt-dlp EJS setup."
    return "YouTube rejected the download. Try a public video or another quality."



SITE_NAME = "ConvertNest"

def current_site_url():
    configured = os.environ.get("SITE_URL", "").strip().rstrip("/")
    return configured or request.host_url.rstrip("/")


@app.context_processor
def inject_site_context():
    return {
        "site_url": current_site_url(),
        "site_name": SITE_NAME,
        "turnstile_site_key": os.environ.get("TURNSTILE_SITE_KEY", "").strip(),
    }


def breadcrumb_schema(name, path):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ConvertNest", "item": current_site_url() + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": current_site_url() + path},
        ],
    }


def tool_schema(seo, path):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": current_site_url() + "/#website",
                "url": current_site_url() + "/",
                "name": SITE_NAME,
                "description": "Online PDF, image and YouTube MP3 conversion tools.",
            },
            {
                "@type": "SoftwareApplication",
                "name": seo["h1"],
                "url": current_site_url() + path,
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "description": seo["description"],
            },
            breadcrumb_schema(seo["h1"], path),
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                    for item in seo["faq"]
                ],
            },
        ],
    }


SEO_PAGES = {
    "pdf-jpg": {
        "path": "/pdf-to-jpg",
        "title": "PDF to JPG Converter Online — Free | ConvertNest",
        "description": "Convert PDF pages to JPG images online for free. Upload a PDF and download your pages as high-quality JPG files in one ZIP.",
        "h1": "PDF to JPG Converter Online",
        "intro": "Convert PDF pages into JPG images directly in your browser. Upload one PDF and download the converted pages as a ZIP file.",
        "section_title": "Convert PDF to JPG without installing software",
        "paragraphs": [
            "ConvertNest's PDF to JPG converter is built for a common task: turning document pages into image files that are easy to preview, share, or upload elsewhere. It supports PDFs up to 100 pages and returns the converted JPG pages together in a ZIP download.",
            "The conversion happens on the server for processing and the temporary job folder is removed after the download response closes. No account is required to use the converter.",
        ],
        "steps": ["Choose a PDF from your device or drag it into the upload box.", "Select Convert PDF to JPG and wait while the pages are rendered.", "Download the ZIP containing the JPG images."],
        "faq": [
            {"q": "Is the PDF to JPG converter free?", "a": "Yes. ConvertNest provides the PDF to JPG tool without requiring an account. Service limits may apply."},
            {"q": "How many PDF pages can I convert?", "a": "The current tool accepts PDFs with up to 100 pages."},
            {"q": "What do I download after conversion?", "a": "You receive a ZIP file containing one JPG image for each PDF page."},
        ],
    },
    "jpg-pdf": {
        "path": "/jpg-to-pdf",
        "title": "JPG to PDF Converter Online — Free | ConvertNest",
        "description": "Combine JPG, PNG and WEBP images into one PDF online for free. Upload up to 30 images and download a single PDF.",
        "h1": "JPG to PDF Converter Online",
        "intro": "Combine JPG, PNG, or WEBP images into one PDF document. Arrange your files before uploading and get a single downloadable PDF.",
        "section_title": "Turn images into one PDF online",
        "paragraphs": [
            "ConvertNest's JPG to PDF converter combines multiple images into a single PDF, which is useful for scanned documents, receipts, forms, photos, and image-based pages. The current limit is 30 images per PDF.",
            "The tool converts supported images to RGB and builds a standard PDF without requiring desktop software or an account.",
        ],
        "steps": ["Select or drag your JPG, PNG, or WEBP images into the upload box.", "Arrange the selected files in the order you want them converted.", "Choose Convert Images to PDF and download the finished PDF."],
        "faq": [
            {"q": "Can I combine multiple JPG images into one PDF?", "a": "Yes. You can upload up to 30 supported images and combine them into one PDF."},
            {"q": "Does it support PNG and WEBP?", "a": "Yes. JPG, JPEG, PNG, and WEBP images are supported."},
            {"q": "Do I need an account?", "a": "No account is required for the converter."},
        ],
    },
    "pdf-maker": {
        "path": "/pdf-maker",
        "title": "PDF Maker Online — Create PDF from Images Free | ConvertNest",
        "description": "Create a PDF online from JPG, PNG, or WEBP images. Arrange your images and combine them into one PDF for free with ConvertNest.",
        "h1": "PDF Maker Online",
        "intro": "Create a PDF from multiple JPG, PNG, or WEBP images. Upload your pages and download them as one PDF document.",
        "section_title": "Create a PDF from images online",
        "paragraphs": [
            "ConvertNest PDF Maker combines multiple image files into a single PDF. It is useful for scanned pages, receipts, forms, notes, screenshots, and photo documents.",
            "The current PDF Maker accepts up to 30 JPG, PNG, or WEBP images per job. No account is required."
        ],
        "steps": [
            "Choose or drag your JPG, PNG, or WEBP images into the upload area.",
            "Arrange the images in the order you want them to appear in the PDF.",
            "Click Create PDF and download the finished document."
        ],
        "faq": [
            {"q": "Is the PDF Maker free?", "a": "Yes. ConvertNest provides the PDF Maker without requiring an account. Service limits may apply."},
            {"q": "What image formats can I use?", "a": "You can use JPG, JPEG, PNG, and WEBP images."},
            {"q": "How many images can I combine?", "a": "The current PDF Maker accepts up to 30 images per PDF."}
        ],
    },
    "youtube-mp3": {
        "path": "/youtube-to-mp3",
        "title": "YouTube to MP3 Converter — Free | ConvertNest",
        "description": "Convert eligible public YouTube video audio to MP3 online. Paste a URL and download a 192 kbps MP3 when you have permission to do so.",
        "h1": "YouTube to MP3 Converter",
        "intro": "Extract audio from an eligible public YouTube video and download it as an MP3 file. Use the tool only for content you own or have permission to process.",
        "section_title": "Convert eligible YouTube videos to MP3",
        "paragraphs": [
            "ConvertNest's YouTube to MP3 converter extracts the best available audio stream and uses FFmpeg to create an MP3 at 192 kbps. It is intended for eligible public videos where downloading or conversion is permitted.",
            "Some YouTube videos cannot be processed because they are private, restricted, unavailable in the server's region, members-only, or require access the service does not have.",
        ],
        "steps": ["Copy the URL of an eligible YouTube video.", "Paste the URL into the converter.", "Choose Download MP3 and wait for the audio file to be prepared."],
        "faq": [
            {"q": "Can ConvertNest convert YouTube to MP3?", "a": "Yes, for eligible public videos that the service can access and that you have permission to download or convert."},
            {"q": "What MP3 quality does it use?", "a": "The current MP3 tool uses 192 kbps output."},
            {"q": "Why might a YouTube to MP3 conversion fail?", "a": "The source may be private, restricted, unavailable to the server, or expose media formats that cannot be accessed."},
        ],
    },
}


@app.get("/")
def index():
    home_schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": current_site_url() + "/#website", "url": current_site_url() + "/", "name": SITE_NAME, "description": "Online PDF, image and YouTube MP3 conversion tools."},
            {"@type": "Organization", "name": SITE_NAME, "url": current_site_url() + "/", "logo": current_site_url() + url_for("static", filename="convert-nest-mark.png")},
        ],
    }
    return render_template(
    "index.html",
    home_schema=home_schema,
    turnstile_site_key=os.environ.get("TURNSTILE_SITE_KEY", "").strip()
)


def render_tool_page(kind):
    seo = SEO_PAGES[kind]
    return render_template("tool_page.html", kind=kind, seo=seo, schema=tool_schema(seo, seo["path"]))


@app.get("/pdf-to-jpg")
def pdf_to_jpg_page():
    return render_tool_page("pdf-jpg")


@app.get("/jpg-to-pdf")
def jpg_to_pdf_page():
    return render_tool_page("jpg-pdf")


@app.get("/pdf-maker")
def pdf_maker_page():
    return render_tool_page("pdf-maker")


@app.get("/youtube-to-mp3")
def youtube_to_mp3_page():
    return render_tool_page("youtube-mp3")


@app.get("/robots.txt")
def robots_txt():
    return Response(
        "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /health\n\nSitemap: " + current_site_url() + "/sitemap.xml\n",
        mimetype="text/plain",
    )


@app.get("/sitemap.xml")
def sitemap_xml():
    urls = ["/", *(item["path"] for item in SEO_PAGES.values())]
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in urls:
        body.append(f"<url><loc>{current_site_url()}{path}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


@app.post("/api/pdf-to-jpg")
def pdf_to_jpg():
    upload = request.files.get("file")
    if not upload or not upload.filename.lower().endswith(".pdf"):
        return jsonify(error="Please upload a PDF file."), 400

    job = BASE / uuid.uuid4().hex
    job.mkdir()
    pdf_path = job / secure_filename(upload.filename)
    upload.save(pdf_path)

    try:
        doc = fitz.open(pdf_path)
        if len(doc) > 100:
            doc.close()
            cleanup(job)
            return jsonify(error="PDF limit is 100 pages."), 400

        output_dir = job / "jpg"
        output_dir.mkdir()
        jpg_paths = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            out = output_dir / f"page-{i+1}.jpg"
            pix.save(out, jpg_quality=90)
            jpg_paths.append(out)
        doc.close()

        zip_path = job / "pdf-pages-jpg.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in jpg_paths:
                z.write(p, p.name)

        response = send_file(zip_path, as_attachment=True, download_name="pdf-pages-jpg.zip")
        response.call_on_close(lambda: cleanup(job))
        return response
    except Exception as e:
        cleanup(job)
        return jsonify(error=f"Could not convert PDF: {e}"), 500


@app.post("/api/jpg-to-pdf")
def jpg_to_pdf():
    files = request.files.getlist("files")
    valid = []
    for f in files:
        ext = Path(f.filename).suffix.lower().lstrip(".")
        if f.filename and ext in ALLOWED_IMAGES:
            valid.append(f)

    if not valid:
        return jsonify(error="Upload one or more JPG, PNG, or WEBP images."), 400
    if len(valid) > 30:
        return jsonify(error="Maximum 30 images per PDF."), 400

    job = BASE / uuid.uuid4().hex
    job.mkdir()

    try:
        images = []
        for i, f in enumerate(valid):
            path = job / f"image-{i+1}{Path(f.filename).suffix.lower()}"
            f.save(path)
            with Image.open(path) as im:
                images.append(im.convert("RGB").copy())

        pdf_path = job / "images.pdf"
        images[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=images[1:])
        for im in images:
            im.close()

        response = send_file(pdf_path, as_attachment=True, download_name="images.pdf")
        response.call_on_close(lambda: cleanup(job))
        return response
    except Exception as e:
        cleanup(job)
        return jsonify(error=f"Could not create PDF: {e}"), 500


@app.post("/api/youtube/mp3")
def youtube_mp3():
    """Download eligible public YouTube audio as an MP3."""
    verified, verification_error = verify_turnstile()
    if not verified:
        return jsonify(error=verification_error), 403

    url = request.form.get("url", "").strip()
    if not YOUTUBE_RE.match(url):
        return jsonify(error="Enter a valid YouTube URL."), 400

    job = BASE / uuid.uuid4().hex
    job.mkdir()

    opts = youtube_common_options()
    opts.update({
        "outtmpl": str(job / "%(title).120s.%(ext)s"),
        "format": "ba/b[acodec!=none]",
        "max_filesize": 512 * 1024 * 1024,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        base = safe_media_name(info, "youtube-audio")
        media = next((p for p in job.iterdir() if p.is_file() and p.suffix.lower() == ".mp3"), None)
        if media is None or not media.exists():
            raise RuntimeError("No MP3 file was produced.")

        response = send_file(
            media,
            as_attachment=True,
            download_name=f"{base}.mp3",
            mimetype="audio/mpeg",
        )
        response.call_on_close(lambda: cleanup(job))
        return response
    except yt_dlp.utils.DownloadError as e:
        cleanup(job)
        return jsonify(error=youtube_error_message(e)), 400
    except Exception:
        cleanup(job)
        return jsonify(error="MP3 conversion failed. The video may be unavailable, restricted, or temporarily inaccessible."), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is too large. Maximum upload size is 50 MB."), 413


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
