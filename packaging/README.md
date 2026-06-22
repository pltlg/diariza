# Packaging

Produces the bundled installers (`.exe` / `.dmg`) — the Python engine is frozen with PyInstaller and
shipped inside the Electron app as a sidecar binary.

## Steps

1. **Build the engine binary** → `packaging/dist/backend/`:
   - Windows (GPU): `./build_backend.ps1 -Cuda cu121`
   - Windows (CPU): `./build_backend.ps1`
   - macOS/Linux: `./build_backend.sh`
2. **Provide ffmpeg** → drop `ffmpeg(.exe)` into `packaging/ffmpeg/` (see `ffmpeg/README.md`).
3. **Build the installer** (from `apps/desktop/`):
   - `npm run dist:win` or `npm run dist:mac`
   - `electron-builder.yml` copies `packaging/dist/backend` and `packaging/ffmpeg/ffmpeg*` into
     the app's `resources/backend/`, where `src/main/sidecar.ts` finds them at runtime.

## The torch / GPU caveat (important)

A single bundled torch build cannot serve every GPU — this is the exact Pascal (sm_61) failure that
motivated the project. Strategy:

- **Windows** ships **two** variants: a **CUDA build** (`-Cuda cu121`, which still includes Pascal
  `sm_60/61`) and a **CPU-only** build. The app's hardware probe (`diariza/hardware.py`) routes to
  CPU at runtime if the GPU isn't usable, so even the CUDA build degrades gracefully.
- **macOS (arm64)** ships CPU/MPS.

## Gated models

pyannote local models are gated. On first run the user adds an HF token in **Settings** and accepts
the model conditions (the app links to the HF pages). Cloud backends use their own API keys.
