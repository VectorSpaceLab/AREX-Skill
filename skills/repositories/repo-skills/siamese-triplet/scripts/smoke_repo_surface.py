#!/usr/bin/env python3
"""Run a bundled smoke over the repo's public surface.

Use this from a checkout or module directory that exposes the repo's top-level
modules (`datasets.py`, `losses.py`, `metrics.py`, `networks.py`, `trainer.py`,
`utils.py`). The script avoids dataset downloads and instead uses tiny synthetic
fixtures that match the notebook shapes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_script(label: str, script: Path, module_dir: str) -> None:
    cmd = [sys.executable, str(script), "--module-dir", module_dir]
    print(f"[{label}] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module-dir",
        default=str(Path.cwd()),
        help="Directory containing the repo's top-level modules; defaults to the current working directory.",
    )
    parser.add_argument(
        "--skip-cuda",
        action="store_true",
        help="Skip the optional CUDA allocation smoke even when CUDA is available.",
    )
    args = parser.parse_args()

    module_dir = str(Path(args.module_dir).resolve())
    here = Path(__file__).resolve().parent

    run_script("dataset-sampling", here.parent / "sub-skills" / "dataset-sampling" / "scripts" / "check_dataset_wrappers.py", module_dir)
    run_script("embedding-losses-mining", here.parent / "sub-skills" / "embedding-losses-mining" / "scripts" / "check_losses_networks.py", module_dir)
    run_script("training-experiments", here.parent / "sub-skills" / "training-experiments" / "scripts" / "tiny_training_smoke.py", module_dir)

    if not args.skip_cuda:
        try:
            import torch
        except Exception as exc:  # pragma: no cover - import guard only
            print(f"[cuda] skipped: torch import failed: {exc}")
        else:
            if torch.cuda.is_available():
                x = torch.empty((1,), device="cuda")
                print(f"[cuda] allocation ok: {x.device} {x.dtype} {tuple(x.shape)}")
            else:
                print("[cuda] skipped: CUDA unavailable")

    print("ALL_SMOKES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
