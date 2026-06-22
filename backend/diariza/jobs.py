"""In-process job manager: runs the (blocking) pipeline on a worker thread and streams progress.

A job runs the pipeline in a background thread; its progress callback hands events back to the
asyncio loop via ``call_soon_threadsafe`` so the WebSocket endpoint can stream them. Cancellation is
cooperative — we set a flag and the pipeline checks it between stages (mid-model cancel isn't
possible with pyannote/whisper).
"""

from __future__ import annotations

import asyncio
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .merge import assign_speakers, speaker_stats
from .pipeline import PipelineResult, run_pipeline
from . import vtt


class JobCancelled(Exception):
    pass


@dataclass
class Job:
    id: str
    params: dict
    status: str = "queued"          # queued | running | done | error | cancelled
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    result: Optional[PipelineResult] = None
    _cancel: threading.Event = field(default_factory=threading.Event)
    _queue: "asyncio.Queue[dict]" = field(default_factory=asyncio.Queue)
    _loop: Optional[asyncio.AbstractEventLoop] = None

    def public(self) -> dict:
        d = {
            "id": self.id,
            "status": self.status,
            "progress": round(self.progress, 4),
            "message": self.message,
            "error": self.error,
        }
        if self.result is not None:
            d["speakers"] = self.result.speakers
            d["outputs"] = self.result.outputs
        return d


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def create(self, params: dict, loop: asyncio.AbstractEventLoop) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], params=params)
        job._loop = loop
        self._jobs[job.id] = job
        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return job

    def cancel(self, job_id: str) -> None:
        self.get(job_id)._cancel.set()

    # --- internals -------------------------------------------------------
    def _emit(self, job: Job, event: dict) -> None:
        if job._loop is not None:
            job._loop.call_soon_threadsafe(job._queue.put_nowait, event)

    def _run(self, job: Job) -> None:
        job.status = "running"

        def progress(frac: float, msg: str) -> None:
            if job._cancel.is_set():
                raise JobCancelled()
            if frac >= 0:
                job.progress = frac
            job.message = msg
            self._emit(job, {"type": "progress", "progress": job.progress, "message": msg})

        try:
            p = job.params
            result = run_pipeline(
                p["media_path"],
                transcript_path=p.get("transcript_path"),
                diarization_backend=p.get("diarization_backend", "pyannote-local"),
                transcription_backend=p.get("transcription_backend", "faster-whisper-local"),
                num_speakers=p.get("num_speakers"),
                min_speakers=p.get("min_speakers"),
                max_speakers=p.get("max_speakers"),
                language=p.get("language"),
                asr_model=p.get("asr_model"),
                device=p.get("device", "auto"),
                names=p.get("names"),
                output_dir=p.get("output_dir", "out"),
                output_basename=p.get("output_basename"),
                progress=progress,
            )
            job.result = result
            job.status = "done"
            job.progress = 1.0
            self._emit(job, {"type": "done", **job.public()})
        except JobCancelled:
            job.status = "cancelled"
            self._emit(job, {"type": "cancelled", **job.public()})
        except Exception as e:  # noqa: BLE001
            job.status = "error"
            job.error = f"{type(e).__name__}: {e}"
            self._emit(job, {"type": "error", "error": job.error, "trace": traceback.format_exc()})

    def relabel(self, job_id: str, names: dict[str, str]) -> dict:
        """Re-apply a SPEAKER_NN→name mapping to a finished job and rewrite its exports."""
        job = self.get(job_id)
        if job.result is None:
            raise RuntimeError("job has no result to relabel")
        res = job.result
        assign_speakers(res.cues, res.segments, names=names)
        stats = speaker_stats(res.cues)
        vtt.write_vtt(res.cues, res.outputs["vtt"])
        vtt.write_srt(res.cues, res.outputs["srt"])
        vtt.write_txt(res.cues, res.outputs["txt"])
        vtt.write_json(res.cues, res.outputs["json"])
        res.speakers = [
            {"speaker": s.speaker, "minutes": round(s.total_seconds / 60, 1),
             "cues": s.cue_count, "samples": s.samples}
            for s in stats
        ]
        return job.public()
