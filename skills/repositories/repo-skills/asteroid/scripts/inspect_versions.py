#!/usr/bin/env python3
"""Print Asteroid runtime versions and a tiny backend summary.

Use this script when you want a fast, self-contained inspection of the active
environment before choosing an Asteroid sub-skill or debugging imports.
"""

from __future__ import annotations

import importlib.metadata as md


def _safe_version(dist_name: str) -> str:
    try:
        return md.version(dist_name)
    except md.PackageNotFoundError:
        return "not installed"


def main() -> None:
    import asteroid
    import torch
    import pytorch_lightning as pl
    import torchaudio

    print(f"Asteroid: {asteroid.__version__}")
    print(f"Torch: {torch.__version__}")
    print(f"TorchAudio: {torchaudio.__version__}")
    print(f"PyTorch-Lightning: {pl.__version__}")
    print(f"Torch CUDA: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")

    # Keep these as versions rather than imports so the script remains a quick
    # environment probe even if a downstream optional import is absent.
    for dist in [
        "asteroid-filterbanks",
        "soundfile",
        "requests",
        "huggingface_hub",
        "pandas",
        "numpy",
        "scipy",
        "pb_bss_eval",
        "torch_stoi",
        "julius",
        "librosa",
    ]:
        print(f"{dist}: {_safe_version(dist)}")


if __name__ == "__main__":
    main()
