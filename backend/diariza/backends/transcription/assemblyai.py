"""AssemblyAI cloud transcription (utterances/words → Cues)."""

from __future__ import annotations

from typing import Optional

from ...types import Cue
from ..base import ProgressFn, TranscriptionBackend, _noop
from .._assemblyai import run


class AssemblyAICloudTranscription(TranscriptionBackend):
    name = "assemblyai-cloud"
    requires_api_key = True

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"language": {"type": "string", "title": "Language code (optional)"}},
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
        progress(-1.0, "uploading to AssemblyAI")
        result = run(audio_path, speaker_labels=False, language=language,
                     on_tick=lambda s: progress(-1.0, f"AssemblyAI: {s}"))
        utterances = result.get("utterances")
        if utterances:
            cues = [Cue(start=u["start"] / 1000.0, end=u["end"] / 1000.0, text=u["text"].strip())
                    for u in utterances]
        else:
            words = result.get("words") or []
            cues = [Cue(start=w["start"] / 1000.0, end=w["end"] / 1000.0, text=w["text"])
                    for w in words]
        progress(1.0, f"transcription done: {len(cues)} cues")
        return cues
