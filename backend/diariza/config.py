"""User settings + secret storage.

Plain settings live in a JSON file under the per-user app-config dir; secrets (HF token, cloud API
keys) go to the OS keychain via ``keyring`` and are never written to disk in plaintext.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

_SERVICE = "diariza"


def config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    d = Path(base) / "diariza"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return config_dir() / "settings.json"


def load_settings() -> dict[str, Any]:
    p = _settings_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(settings: dict[str, Any]) -> None:
    _settings_path().write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def get_secret(key: str) -> Optional[str]:
    """Read a secret from the OS keychain, falling back to an env var of the same name."""
    try:
        import keyring  # noqa: PLC0415

        val = keyring.get_password(_SERVICE, key)
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key)


def set_secret(key: str, value: str) -> None:
    import keyring  # noqa: PLC0415

    keyring.set_password(_SERVICE, key, value)
