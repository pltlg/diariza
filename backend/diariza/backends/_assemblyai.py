"""AssemblyAI REST flow shared by its diarization and transcription backends.

Upload local audio → create a transcript (optionally with speaker_labels) → poll until done.
Docs: https://www.assemblyai.com/docs
"""

from __future__ import annotations

from typing import Optional

from .cloud_util import _client, require_key, poll

_BASE = "https://api.assemblyai.com/v2"


def run(audio_path: str, *, speaker_labels: bool, language: Optional[str], on_tick=None) -> dict:
    key = require_key("ASSEMBLYAI_API_KEY", "AssemblyAI")
    headers = {"authorization": key}
    with _client() as http:
        with open(audio_path, "rb") as f:
            up = http.post(f"{_BASE}/upload", headers=headers, content=f.read())
        up.raise_for_status()
        audio_url = up.json()["upload_url"]

        body: dict = {"audio_url": audio_url, "speaker_labels": speaker_labels}
        if language:
            body["language_code"] = language
        cr = http.post(f"{_BASE}/transcript", headers=headers, json=body)
        cr.raise_for_status()
        tid = cr.json()["id"]

        def fetch() -> dict:
            r = http.get(f"{_BASE}/transcript/{tid}", headers=headers)
            r.raise_for_status()
            return r.json()

        result = poll(
            fetch,
            is_done=lambda r: r["status"] in ("completed", "error"),
            on_tick=lambda r: on_tick and on_tick(r.get("status", "")),
        )
        if result["status"] == "error":
            raise RuntimeError(f"AssemblyAI error: {result.get('error')}")
        return result
