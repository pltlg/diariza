"""Device detection and the GPU-usability probe.

Productizes the Pascal lesson: ``torch.cuda.is_available()`` can return True on a GPU whose kernels
aren't in the installed torch build (Quadro P2200 / sm_61 vs a cu128 wheel), and the failure only
shows up mid-run as "no kernel image is available for execution on the device". So before trusting a
GPU we run a tiny real matmul and fall back to CPU if it raises.

torch is an optional extra; everything here degrades to CPU-only when torch isn't installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Optional

DeviceKind = Literal["cuda", "mps", "cpu"]


@dataclass
class DeviceInfo:
    kind: DeviceKind
    name: str
    usable: bool
    detail: str = ""


def _try_import_torch():
    try:
        import torch  # noqa: PLC0415

        return torch
    except Exception:
        return None


def _cuda_usable(torch) -> tuple[bool, str]:
    """Real op on the GPU — catches the 'is_available True but no kernel image' trap."""
    try:
        x = torch.randn(64, 64, device="cuda")
        _ = float((x @ x).sum().item())
        return True, ""
    except Exception as e:  # AcceleratorError / RuntimeError: no kernel image, OOM, etc.
        return False, str(e).splitlines()[0] if str(e) else type(e).__name__


@lru_cache(maxsize=1)
def list_devices() -> list[DeviceInfo]:
    """All candidate devices with a usability verdict. CPU is always present and usable."""
    devices: list[DeviceInfo] = []
    torch = _try_import_torch()
    if torch is not None:
        try:
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                ok, why = _cuda_usable(torch)
                cc = ".".join(map(str, torch.cuda.get_device_capability(0)))
                detail = f"compute capability {cc}" + (f"; {why}" if not ok else "")
                devices.append(DeviceInfo("cuda", name, ok, detail))
        except Exception:
            pass
        try:
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                devices.append(DeviceInfo("mps", "Apple GPU (MPS)", True))
        except Exception:
            pass
    devices.append(DeviceInfo("cpu", "CPU", True))
    return devices


def resolve_device(preference: str = "auto") -> DeviceInfo:
    """Resolve a user preference ('auto' | 'cuda'/'gpu' | 'mps' | 'cpu') to a concrete device.

    'auto' picks the best *usable* accelerator (cuda → mps → cpu). An explicit accelerator that is
    present-but-unusable is returned as-is (usable=False) so the caller can show a clear error and
    offer a one-click switch to CPU.
    """
    devices = {d.kind: d for d in list_devices()}
    pref = preference.lower()
    if pref in ("gpu", "cuda"):
        pref = "cuda"
    if pref == "auto":
        for kind in ("cuda", "mps", "cpu"):
            d = devices.get(kind)
            if d and d.usable:
                return d
        return devices["cpu"]
    return devices.get(pref) or devices["cpu"]


def torch_device_str(info: DeviceInfo) -> str:
    return info.kind  # "cuda" | "mps" | "cpu" — what torch.device() accepts
