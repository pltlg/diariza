# diariza

Cross-platform desktop app (Windows + macOS) that turns a **video or audio file** — optionally with
an existing transcript — into a **speaker-labeled transcript**.

- **Two modes:** transcribe from scratch (Whisper) → diarize → merge, *or* import an existing
  transcript (VTT/SRT) and just add speaker labels.
- **Interchangeable models:** diarization and transcription backends are plugins (local *and*
  cloud) selected at runtime.
- **CPU + GPU with auto-detect:** picks the best usable device (CUDA → Apple MPS → CPU) and falls
  back safely when a GPU is present but unusable.

## Architecture

```
React renderer  <—HTTP + WebSocket—>  Python FastAPI sidecar (pyannote / whisper / cloud)
        \__ Electron main (window + spawns/supervises the sidecar) __/
```

- `backend/` — the Python engine (pipeline, plugin backends, FastAPI server, CLI). Works headless.
- `apps/desktop/` — the Electron + React desktop shell.
- `packaging/` — PyInstaller spec + ffmpeg binaries + installer config.

## Engine quickstart (headless)

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
# Mode B (merge speakers onto an existing transcript):
diariza run path/to/video.mp4 --transcript path/to/transcript.vtt --num-speakers 6 -o out/
# Mode A (transcribe from scratch, then diarize):
diariza run path/to/video.mp4 --transcribe --language hu -o out/
```

See `docs/` for backend plugin authoring and the full app build.

## Status

Early development. Milestone order: M0 scaffold → M1 headless engine → M2 API → M3 Electron shell →
M4 speaker labeling UI → M5 more backends → M6 packaging.
