"""Core data types shared across the pipeline and all backends.

Times are always floats in **seconds**. Keeping these tiny and dependency-free means backends,
the merge step, and the I/O layer all speak the same language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Segment:
    """A span of audio attributed to one speaker (output of a DiarizationBackend)."""

    start: float
    end: float
    speaker: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class Cue:
    """One transcript line. ``text`` may come from ASR or an imported VTT/SRT.

    ``speaker`` is filled in by the merge step. ``orig_speaker`` preserves any speaker label that
    was already on an imported transcript (e.g. the Teams ``<v Peter Kiss>`` tag).
    """

    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    orig_speaker: Optional[str] = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class SpeakerStat:
    """Aggregate stats for one speaker, used by the labeling UI."""

    speaker: str
    total_seconds: float = 0.0
    cue_count: int = 0
    first_start: Optional[float] = None
    samples: list[float] = field(default_factory=list)  # sample start times for click-to-play
