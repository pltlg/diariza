"""Golden test: re-merge the real diarize_bundle output and confirm the port reproduces it.

Uses the prototype's ``diarization.json`` (segments) + ``URS_transcript.vtt`` and checks that our
ported merge yields the same 6 speakers with the same dominant speaker (~108 min) we produced by
hand. Skips automatically if the bundle isn't on disk (e.g. CI).
"""

import json
import os
from pathlib import Path

import pytest

from diariza import vtt
from diariza.merge import assign_speakers, speaker_stats
from diariza.types import Segment


def _bundle_dir() -> Path | None:
    env = os.environ.get("DIARIZA_BUNDLE")
    candidates = [Path(env)] if env else []
    candidates.append(Path(__file__).resolve().parents[3] / "diarize_bundle")
    for c in candidates:
        if (c / "diarization.json").exists() and (c / "URS_transcript.vtt").exists():
            return c
    return None


def test_golden_matches_prototype():
    bundle = _bundle_dir()
    if bundle is None:
        pytest.skip("diarize_bundle not found (set DIARIZA_BUNDLE to enable)")

    segs = [
        Segment(s["start"], s["end"], s["speaker"])
        for s in json.loads((bundle / "diarization.json").read_text(encoding="utf-8"))
    ]
    cues = vtt.parse_transcript(bundle / "URS_transcript.vtt")
    assign_speakers(cues, segs)
    stats = speaker_stats(cues)

    speakers = {s.speaker for s in stats}
    assert len(speakers) == 6, f"expected 6 speakers, got {sorted(speakers)}"
    # Dominant speaker ~108 min in the original run.
    assert stats[0].total_seconds / 60 > 90
