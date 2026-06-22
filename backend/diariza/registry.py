"""Backend discovery.

Primary path: Python entry points (``diariza.diarization_backends`` /
``diariza.transcription_backends``) so third-party backends are found automatically once installed.
Fallback path: a small built-in table, so the engine also works when run straight from a source
checkout that hasn't been ``pip install``-ed.

Backend *classes* are listed eagerly (cheap), but only *instantiated* on demand — heavy imports
(torch, pyannote, faster-whisper) happen lazily inside each backend module.
"""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import entry_points

from .backends.base import DiarizationBackend, TranscriptionBackend

# (entry-point name, "module:ClassName") — fallback when entry points aren't registered.
_BUILTIN_DIARIZATION = {
    "pyannote-local": "diariza.backends.diarization.pyannote_local:PyannoteLocalBackend",
    "nemo-local": "diariza.backends.diarization.nemo_local:NeMoLocalBackend",
    "pyannoteai-cloud": "diariza.backends.diarization.pyannote_cloud:PyannoteAICloudDiarization",
    "assemblyai-cloud": "diariza.backends.diarization.assemblyai:AssemblyAICloudDiarization",
    "deepgram-cloud": "diariza.backends.diarization.deepgram:DeepgramCloudDiarization",
}
_BUILTIN_TRANSCRIPTION = {
    "faster-whisper-local": "diariza.backends.transcription.faster_whisper_local:FasterWhisperBackend",
    "assemblyai-cloud": "diariza.backends.transcription.assemblyai:AssemblyAICloudTranscription",
    "deepgram-cloud": "diariza.backends.transcription.deepgram:DeepgramCloudTranscription",
}


def _load(path: str) -> type:
    module, _, cls = path.partition(":")
    return getattr(import_module(module), cls)


def _discover(group: str, builtins: dict[str, str]) -> dict[str, type]:
    found: dict[str, type] = {}
    try:
        for ep in entry_points(group=group):
            try:
                found[ep.name] = ep.load()
            except Exception:
                pass  # a broken/optional backend must not break discovery of the others
    except Exception:
        pass
    for name, path in builtins.items():
        found.setdefault(name, _LazyClass(path))  # type: ignore[assignment]
    return found


class _LazyClass:
    """Defer importing a backend class until it's actually instantiated."""

    def __init__(self, path: str):
        self._path = path
        self._cls: type | None = None

    def _resolve(self) -> type:
        if self._cls is None:
            self._cls = _load(self._path)
        return self._cls

    def __call__(self, *a, **kw):
        return self._resolve()(*a, **kw)


def diarization_backends() -> dict[str, type]:
    return _discover("diariza.diarization_backends", _BUILTIN_DIARIZATION)


def transcription_backends() -> dict[str, type]:
    return _discover("diariza.transcription_backends", _BUILTIN_TRANSCRIPTION)


def get_diarization_backend(name: str) -> DiarizationBackend:
    backends = diarization_backends()
    if name not in backends:
        raise KeyError(f"Unknown diarization backend '{name}'. Available: {sorted(backends)}")
    return backends[name]()


def get_transcription_backend(name: str) -> TranscriptionBackend:
    backends = transcription_backends()
    if name not in backends:
        raise KeyError(f"Unknown transcription backend '{name}'. Available: {sorted(backends)}")
    return backends[name]()
