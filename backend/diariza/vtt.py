"""Transcript I/O: parse VTT/SRT into Cues and write labeled VTT / SRT / TXT / JSON.

Ported and generalized from the prototype ``merge_speakers.py`` (the ``<v Name>`` + timestamp regex
parsing and the grouped-TXT writer), extended with SRT support and a JSON sidecar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .types import Cue

# "HH:MM:SS.mmm" (VTT) or "HH:MM:SS,mmm" (SRT); hours optional.
_TIME = r"(?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{1,3}"
_RANGE_RE = re.compile(rf"({_TIME})\s*-->\s*({_TIME})")
_VTAG_RE = re.compile(r"<v\s+([^>]+)>(.*?)</v>", re.DOTALL)


def ts_to_sec(ts: str) -> float:
    """Parse a VTT/SRT timestamp ('HH:MM:SS.mmm', 'MM:SS.mmm', or ',' ms) into seconds."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        h, m, s = 0.0, 0.0, parts[0]
    return h * 3600 + m * 60 + s


def sec_to_vtt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def sec_to_srt(t: float) -> str:
    return sec_to_vtt(t).replace(".", ",")


def parse_transcript(path: str | Path) -> list[Cue]:
    """Parse a .vtt or .srt file into Cues, auto-detecting format from content."""
    raw = Path(path).read_text(encoding="utf-8-sig")
    return parse_transcript_text(raw)


def parse_transcript_text(raw: str) -> list[Cue]:
    cues: list[Cue] = []
    # Blocks separated by blank line(s); works for both VTT and SRT.
    for block in re.split(r"\n\s*\n", raw):
        m = _RANGE_RE.search(block)
        if not m:
            continue
        start, end = ts_to_sec(m.group(1)), ts_to_sec(m.group(2))
        after = block[m.end():].strip()
        vm = _VTAG_RE.search(after)
        if vm:
            orig = vm.group(1).strip()
            text = re.sub(r"\s+", " ", vm.group(2)).strip()
        else:
            orig = None
            # SRT/plain: text is everything after the timestamp line (may be multi-line).
            text = re.sub(r"\s+", " ", after).strip()
        if text or orig:
            cues.append(Cue(start=start, end=end, text=text, orig_speaker=orig))
    return cues


def _label(cue: Cue) -> str:
    return cue.speaker or cue.orig_speaker or "UNKNOWN"


def write_vtt(cues: Iterable[Cue], path: str | Path) -> None:
    lines = ["WEBVTT", ""]
    for i, c in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{sec_to_vtt(c.start)} --> {sec_to_vtt(c.end)}")
        lines.append(f"<v {_label(c)}>{c.text}</v>")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_srt(cues: Iterable[Cue], path: str | Path) -> None:
    lines = []
    for i, c in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{sec_to_srt(c.start)} --> {sec_to_srt(c.end)}")
        lines.append(f"{_label(c)}: {c.text}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_txt(cues: list[Cue], path: str | Path) -> None:
    """Readable transcript, merging consecutive cues from the same speaker (ported logic)."""
    out: list[str] = []
    cur: str | None = None
    buf: list[str] = []
    cur_start: float = 0.0
    for c in cues:
        lab = _label(c)
        if lab != cur:
            if cur is not None:
                out.append(f"[{sec_to_vtt(cur_start)}] {cur}:\n{' '.join(buf)}\n")
            cur, buf, cur_start = lab, [], c.start
        buf.append(c.text)
    if cur is not None:
        out.append(f"[{sec_to_vtt(cur_start)}] {cur}:\n{' '.join(buf)}\n")
    Path(path).write_text("\n".join(out), encoding="utf-8")


def write_json(cues: Iterable[Cue], path: str | Path) -> None:
    data = [
        {
            "start": round(c.start, 3),
            "end": round(c.end, 3),
            "speaker": _label(c),
            "text": c.text,
        }
        for c in cues
    ]
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
