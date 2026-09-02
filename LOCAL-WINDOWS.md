# Local Windows startup

If a `.bat` window was closing immediately, the previous launcher was hiding the actual error. This build keeps the window open on every setup/startup failure.

1. Install Python 3.11+, Git for Windows, Node.js 22+, and FFmpeg.
2. Run `setup_windows.bat`.
3. If setup succeeds, run `start_windows.bat`.
4. If it still fails, run `diagnose_windows.bat` and send the final output/screenshot.

The app starts a local bgutil PO-token provider on `127.0.0.1:4416` and waits for its health endpoint before starting Flask. yt-dlp uses the provider plugin plus Node for YouTube challenge solving.


### FFmpeg
ConvertNest now installs `imageio-ffmpeg` with Python dependencies and passes its bundled FFmpeg executable directly to yt-dlp. You do not need to manually install FFmpeg or edit PATH for MP3 conversion.


## Important Windows fix
The setup script explicitly uses CALL for npm/npx because npm.cmd and npx.cmd are batch files on Windows. Without CALL, the parent setup script can terminate as soon as npm finishes.
