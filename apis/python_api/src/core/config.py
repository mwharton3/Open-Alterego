"""Runtime configuration shared by every user interface."""

import os
from dataclasses import dataclass
from typing import Mapping


def resolve_device(device: str = "auto") -> str:
    """Map ``auto`` to ``cuda`` when an NVIDIA GPU is usable, else ``cpu``.

    Any explicit value (``cpu``, ``cuda``, ``cuda:1``, ``mps``) is returned
    unchanged. Apple ``mps`` is deliberately not auto-selected: with torch 2.6
    it needs ``PYTORCH_ENABLE_MPS_FALLBACK=1`` (no ``max_pool3d``) and measured
    about 2x slower than CPU for this model's beam search on an M3 Pro.
    torch is imported lazily so configuration stays cheap.
    """

    if device != "auto":
        return device
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Model configuration with no dependency on a particular UI."""

    device: str = "auto"
    detector: str = "mediapipe"
    checkpoint_path: str | None = None
    enhance: bool = True

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "RuntimeConfig":
        values = os.environ if environ is None else environ
        return cls(
            device=values.get("LIPREAD_DEVICE") or "auto",
            detector=values.get("LIPREAD_DETECTOR", "mediapipe"),
            checkpoint_path=values.get("LIPREAD_CKPT") or None,
        )
