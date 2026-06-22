from fastapi.testclient import TestClient

from diariza.server import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_devices_lists_cpu():
    r = client.get("/devices")
    assert r.status_code == 200
    kinds = {d["kind"] for d in r.json()["devices"]}
    assert "cpu" in kinds


def test_backends_expose_schema():
    r = client.get("/backends")
    data = r.json()
    diar_names = {b["name"] for b in data["diarization"]}
    asr_names = {b["name"] for b in data["transcription"]}
    assert "pyannote-local" in diar_names
    assert "faster-whisper-local" in asr_names
    # Each backend advertises a config schema the UI can render.
    for b in data["diarization"] + data["transcription"]:
        assert "config_schema" in b or b.get("available") is False


def test_unknown_job_404():
    assert client.get("/jobs/nope").status_code == 404
