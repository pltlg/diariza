"""Deepgram cloud diarization (diarize=true → Segments)."""

from __future__ import annotations

from typing import Optional

from ...types import Segment
from ..base import DiarizationBackend, ProgressFn, _noop
from ..cloud_util import speaker_label
from .._deepgram import run, utterances


class DeepgramCloudDiarization(DiarizationBackend):
    name = "deepgram-cloud"
    requires_api_key = True
    supports_num_speakers = False

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "language": {"type": "string", "title": "Language (optional)"},
                "model": {"type": "string", "default": "nova-2", "title": "Model"},
            },
        }

    def diarize(
        self,
        audio_path: str,
        *,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        device: str = "auto",
        progress: ProgressFn = _noop,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **options,
    ) -> list[Segment]:
        progress(-1.0, "sending to Deepgram")
        result = run(audio_path, diarize=True, language=language, model=model)
        segments = [
            Segment(start=float(u["start"]), end=float(u["end"]),
                    speaker=speaker_label(u.get("speaker", 0)))
            for u in utterances(result)
        ]
        progress(1.0, f"diarization done: {len(segments)} segments")
        return segments
