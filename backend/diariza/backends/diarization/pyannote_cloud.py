"""pyannoteAI cloud diarization.

Flow (https://docs.pyannote.ai): create a temporary media slot → PUT the local file to the
presigned URL → start a diarize job → poll until it succeeds → map output to Segments.
"""

from __future__ import annotations

from typing import Optional

from ...types import Segment
from ..base import DiarizationBackend, ProgressFn, _noop
from ..cloud_util import _client, poll, require_key, speaker_label

_BASE = "https://api.pyannote.ai/v1"


class PyannoteAICloudDiarization(DiarizationBackend):
    name = "pyannoteai-cloud"
    requires_api_key = True
    supports_num_speakers = True

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"num_speakers": {"type": "integer", "minimum": 1,
                                            "title": "Exact speakers (optional)"}},
        }

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
        key = require_key("PYANNOTEAI_API_KEY", "pyannoteAI")
        headers = {"Authorization": f"Bearer {key}"}
        media_url = "media://diariza-upload"

        with _client() as http:
            progress(-1.0, "requesting upload slot")
            slot = http.post(f"{_BASE}/media/input", headers=headers, json={"url": media_url})
            slot.raise_for_status()
            put_url = slot.json()["url"]

            progress(-1.0, "uploading audio")
            with open(audio_path, "rb") as f:
                http.put(put_url, content=f.read(),
                         headers={"Content-Type": "application/octet-stream"}).raise_for_status()

            body: dict = {"url": media_url}
            if num_speakers:
                body["numSpeakers"] = num_speakers
            progress(-1.0, "starting diarization job")
            job = http.post(f"{_BASE}/diarize", headers=headers, json=body)
            job.raise_for_status()
            job_id = job.json()["jobId"]

            def fetch() -> dict:
                r = http.get(f"{_BASE}/jobs/{job_id}", headers=headers)
                r.raise_for_status()
                return r.json()

            result = poll(
                fetch,
                is_done=lambda r: r.get("status") in ("succeeded", "failed", "canceled"),
                on_tick=lambda r: progress(-1.0, f"pyannoteAI: {r.get('status')}"),
            )
            if result.get("status") != "succeeded":
                raise RuntimeError(f"pyannoteAI job {result.get('status')}")

        diar = result.get("output", {}).get("diarization", []) or []
        segments = [
            Segment(start=float(d["start"]), end=float(d["end"]),
                    speaker=speaker_label(d["speaker"]))
            for d in diar
        ]
        progress(1.0, f"diarization done: {len(segments)} segments")
        return segments
