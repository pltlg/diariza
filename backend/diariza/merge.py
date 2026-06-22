"""Assign diarization speakers onto transcript cues by timestamp overlap.

Direct port of ``assign_speaker`` from the prototype ``merge_speakers.py``: each cue gets the
speaker whose segments overlap it most; if nothing overlaps, the nearest segment by gap wins.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Optional, Sequence

from .types import Cue, Segment, SpeakerStat

_MAX_SAMPLES = 8


def _assign_one(cs: float, ce: float, segments: Sequence[Segment]) -> tuple[str, float]:
    overlap: dict[str, float] = defaultdict(float)
    for seg in segments:
        o = min(ce, seg.end) - max(cs, seg.start)
        if o > 0:
            overlap[seg.speaker] += o
    if not overlap:
        best, best_gap = None, float("inf")
        for seg in segments:
            gap = max(cs - seg.end, seg.start - ce, 0.0)
            if gap < best_gap:
                best_gap, best = gap, seg.speaker
        return (best or "UNKNOWN"), 0.0
    spk = max(overlap, key=overlap.__getitem__)
    return spk, overlap[spk]


def assign_speakers(
    cues: list[Cue],
    segments: Sequence[Segment],
    names: Optional[Mapping[str, str]] = None,
) -> list[Cue]:
    """Set ``cue.speaker`` for every cue (in place) and return the list.

    ``names`` optionally remaps raw labels (e.g. ``{"SPEAKER_02": "Peter Kiss"}``).
    """
    names = names or {}
    for c in cues:
        raw, _ = _assign_one(c.start, c.end, segments)
        c.speaker = names.get(raw, raw)
    return cues


def speaker_stats(cues: Sequence[Cue]) -> list[SpeakerStat]:
    """Per-speaker speaking time, cue counts and a few sample timestamps, sorted by time desc."""
    stats: dict[str, SpeakerStat] = {}
    for c in cues:
        spk = c.speaker or c.orig_speaker or "UNKNOWN"
        st = stats.setdefault(spk, SpeakerStat(speaker=spk))
        st.total_seconds += c.duration
        st.cue_count += 1
        if st.first_start is None or c.start < st.first_start:
            st.first_start = c.start
        if len(st.samples) < _MAX_SAMPLES:
            st.samples.append(c.start)
    return sorted(stats.values(), key=lambda s: s.total_seconds, reverse=True)
