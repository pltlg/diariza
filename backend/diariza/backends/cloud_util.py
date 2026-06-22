"""Shared helpers for cloud backends: API-key lookup and a tiny httpx wrapper.

Keys are read from the OS keychain (via config) or env. Audio is uploaded straight from the local
file since the engine runs on the user's machine.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .. import config


class MissingApiKey(RuntimeError):
    pass


def require_key(env_name: str, human: str) -> str:
    key = config.get_secret(env_name)
    if not key:
        raise MissingApiKey(f"No API key for {human}. Set {env_name} in Settings.")
    return key


def _client(timeout: float = 600.0):
    import httpx  # noqa: PLC0415

    return httpx.Client(timeout=timeout)


def poll(
    fn,
    *,
    is_done,
    interval: float = 3.0,
    timeout: float = 3600.0,
    on_tick=None,
):
    """Poll ``fn()`` until ``is_done(result)`` is truthy or timeout. Returns the final result."""
    start = time.monotonic()
    while True:
        result = fn()
        if is_done(result):
            return result
        if time.monotonic() - start > timeout:
            raise TimeoutError("cloud job timed out")
        if on_tick:
            on_tick(result)
        time.sleep(interval)


def speaker_label(raw: Any) -> str:
    """Normalize a provider speaker id ('A', 0, 'spk_1') to our SPEAKER_NN convention."""
    if isinstance(raw, int):
        return f"SPEAKER_{raw:02d}"
    s = str(raw)
    if len(s) == 1 and s.isalpha():  # AssemblyAI uses 'A','B',...
        return f"SPEAKER_{ord(s.upper()) - 65:02d}"
    return f"SPEAKER_{s}"
