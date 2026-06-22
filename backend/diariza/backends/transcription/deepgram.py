"""Deepgram cloud transcription (utterances → Cues)."""

from __future__ import annotations

from typing import Optional

from ...types import Cue
from ..base import ProgressFn, TranscriptionBackend, _noop
from .._deepgram import run, utterances


class DeepgramCloudTranscription(TranscriptionBackend):
    name = "deepgram-cloud"
    requires_api_key = True

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "language": {"type": "string", "title": "Language (optional)"},
                "model": {"type": "string", "default": "nova-2", "title": "Model"},
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
        progress(-1.0, "sending to Deepgram")
        result = run(audio_path, diarize=False, language=language, model=model)
        cues = [
            Cue(start=float(u["start"]), end=float(u["end"]), text=u.get("transcript", "").strip())
            for u in utterances(result)
        ]
        progress(1.0, f"transcription done: {len(cues)} cues")
        return cues
