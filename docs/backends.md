# Authoring a backend

Diarization and transcription models are plugins. Adding one is a class + an entry point — no core
changes. The UI lists it automatically and renders its options from `config_schema()`.

## Diarization backend

```python
from diariza.backends.base import DiarizationBackend, ProgressFn, _noop
from diariza.types import Segment

class MyDiarizer(DiarizationBackend):
    name = "my-diarizer"
    requires_api_key = False        # True → the UI prompts for / stores a key
    supports_num_speakers = True

    def config_schema(self) -> dict:
        # JSON schema → the Configure screen renders a form from this.
        return {"type": "object", "properties": {
            "num_speakers": {"type": "integer", "minimum": 1, "title": "Speakers"}}}

    def diarize(self, audio_path, *, num_speakers=None, min_speakers=None,
                max_speakers=None, device="auto", progress: ProgressFn = _noop, **options):
        progress(-1.0, "working")            # fraction in 0..1, or <0 for indeterminate
        # ... produce speaker turns ...
        return [Segment(start=0.0, end=1.0, speaker="SPEAKER_00")]
```

## Transcription backend

Implement `TranscriptionBackend.transcribe(...)` returning `list[Cue]`
(`Cue(start, end, text)`).

## Registering

Add an entry point in `backend/pyproject.toml` (or your own package's):

```toml
[project.entry-points."diariza.diarization_backends"]
my-diarizer = "my_pkg.my_module:MyDiarizer"

[project.entry-points."diariza.transcription_backends"]
my-asr = "my_pkg.my_module:MyAsr"
```

Reinstall (`pip install -e .`) and it appears in `diariza backends` and the app.

## Conventions

- Times are floats in **seconds**.
- Normalize provider speaker ids to `SPEAKER_NN` (see `backends/cloud_util.speaker_label`).
- Keep heavy imports (torch, etc.) **inside** the method, not at module top, so the engine and the
  backend list load fast and without the optional dependency.
- Read the device with `diariza.hardware.resolve_device(device)` and honor CPU fallback.
