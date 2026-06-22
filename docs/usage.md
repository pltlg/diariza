# Using diariza

## Install (end users)

Download the installer for your OS from the GitHub Releases page and run it:
- **Windows:** `diariza-<version>-setup.exe` (choose the **CUDA** build for an NVIDIA GPU, or the
  **CPU** build otherwise — the app falls back to CPU automatically if a GPU isn't usable).
- **macOS:** `diariza-<version>.dmg` (Apple Silicon; runs on CPU/MPS).

## First run — models & keys

Open **Settings**:
- **Local pyannote** (default): paste a **Hugging Face token** and accept the gated models at
  `hf.co/pyannote/speaker-diarization-3.1` and `hf.co/pyannote/segmentation-3.0` with the same
  account. Models download on first use.
- **Cloud backends** (AssemblyAI / Deepgram / pyannoteAI): paste the relevant API key. Audio is
  uploaded to that provider.

Secrets are stored in your OS keychain, never in plaintext files.

## Workflow

1. **Import** — pick a video/audio file. Optionally add an existing transcript (`.vtt`/`.srt`):
   - with a transcript → **Mode B**: only speaker labels are added;
   - without → **Mode A**: it transcribes with Whisper first.
2. **Configure** — choose diarization (and transcription) backend, **device** (Auto/GPU/CPU),
   number of speakers (blank = auto), and output folder.
3. **Run** — watch live progress; cancel any time.
4. **Speakers** — rename detected speakers; give two rows the same name to merge them, then
   **Apply**.
5. **Export** — labeled `.vtt`, `.srt`, `.txt` and `.json` are written to your output folder.

## Headless / CLI

The engine also runs without the UI:

```bash
diariza run meeting.mp4 --num-speakers 6 -o out/                 # Mode A (Whisper + diarize)
diariza run meeting.mp4 -t meeting.vtt --num-speakers 6 -o out/  # Mode B (existing transcript)
diariza devices    # list compute devices + usability
diariza backends   # list installed backends
```

## Language

Toggle **EN / HU** in the header (the choice is remembered).
