"""AssemblyAI cloud diarization (speaker_labels → Segments)."""

from __future__ import annotations

from typing import Optional

from ...types import Segment
from ..base import DiarizationBackend, ProgressFn, _noop
from ..cloud_util import speaker_label
from .._assemblyai import run


class AssemblyAICloudDiarization(DiarizationBackend):
    name = "assemblyai-cloud"
    requires_api_key = True
    supports_num_speakers = False  # AssemblyAI infers speaker count

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"language": {"type": "string", "title": "Language code (optional)"}},
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
        **options,
    ) -> list[Segment]:
        progress(-1.0, "uploading to AssemblyAI")
        result = run(audio_path, speaker_labels=True, language=language,
                     on_tick=lambda s: progress(-1.0, f"AssemblyAI: {s}"))
        segments = [
            Segment(start=u["start"] / 1000.0, end=u["end"] / 1000.0,
                    speaker=speaker_label(u["speaker"]))
            for u in result.get("utterances") or []
        ]
        progress(1.0, f"diarization done: {len(segments)} segments")
        return segments
