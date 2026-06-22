"""Deepgram pre-recorded API flow shared by its diarization and transcription backends.

POST local audio bytes to /v1/listen with utterances + optional diarize.
Docs: https://developers.deepgram.com/docs/pre-recorded-audio
"""

from __future__ import annotations

from typing import Optional

from .cloud_util import _client, require_key

_URL = "https://api.deepgram.com/v1/listen"


def run(audio_path: str, *, diarize: bool, language: Optional[str], model: Optional[str]) -> dict:
    key = require_key("DEEPGRAM_API_KEY", "Deepgram")
    params = {
        "model": model or "nova-2",
        "smart_format": "true",
        "utterances": "true",
        "diarize": "true" if diarize else "false",
    }
    if language:
        params["language"] = language
    headers = {"Authorization": f"Token {key}", "Content-Type": "audio/wav"}
    with _client() as http:
        with open(audio_path, "rb") as f:
            r = http.post(_URL, params=params, headers=headers, content=f.read())
        r.raise_for_status()
        return r.json()


def utterances(result: dict) -> list[dict]:
    return result.get("results", {}).get("utterances", []) or []
