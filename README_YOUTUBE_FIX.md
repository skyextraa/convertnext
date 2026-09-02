# YouTube MP3 reliability notes

The production app is intentionally MP3-only. It uses one yt-dlp extraction attempt and a short server timeout instead of cycling through multiple YouTube clients. This reduces duplicate requests, latency, and worker pressure.

A cloud server can still receive a YouTube anti-bot, authentication, privacy, region, age, or membership restriction. Those cases are reported as a normal 400 error instead of leaving a Gunicorn worker stuck.
