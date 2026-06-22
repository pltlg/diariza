"""Media ingest: extract a 16 kHz mono WAV from any audio/video using ffmpeg.

Mirrors the prototype's ``audio_16k_mono.wav`` convention (pyannote + Whisper both want 16 kHz mono).
ffmpeg is located from (1) the ``DIARIZA_FFMPEG`` env var, (2) a bundled binary under
``packaging/ffmpeg`` in the installer, or (3) ``ffmpeg`` on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"}


class FfmpegNotFound(RuntimeError):
    pass


def find_ffmpeg() -> str:
    env = os.environ.get("DIARIZA_FFMPEG")
    if env and Path(env).exists():
        return env
    exe = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    bundled = Path(__file__).resolve().parents[2] / "packaging" / "ffmpeg" / exe
    if bundled.exists():
        return str(bundled)
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise FfmpegNotFound(
        "ffmpeg not found. Set DIARIZA_FFMPEG, bundle it under packaging/ffmpeg, or add it to PATH."
    )


def extract_audio(src: str | Path, out_wav: str | Path, *, sample_rate: int = 16000) -> Path:
    """Extract/transcode ``src`` to a mono WAV at ``sample_rate``. Returns the output path."""
    src, out_wav = Path(src), Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y", "-i", str(src),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-acodec", "pcm_s16le", str(out_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr[-2000:]}")
    return out_wav


def ensure_wav(src: str | Path, work_dir: str | Path, *, sample_rate: int = 16000) -> Path:
    """Return a 16 kHz mono WAV for ``src``, transcoding unless it's already a usable WAV."""
    src = Path(src)
    out = Path(work_dir) / "audio_16k_mono.wav"
    return extract_audio(src, out, sample_rate=sample_rate)
