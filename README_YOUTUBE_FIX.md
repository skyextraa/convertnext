# ConvertNest YouTube setup

The previous build had two separate problems:

1. The PO-token provider was pinned to an older release and the extractor arguments were not passed in the structure yt-dlp expects.
2. The screenshot was from a **local Windows server (`127.0.0.1`)**, so Render's Node/provider setup was never being used during the failing test.

This build uses bgutil 1.3.2, current yt-dlp extractor arguments, and automatically starts the local provider when the provider files have been installed.

## Windows

1. Install **Node.js 22+** and Git for Windows.
2. Run `setup_windows.bat` once.
3. Start the app with `py app.py`.

The setup script installs Python dependencies, downloads bgutil 1.3.2, and compiles its provider.

## Render

`render.yaml` installs Node 22, FFmpeg, bgutil 1.3.2, and starts the HTTP PO-token provider before Gunicorn.

## What to look for in a verbose yt-dlp log

A working provider installation should report a bgutil PO-token provider rather than only saying that the GVS PO token is missing. The official provider documentation shows the expected provider registration in verbose output.

No downloader can guarantee every YouTube URL: private, members-only, region-restricted, age-restricted, authenticated, or otherwise unavailable videos may still fail.
