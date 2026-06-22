"""Local pyannote.audio diarization backend — port of the prototype ``diarize.py``.

Loads ``pyannote/speaker-diarization-3.1`` (gated; needs an accepted HF token), runs it on the
resolved device, and returns Segments. Heavy imports are lazy so the engine/tests load without
torch installed.
"""

from __future__ import annotations

import os
from typing import Optional

from ...hardware import resolve_device, torch_device_str
from ...types import Segment
from ..base import DiarizationBackend, ProgressFn, _noop

_MODEL = "pyannote/speaker-diarization-3.1"


def _hf_token() -> Optional[str]:
    for var in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    return None


class _ProgressHook:
    """Map pyannote's hook callbacks to a 0..1 progress fraction."""

    def __init__(self, progress: ProgressFn):
        self._progress = progress

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __call__(self, step_name, step_artifact=None, *, file=None, total=None, completed=None):
        if total:
            frac = min(1.0, (completed or 0) / total)
            self._progress(frac, f"diarization: {step_name}")
        else:
            self._progress(-1.0, f"diarization: {step_name}")  # indeterminate


class PyannoteLocalBackend(DiarizationBackend):
    name = "pyannote-local"
    requires_api_key = False  # uses an HF token (env/settings), not a per-call API key
    supports_num_speakers = True

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "num_speakers": {"type": "integer", "minimum": 1, "title": "Exact speakers"},
                "min_speakers": {"type": "integer", "minimum": 1, "title": "Min speakers"},
                "max_speakers": {"type": "integer", "minimum": 1, "title": "Max speakers"},
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
        **options,
    ) -> list[Segment]:
        import soundfile as sf  # noqa: PLC0415
        import torch  # noqa: PLC0415
        from pyannote.audio import Pipeline  # noqa: PLC0415

        token = _hf_token()
        if not token:
            raise RuntimeError(
                "No Hugging Face token. Set HF_TOKEN (or add it in Settings) and accept the gated "
                "models at hf.co/pyannote/speaker-diarization-3.1 and segmentation-3.0."
            )

        progress(-1.0, "loading pyannote pipeline")
        pipeline = Pipeline.from_pretrained(_MODEL, use_auth_token=token)
        if pipeline is None:
            raise RuntimeError(
                "pyannote returned no pipeline — the HF token likely hasn't accepted the gated "
                "model conditions (speaker-diarization-3.1 and segmentation-3.0)."
            )

        dev = resolve_device(device)
        if not dev.usable:
            raise RuntimeError(f"Requested GPU is not usable: {dev.name} ({dev.detail}).")
        pipeline.to(torch.device(torch_device_str(dev)))
        progress(-1.0, f"loading audio on {dev.name}")

        data, sr = sf.read(audio_path, dtype="float32", always_2d=True)
        waveform = torch.from_numpy(data.T.copy())
        audio_in = {"waveform": waveform, "sample_rate": sr}

        kwargs: dict = {}
        if num_speakers:
            kwargs["num_speakers"] = num_speakers
        if min_speakers:
            kwargs["min_speakers"] = min_speakers
        if max_speakers:
            kwargs["max_speakers"] = max_speakers

        with _ProgressHook(progress) as hook:
            diarization = pipeline(audio_in, hook=hook, **kwargs)

        segments = [
            Segment(start=round(turn.start, 3), end=round(turn.end, 3), speaker=spk)
            for turn, _, spk in diarization.itertracks(yield_label=True)
        ]
        progress(1.0, f"diarization done: {len(segments)} segments")
        return segments
