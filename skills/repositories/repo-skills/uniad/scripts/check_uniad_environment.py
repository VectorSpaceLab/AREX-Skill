#!/usr/bin/env python3
"""Check a UniAD runtime for imports, CUDA, and optional config parsing."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

MODULES = ["torch", "mmcv", "mmdet", "mmseg", "mmdet3d"]
CONFIGS = [
    "projects/configs/bevformer/base_bevformer.py",
    "projects/configs/stage1_track_map/base_track_map.py",
    "projects/configs/stage2_e2e/base_e2e.py",
]


def module_version(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"


def check_cuda() -> dict:
    try:
        import torch

        info = {
            "torch": getattr(torch, "__version__", "unknown"),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["tensor_allocation"] = "passed"
        return info
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"error": f"{type(exc).__name__}: {exc}"}


def parse_configs(repo_root: Path) -> list[dict]:
    try:
        from mmcv import Config
    except Exception as exc:
        return [{"error": f"cannot import mmcv.Config: {type(exc).__name__}: {exc}"}]

    out = []
    for rel in CONFIGS:
        path = repo_root / rel
        if not path.is_file():
            out.append({"config": rel, "status": "missing"})
            continue
        try:
            cfg = Config.fromfile(str(path))
            out.append(
                {
                    "config": rel,
                    "status": "ok",
                    "model": cfg.model.get("type") if hasattr(cfg, "model") else None,
                    "dataset_type": cfg.get("dataset_type"),
                    "queue_length": cfg.get("queue_length"),
                    "load_from": cfg.get("load_from"),
                    "plugin": cfg.get("plugin"),
                    "plugin_dir": cfg.get("plugin_dir"),
                }
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            out.append({"config": rel, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="UniAD checkout root to add to sys.path and inspect")
    parser.add_argument("--configs", action="store_true", help="Parse the three public UniAD configs")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.environ["PYTHONPATH"] = str(repo_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

    result = {
        "python": sys.version.split()[0],
        "repo_root_exists": repo_root.is_dir(),
        "modules": {},
        "cuda": check_cuda(),
        "plugin_import": None,
    }
    for mod in MODULES:
        ok, version_or_error = module_version(mod)
        result["modules"][mod] = {"ok": ok, "version_or_error": version_or_error}
    try:
        import projects.mmdet3d_plugin  # noqa: F401

        result["plugin_import"] = {"ok": True, "module": "projects.mmdet3d_plugin"}
    except Exception as exc:
        result["plugin_import"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.configs:
        result["configs"] = parse_configs(repo_root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
        if not result["plugin_import"]["ok"]:
            print("\nPlugin import failed. Check PYTHONPATH, OpenMMLab versions, and mmcv-full CUDA ops.", file=sys.stderr)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
