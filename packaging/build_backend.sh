#!/usr/bin/env bash
# Build the diariza engine into packaging/dist/backend (macOS / Linux).
#   ./build_backend.sh            # CPU / Apple-MPS build (arm64 wheels include MPS)
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .buildvenv
py=".buildvenv/bin/python"
"$py" -m pip install --upgrade pip
echo "==> engine + ML extras + pyinstaller..."
"$py" -m pip install "../backend[pyannote,whisper,cloud]" pyinstaller

echo "==> PyInstaller..."
"$py" -m PyInstaller pyinstaller/diariza-backend.spec --distpath dist --workpath build --noconfirm

echo ""
echo "Done: packaging/dist/backend/diariza-backend"
