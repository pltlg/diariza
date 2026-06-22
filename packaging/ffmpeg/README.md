# ffmpeg binaries

Drop the platform ffmpeg binary here before building an installer; it is bundled into the app and
located by `diariza/media.py` / `src/main/sidecar.ts` at runtime.

- Windows: `ffmpeg.exe`
- macOS / Linux: `ffmpeg`

Binaries are git-ignored (see root `.gitignore`) — do not commit them. CI downloads them during the
release build. For local dev, having `ffmpeg` on your PATH is enough; this folder is only for
producing self-contained installers.
