from diariza import vtt
from diariza.types import Cue


def test_parse_vtt_with_speaker_tags():
    raw = (
        "WEBVTT\n\n"
        "id-1\n00:00:24.578 --> 00:00:26.818\n<v Peter Kiss>Most várjál jó.</v>\n\n"
        "id-2\n00:00:28.668 --> 00:00:34.264\n<v Peter Kiss>Akkor jó.</v>\n"
    )
    cues = vtt.parse_transcript_text(raw)
    assert len(cues) == 2
    assert cues[0].orig_speaker == "Peter Kiss"
    assert cues[0].text == "Most várjál jó."
    assert abs(cues[0].start - 24.578) < 1e-6
    assert abs(cues[1].end - 34.264) < 1e-6


def test_parse_srt_comma_ms():
    raw = "1\n00:00:01,000 --> 00:00:02,500\nHello there\n\n2\n00:00:03,000 --> 00:00:04,000\nBye\n"
    cues = vtt.parse_transcript_text(raw)
    assert [c.text for c in cues] == ["Hello there", "Bye"]
    assert abs(cues[0].end - 2.5) < 1e-6


def test_ts_roundtrip():
    for t in (0.0, 24.578, 3661.5):
        assert abs(vtt.ts_to_sec(vtt.sec_to_vtt(t)) - t) < 1e-3


def test_write_outputs(tmp_path):
    cues = [
        Cue(0.0, 2.0, "hello", speaker="SPEAKER_00"),
        Cue(2.0, 4.0, "world", speaker="SPEAKER_00"),
        Cue(4.0, 6.0, "bye", speaker="SPEAKER_01"),
    ]
    vtt.write_vtt(cues, tmp_path / "o.vtt")
    vtt.write_srt(cues, tmp_path / "o.srt")
    vtt.write_txt(cues, tmp_path / "o.txt")
    vtt.write_json(cues, tmp_path / "o.json")

    # VTT round-trips back to the same cues/speakers.
    back = vtt.parse_transcript(tmp_path / "o.vtt")
    assert [c.orig_speaker for c in back] == ["SPEAKER_00", "SPEAKER_00", "SPEAKER_01"]

    # TXT groups consecutive same-speaker cues into one block.
    txt = (tmp_path / "o.txt").read_text(encoding="utf-8")
    assert txt.count("SPEAKER_00:") == 1
    assert "hello world" in txt
    assert txt.count("SPEAKER_01:") == 1
