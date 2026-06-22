"""FastAPI sidecar: REST for actions + WebSocket for live job progress.

The Electron main process spawns this (``python -m diariza.server`` in dev, the PyInstaller binary
in prod) on a localhost port and the renderer talks to it. Local-file paths are passed directly
since both sides run on the same machine.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__, config
from .hardware import list_devices
from .jobs import JobManager
from .registry import diarization_backends, transcription_backends

app = FastAPI(title="diariza", version=__version__)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
jobs = JobManager()


# --- schemas ------------------------------------------------------------
class JobRequest(BaseModel):
    media_path: str
    transcript_path: Optional[str] = None
    diarization_backend: str = "pyannote-local"
    transcription_backend: str = "faster-whisper-local"
    num_speakers: Optional[int] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    language: Optional[str] = None
    asr_model: Optional[str] = None
    device: str = "auto"
    names: Optional[dict[str, str]] = None
    output_dir: str = "out"
    output_basename: Optional[str] = None


class SecretRequest(BaseModel):
    key: str
    value: str


class RelabelRequest(BaseModel):
    names: dict[str, str]


def _describe(backends: dict[str, type]) -> list[dict]:
    out = []
    for name, cls in backends.items():
        try:
            inst = cls()
            out.append({
                "name": name,
                "requires_api_key": getattr(inst, "requires_api_key", False),
                "supports_num_speakers": getattr(inst, "supports_num_speakers", False),
                "config_schema": inst.config_schema(),
            })
        except Exception as e:  # a backend whose deps are missing still lists its name
            out.append({"name": name, "available": False, "error": str(e)})
    return out


# --- REST ---------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/devices")
def devices() -> dict:
    return {"devices": [d.__dict__ for d in list_devices()]}


@app.get("/backends")
def backends() -> dict:
    return {
        "diarization": _describe(diarization_backends()),
        "transcription": _describe(transcription_backends()),
    }


@app.get("/settings")
def get_settings() -> dict:
    return config.load_settings()


@app.put("/settings")
def put_settings(settings: dict) -> dict:
    config.save_settings(settings)
    return settings


@app.post("/secrets")
def set_secret(req: SecretRequest) -> dict:
    config.set_secret(req.key, req.value)
    return {"ok": True}


@app.post("/jobs")
async def create_job(req: JobRequest) -> dict:
    loop = asyncio.get_running_loop()
    job = jobs.create(req.model_dump(), loop)
    return job.public()


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        return jobs.get(job_id).public()
    except KeyError:
        raise HTTPException(404, "job not found")


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    try:
        jobs.cancel(job_id)
    except KeyError:
        raise HTTPException(404, "job not found")
    return {"ok": True}


@app.post("/jobs/{job_id}/relabel")
def relabel_job(job_id: str, req: RelabelRequest) -> dict:
    try:
        return jobs.relabel(job_id, req.names)
    except KeyError:
        raise HTTPException(404, "job not found")
    except RuntimeError as e:
        raise HTTPException(409, str(e))


@app.websocket("/jobs/{job_id}/events")
async def job_events(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    try:
        job = jobs.get(job_id)
    except KeyError:
        await ws.close(code=4404)
        return
    # Replay current state, then stream until a terminal event.
    await ws.send_json({"type": "progress", "progress": job.progress, "message": job.message})
    try:
        while True:
            event = await job._queue.get()
            await ws.send_json(event)
            if event.get("type") in ("done", "error", "cancelled"):
                break
    except WebSocketDisconnect:
        pass


def main() -> None:
    import argparse

    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
