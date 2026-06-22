# PyInstaller spec for the diariza engine → one-folder binary "diariza-backend".
# Build from packaging/:  pyinstaller pyinstaller/diariza-backend.spec --distpath dist --workpath build
#
# collect_all pulls the data files, dynamic libs and hidden imports the heavy ML stack needs
# (pyannote/torch ship data + C-extensions that PyInstaller can't infer statically).

from PyInstaller.utils.hooks import collect_all

_PKGS = [
    "diariza",
    "pyannote",
    "pyannote.audio",
    "torch",
    "torchaudio",
    "speechbrain",
    "asteroid_filterbanks",
    "lightning",
    "lightning_fabric",
    "pytorch_lightning",
    "torchmetrics",
    "faster_whisper",
    "ctranslate2",
    "soundfile",
    "huggingface_hub",
    "uvicorn",
    "fastapi",
]

datas, binaries, hiddenimports = [], [], []
for pkg in _PKGS:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass  # optional/absent extras (e.g. cloud-only install) are skipped

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="diariza-backend",
    console=True,
)

coll = COLLECT(exe, a.binaries, a.datas, name="backend")  # → dist/backend/
