#!/usr/bin/env python3
"""Check the AnyDoor repo layout, runtime imports, and placeholder paths.

This is a safe preflight helper. It does not run generation, download weights,
or start training.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - optional in very small environments
    yaml = None

warnings.filterwarnings("ignore", message="Could not get documentation group*")


REQUIRED_PATHS = [
    "readme.md",
    "requirements.txt",
    "environment.yaml",
    "cog.yaml",
    "configs/anydoor.yaml",
    "configs/inference.yaml",
    "configs/demo.yaml",
    "configs/datasets.yaml",
    "cldm/model.py",
    "cldm/cldm.py",
    "ldm/util.py",
    "datasets/data_utils.py",
    "run_inference.py",
    "run_gradio_demo.py",
    "run_train_anydoor.py",
    "predict.py",
    "tool_add_control_sd21.py",
]

OPTIONAL_PATHS = [
    "iseg/coarse_mask_refine.pth",
    "dinov2/README.md",
]

MODULES = [
    "torch",
    "torchvision",
    "cv2",
    "numpy",
    "omegaconf",
    "pytorch_lightning",
    "einops",
    "albumentations",
    "gradio",
    "transformers",
    "open_clip",
    "safetensors",
    "pycocotools",
    "lvis",
    "panopticapi",
    "timm",
    "fvcore",
]


def read_yaml(path: Path) -> Any:
    if yaml is None:
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_placeholders(node: Any, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            hits.extend(collect_placeholders(value, child_prefix))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            child_prefix = f"{prefix}[{idx}]"
            hits.extend(collect_placeholders(value, child_prefix))
    elif isinstance(node, str) and node.startswith("path/"):
        hits.append(f"{prefix}={node}")
    return hits


def module_status(name: str, repo_root: Path) -> dict[str, str]:
    try:
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        dinov2 = repo_root / "dinov2"
        if dinov2.exists() and str(dinov2) not in sys.path:
            sys.path.insert(0, str(dinov2))
        mod = importlib.import_module(name)
        return {"module": name, "status": "ok", "detail": getattr(mod, "__file__", "<namespace>")}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"module": name, "status": "fail", "detail": f"{type(exc).__name__}: {exc}"}


def torch_smoke(repo_root: Path) -> dict[str, str]:
    try:
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        import torch  # type: ignore

        result = {
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_runtime": str(getattr(torch.version, "cuda", None)),
            "cuda_available": str(torch.cuda.is_available()),
            "device_count": str(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            result["device0"] = torch.cuda.get_device_name(0)
            result["capability0"] = str(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            result["allocation"] = "ok"
        else:
            result["allocation"] = "skipped"
        return result
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"status": "fail", "detail": f"{type(exc).__name__}: {exc}"}


def build_report(repo_root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "repo_root": str(repo_root),
        "paths": {"required": {}, "optional": {}},
        "modules": [],
        "torch": {},
        "config_placeholders": {},
    }

    for rel in REQUIRED_PATHS:
        path = repo_root / rel
        report["paths"]["required"][rel] = path.exists()
    for rel in OPTIONAL_PATHS:
        path = repo_root / rel
        report["paths"]["optional"][rel] = path.exists()

    for rel in ["configs/anydoor.yaml", "configs/inference.yaml", "configs/demo.yaml", "configs/datasets.yaml"]:
        path = repo_root / rel
        if path.exists() and yaml is not None:
            data = read_yaml(path)
            report["config_placeholders"][rel] = collect_placeholders(data)
        else:
            report["config_placeholders"][rel] = ["yaml-unavailable-or-missing"]

    report["modules"] = [module_status(name, repo_root) for name in MODULES]
    report["torch"] = torch_smoke(repo_root)
    return report


def print_human(report: dict[str, Any]) -> None:
    print(f"repo_root: {report['repo_root']}")
    print("required_paths:")
    for rel, ok in report["paths"]["required"].items():
        print(f"  {rel}: {'ok' if ok else 'missing'}")
    print("optional_paths:")
    for rel, ok in report["paths"]["optional"].items():
        print(f"  {rel}: {'ok' if ok else 'missing'}")
    print("config_placeholders:")
    for rel, hits in report["config_placeholders"].items():
        print(f"  {rel}: {hits if hits else 'none'}")
    print("modules:")
    for item in report["modules"]:
        print(f"  {item['module']}: {item['status']} :: {item['detail']}")
    print("torch:")
    for key, value in report["torch"].items():
        print(f"  {key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AnyDoor runtime readiness without running generation.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="AnyDoor repository root to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
