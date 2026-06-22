"""Local Whisper ASR via faster-whisper.

Returns word-ish Cues (segment granularity) with timestamps, ready to be merged with diarization.
Heavy import is lazy. Runs on CUDA when usable, else CPU.
"""

from __future__ import annotations

from typing import Optional

from ...hardware import resolve_device
from ...types import Cue
from ..base import ProgressFn, TranscriptionBackend, _noop

_SIZES = ["tiny", "base", "small", "medium", "large-v3"]


class FasterWhisperBackend(TranscriptionBackend):
    name = "faster-whisper-local"
    requires_api_key = False

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "model": {"type": "string", "enum": _SIZES, "default": "large-v3",
                          "title": "Whisper model"},
                "language": {"type": "string", "title": "Language (blank = auto-detect)"},
            },
        }

    def transcribe(
        self,
        audio_path: str,
        *,
        language: Optional[str] = None,
        model: Optional[str] = None,
        device: str = "auto",
        progress: ProgressFn = _noop,
        **options,
    ) -> list[Cue]:
        from faster_whisper import WhisperModel  # noqa: PLC0415

        dev = resolve_device(device)
        # faster-whisper uses CTranslate2: "cuda" or "cpu" (no MPS) — map accordingly.
        ct2_device = "cuda" if dev.kind == "cuda" and dev.usable else "cpu"
        compute_type = "float16" if ct2_device == "cuda" else "int8"

        progress(-1.0, f"loading whisper '{model or 'large-v3'}' on {ct2_device}")
        wm = WhisperModel(model or "large-v3", device=ct2_device, compute_type=compute_type)

        segments, info = wm.transcribe(audio_path, language=language or None, vad_filter=True)
        total = info.duration or 0.0
        cues: list[Cue] = []
        for seg in segments:  # generator — streams as it decodes
            text = (seg.text or "").strip()
            if text:
                cues.append(Cue(start=round(seg.start, 3), end=round(seg.end, 3), text=text))
            if total:
                progress(min(1.0, seg.end / total), f"transcribing… {seg.end:.0f}/{total:.0f}s")
        progress(1.0, f"transcription done: {len(cues)} cues")
        return cues
