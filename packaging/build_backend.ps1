# Build the diariza engine into packaging/dist/backend (Windows).
#
#   .\build_backend.ps1                  # CPU build
#   .\build_backend.ps1 -Cuda cu121      # GPU build (cu121 still supports Pascal sm_61)
param(
    [string]$Cuda = "",                 # "" = CPU; cu121 / cu118 for GPU
    [string]$PythonExe = "python"
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& $PythonExe -m venv .buildvenv
$py = ".\.buildvenv\Scripts\python.exe"
& $py -m pip install --upgrade pip

if ($Cuda) {
    Write-Host "==> torch ($Cuda) for GPU build..."
    & $py -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url "https://download.pytorch.org/whl/$Cuda"
}
Write-Host "==> engine + ML extras + pyinstaller..."
& $py -m pip install "..\backend[pyannote,whisper,cloud]" pyinstaller
# numpy<2 + hub 0.23.5 pin (pyannote 3.1.1) are enforced by the engine's pyproject.

Write-Host "==> PyInstaller..."
& $py -m PyInstaller pyinstaller\diariza-backend.spec --distpath dist --workpath build --noconfirm

Write-Host "`nDone: packaging\dist\backend\diariza-backend.exe" -ForegroundColor Green
