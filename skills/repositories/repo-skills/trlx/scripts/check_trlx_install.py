#!/usr/bin/env python3
"""Check that a trlX installation is usable without launching training.

This helper is safe to run from any working directory. It prints the installed
trlX version, key registry entries, and the `trlx.train` signature. With
`--cuda`, it also performs a tiny CUDA allocation smoke test when a CUDA device
is available.

Example:
    python scripts/check_trlx_install.py
    python scripts/check_trlx_install.py --json
    python scripts/check_trlx_install.py --cuda
    python scripts/check_trlx_install.py --repo-root /path/to/checkout
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    repo = Path(repo_root).expanduser().resolve()
    if repo.is_dir() and str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _safe_imports() -> Dict[str, Any]:
    try:
        import inspect
        import trlx
        from trlx import train
        from trlx.data.default_configs import default_ilql_config, default_ppo_config, default_sft_config
        from trlx.data.method_configs import _METHODS
        from trlx.pipeline import _DATAPIPELINE
        from trlx.trainer import _TRAINERS
    except Exception as exc:  # pragma: no cover - helpful failure path
        raise RuntimeError(
            "Unable to import trlx from the target environment. Install the repo requirements and editable package, "
            "then rerun this check."
        ) from exc

    summary = {
        "trlx_version": getattr(trlx, "__version__", metadata.version("trlx")),
        "train_signature": str(inspect.signature(train)),
        "methods": sorted(_METHODS.keys()),
        "trainers": sorted(_TRAINERS.keys()),
        "pipelines": sorted(_DATAPIPELINE.keys()),
        "default_configs": {
            "ppo": {
                "trainer": default_ppo_config().train.trainer,
                "pipeline": default_ppo_config().train.pipeline,
                "method": default_ppo_config().method.name,
            },
            "ilql": {
                "trainer": default_ilql_config().train.trainer,
                "pipeline": default_ilql_config().train.pipeline,
                "method": default_ilql_config().method.name,
            },
            "sft": {
                "trainer": default_sft_config().train.trainer,
                "pipeline": default_sft_config().train.pipeline,
                "method": default_sft_config().method.name,
            },
        },
    }
    return summary


def _cuda_smoke() -> Dict[str, Any]:
    import torch

    info: Dict[str, Any] = {
        "torch_version": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
        info["device_capability"] = list(torch.cuda.get_device_capability(0))
        x = torch.empty((1,), device="cuda")
        info["tiny_allocation"] = [str(x.device), int(x.numel())]
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--cuda", action="store_true", help="Also run a tiny CUDA smoke test if available.")
    parser.add_argument(
        "--repo-root",
        help="Optional checkout root to prepend to sys.path before importing trlx; useful only when the package is not installed yet.",
    )
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)

    try:
        summary = _safe_imports()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.cuda:
        try:
            summary["cuda"] = _cuda_smoke()
        except Exception as exc:  # pragma: no cover - safe failure path
            print(f"ERROR: CUDA smoke failed: {exc}", file=sys.stderr)
            return 3

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"trlx {summary['trlx_version']}")
        print(f"train: {summary['train_signature']}")
        print(f"methods: {', '.join(summary['methods'])}")
        print(f"trainers: {', '.join(summary['trainers'])}")
        print(f"pipelines: {', '.join(summary['pipelines'])}")
        for name, cfg in summary["default_configs"].items():
            print(f"default[{name}]: trainer={cfg['trainer']} pipeline={cfg['pipeline']} method={cfg['method']}")
        if "cuda" in summary:
            cuda = summary["cuda"]
            print(
                f"cuda: available={cuda['cuda_available']} count={cuda['device_count']} runtime={cuda['cuda_runtime']}"
            )
            if cuda.get("cuda_available"):
                print(f"cuda device0: {cuda['device_name']} capability={tuple(cuda['device_capability'])}")
                print(f"cuda tiny allocation: {cuda['tiny_allocation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
