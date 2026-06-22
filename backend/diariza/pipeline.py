"""End-to-end orchestration: ingest → (ASR | import) → diarize → merge → export.

This is the single entry point both the CLI and the FastAPI server call. Progress is reported as a
single 0..1 fraction across weighted stages so the UI shows one smooth bar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

from . import merge as merge_mod
from . import vtt
from .backends.base import ProgressFn, _noop
from .media import ensure_wav
from .registry import get_diarization_backend, get_transcription_backend
from .types import Cue, Segment

# Stage weights for the unified progress bar (sum = 1.0).
_W_INGEST, _W_TRANSCRIBE, _W_DIARIZE, _W_MERGE = 0.05, 0.45, 0.45, 0.05


@dataclass
class PipelineResult:
    cues: list[Cue]
    segments: list[Segment]
    speakers: list[dict] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)


def _staged(progress: ProgressFn, base: float, weight: float) -> ProgressFn:
    def inner(frac: float, msg: str) -> None:
        f = 0.0 if frac < 0 else frac  # indeterminate → hold at stage base
        progress(base + weight * f, msg)
    return inner


def run_pipeline(
    media_path: str,
    *,
    transcript_path: Optional[str] = None,
    diarization_backend: str = "pyannote-local",
    transcription_backend: str = "faster-whisper-local",
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    language: Optional[str] = None,
    asr_model: Optional[str] = None,
    device: str = "auto",
    names: Optional[Mapping[str, str]] = None,
    output_dir: str = "out",
    output_basename: Optional[str] = None,
    progress: ProgressFn = _noop,
) -> PipelineResult:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = output_basename or Path(media_path).stem

    # 1) Ingest → 16k mono wav (also gives Whisper/pyannote a uniform input).
    progress(0.0, "extracting audio")
    wav = ensure_wav(media_path, out)
    progress(_W_INGEST, "audio ready")

    # 2) Transcript: import existing (Mode B) or ASR from scratch (Mode A).
    if transcript_path:
        cues = vtt.parse_transcript(transcript_path)
        progress(_W_INGEST + _W_TRANSCRIBE, f"imported transcript: {len(cues)} cues")
    else:
        asr = get_transcription_backend(transcription_backend)
        cues = asr.transcribe(
            str(wav), language=language, model=asr_model, device=device,
            progress=_staged(progress, _W_INGEST, _W_TRANSCRIBE),
        )

    # 3) Diarize.
    diar = get_diarization_backend(diarization_backend)
    base = _W_INGEST + _W_TRANSCRIBE
    segments = diar.diarize(
        str(wav), num_speakers=num_speakers, min_speakers=min_speakers,
        max_speakers=max_speakers, device=device,
        progress=_staged(progress, base, _W_DIARIZE),
    )

    # 4) Merge speakers onto cues + stats.
    progress(base + _W_DIARIZE, "assigning speakers")
    merge_mod.assign_speakers(cues, segments, names=names)
    stats = merge_mod.speaker_stats(cues)

    # 5) Export.
    outputs = {
        "vtt": str(out / f"{stem}_diarized.vtt"),
        "srt": str(out / f"{stem}_diarized.srt"),
        "txt": str(out / f"{stem}_diarized.txt"),
        "json": str(out / f"{stem}_diarized.json"),
        "segments": str(out / f"{stem}_segments.json"),
    }
    vtt.write_vtt(cues, outputs["vtt"])
    vtt.write_srt(cues, outputs["srt"])
    vtt.write_txt(cues, outputs["txt"])
    vtt.write_json(cues, outputs["json"])
    Path(outputs["segments"]).write_text(
        json.dumps([s.__dict__ for s in segments], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress(1.0, "done")

    return PipelineResult(
        cues=cues,
        segments=segments,
        speakers=[
            {"speaker": s.speaker, "minutes": round(s.total_seconds / 60, 1),
             "cues": s.cue_count, "samples": s.samples}
            for s in stats
        ],
        outputs=outputs,
    )
