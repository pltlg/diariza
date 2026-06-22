from diariza.merge import assign_speakers, speaker_stats
from diariza.types import Cue, Segment


def test_overlap_assignment_picks_max_overlap():
    segments = [
        Segment(0.0, 5.0, "SPEAKER_00"),
        Segment(5.0, 10.0, "SPEAKER_01"),
    ]
    cues = [
        Cue(0.5, 1.5, "a"),      # fully inside SPEAKER_00
        Cue(4.0, 6.0, "b"),      # 1s in 00, 1s in 01 → tie broken deterministically
        Cue(7.0, 9.0, "c"),      # fully inside SPEAKER_01
    ]
    assign_speakers(cues, segments)
    assert cues[0].speaker == "SPEAKER_00"
    assert cues[2].speaker == "SPEAKER_01"


def test_nearest_gap_fallback_when_no_overlap():
    segments = [Segment(0.0, 1.0, "SPEAKER_00"), Segment(100.0, 101.0, "SPEAKER_01")]
    cue = Cue(2.0, 3.0, "x")  # overlaps nothing; nearest is SPEAKER_00
    assign_speakers([cue], segments)
    assert cue.speaker == "SPEAKER_00"


def test_names_mapping_applied():
    segments = [Segment(0.0, 10.0, "SPEAKER_02")]
    cue = Cue(1.0, 2.0, "hi")
    assign_speakers([cue], segments, names={"SPEAKER_02": "Peter Kiss"})
    assert cue.speaker == "Peter Kiss"


def test_speaker_stats_sorted_by_time():
    cues = [
        Cue(0.0, 10.0, "a", speaker="A"),
        Cue(10.0, 13.0, "b", speaker="B"),
        Cue(13.0, 18.0, "c", speaker="A"),
    ]
    stats = speaker_stats(cues)
    assert stats[0].speaker == "A"
    assert abs(stats[0].total_seconds - 15.0) < 1e-6
    assert stats[0].cue_count == 2
