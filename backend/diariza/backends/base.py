"""Backend interfaces — the heart of the 'interchangeable model' requirement.

A backend is just a class implementing one of these ABCs and registered via a
``diariza.diarization_backends`` / ``diariza.transcription_backends`` entry point (see
pyproject.toml and ``registry.py``). The UI reads ``config_schema()`` to render each backend's
options dynamically, so adding a new model never touches the core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from ..types import Cue, Segment

# progress(fraction in 0..1, human-readable message). Wired to the WebSocket in the server.
ProgressFn = Callable[[float, str], None]


def _noop(fraction: float, message: str) -> None:  # default progress sink
    pass


class DiarizationBackend(ABC):
    name: str = "base"
    requires_api_key: bool = False
    supports_num_speakers: bool = True

    def config_schema(self) -> dict:
        """JSON-schema describing this backend's options; the UI renders a form from it."""
        return {"type": "object", "properties": {}}

    @abstractmethod
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
        ...


class TranscriptionBackend(ABC):
    name: str = "base"
    requires_api_key: bool = False

    def config_schema(self) -> dict:
        return {"type": "object", "properties": {}}

    @abstractmethod
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
        ...
