"""Local NVIDIA NeMo diarization backend.

NeMo's neural diarizer (MSDD) is a heavyweight optional dependency (``nemo_toolkit[asr]``). This
backend imports it lazily and surfaces a clear install hint if it's absent, so it always *appears*
in the backend list (the UI can show it as unavailable) without forcing the dependency on everyone.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Optional

from ...hardware import resolve_device
from ...types import Segment
from ..base import DiarizationBackend, ProgressFn, _noop


class NeMoLocalBackend(DiarizationBackend):
    name = "nemo-local"
    requires_api_key = False
    supports_num_speakers = True

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "num_speakers": {"type": "integer", "minimum": 1, "title": "Exact speakers"},
                "domain": {"type": "string", "enum": ["telephonic", "meeting", "general"],
                           "default": "meeting", "title": "Acoustic domain"},
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
        domain: str = "meeting",
        **options,
    ) -> list[Segment]:
        try:
            from nemo.collections.asr.models import NeuralDiarizer  # noqa: PLC0415
        except Exception as e:  # pragma: no cover - optional heavy dep
            raise RuntimeError(
                "NeMo is not installed. Install with `pip install nemo_toolkit[asr]` to use the "
                f"nemo-local backend. ({e})"
            )

        dev = resolve_device(device)
        progress(-1.0, f"loading NeMo neural diarizer on {dev.name}")
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "input.json"
            entry = {
                "audio_filepath": audio_path, "offset": 0, "duration": None,
                "label": "infer", "text": "-",
                "num_speakers": num_speakers, "rttm_filepath": None, "uem_filepath": None,
            }
            manifest.write_text(json.dumps(entry) + "\n", encoding="utf-8")

            diarizer = NeuralDiarizer.from_pretrained("diar_msdd_telephonic")
            diarizer.to(dev.kind)
            progress(-1.0, "running NeMo diarization")
            annotation = diarizer(audio_path, num_speakers=num_speakers)

        segments = [
            Segment(start=round(turn.start, 3), end=round(turn.end, 3), speaker=str(spk))
            for turn, _, spk in annotation.itertracks(yield_label=True)
        ]
        progress(1.0, f"diarization done: {len(segments)} segments")
        return segments
