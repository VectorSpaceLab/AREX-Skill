#!/usr/bin/env python3
"""Check whether the current Python can inspect and use MMAction2 safely.

This helper performs import/version/backend checks only. It does not download
weights, open media files, build datasets, train, test, or write outputs unless
`--json-out` is provided.

Example:
    python check_mmaction2_environment.py --probe-config my_config.py --json-out report.json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

CORE = [
    ("mmaction", "mmaction2"),
    ("mmcv", "mmcv"),
    ("mmengine", "mmengine"),
    ("torch", "torch"),
]
OPTIONAL = [
    ("decord", "decord"),
    ("cv2", "opencv-python"),
    ("mmdet", "mmdet"),
    ("mmpose", "mmpose"),
    ("onnx", "onnx"),
    ("onnxruntime", "onnxruntime"),
    ("model_archiver", "torch-model-archiver"),
    ("clip", "openai-clip"),
    ("librosa", "librosa"),
    ("soundfile", "soundfile"),
]


def module_status(module: str, dist: str) -> Dict[str, Any]:
    available = importlib.util.find_spec(module) is not None
    try:
        version = metadata.version(dist)
    except metadata.PackageNotFoundError:
        version = None
    except Exception as exc:  # noqa: BLE001
        version = f"error: {type(exc).__name__}: {exc}"
    return {"module": module, "distribution": dist, "available": available, "version": version}


def import_module(module: str) -> Dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # noqa: BLE001
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def torch_backend() -> Dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    info: Dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_compiled": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if info["cuda_available"]:
        try:
            info["cuda_device_0"] = torch.cuda.get_device_name(0)
            info["cuda_capability_0"] = torch.cuda.get_device_capability(0)
            torch.empty((1,), device="cuda")
            info["cuda_tensor_smoke"] = "passed"
        except Exception as exc:  # noqa: BLE001
            info["cuda_tensor_smoke"] = f"failed: {type(exc).__name__}: {exc}"
    return info


def config_probe(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {"requested": False}
    config_path = Path(path)
    try:
        from mmengine import Config

        cfg = Config.fromfile(config_path)
        model = cfg.get("model", {})
        return {
            "requested": True,
            "ok": True,
            "config_name": config_path.name,
            "default_scope": cfg.get("default_scope", None),
            "model_type": model.get("type") if hasattr(model, "get") else None,
            "train_dataset_type": cfg.get("train_dataloader", {}).get("dataset", {}).get("type"),
            "test_pipeline_length": len(cfg.get("test_pipeline", [])),
        }
    except Exception as exc:  # noqa: BLE001
        return {"requested": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "core": [module_status(*item) for item in CORE],
        "optional": [module_status(*item) for item in OPTIONAL],
        "imports": [import_module(module) for module, _ in CORE],
        "torch_backend": torch_backend(),
        "config_probe": config_probe(args.probe_config),
        "notes": [
            "CUDA is optional for many MMAction2 workflows; pass device='cpu' explicitly on CPU-only hosts.",
            "mmdet and mmpose are optional for detection/pose-assisted demos, not required for ordinary recognizer inference.",
            "This helper does not prove a checkpoint, dataset, video decoder, or distributed job works.",
        ],
    }
    report["ok"] = all(row.get("available") for row in report["core"]) and all(row.get("ok") for row in report["imports"])
    return report


def print_text(report: Dict[str, Any]) -> None:
    print("MMAction2 environment check")
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print("\nCore packages:")
    for row in report["core"]:
        print(f"  - {row['module']}: available={row['available']} version={row['version'] or 'unknown'}")
    print("\nOptional packages:")
    for row in report["optional"]:
        print(f"  - {row['module']}: available={row['available']} version={row['version'] or 'not installed'}")
    print("\nImports:")
    for row in report["imports"]:
        suffix = "ok" if row["ok"] else row.get("error")
        print(f"  - {row['module']}: {suffix}")
    print("\nTorch backend:")
    for key, value in report["torch_backend"].items():
        print(f"  - {key}: {value}")
    if report["config_probe"].get("requested"):
        print("\nConfig probe:")
        for key, value in report["config_probe"].items():
            print(f"  - {key}: {value}")
    print("\nVerdict:", "ok" if report["ok"] else "not ready")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check core MMAction2 imports, versions, optional packages, backend availability, and optionally parse one config.")
    parser.add_argument("--probe-config", help="Optional MMAction2 config file to parse with mmengine.Config.fromfile.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of text.")
    parser.add_argument("--json-out", help="Write the same JSON report to this path.")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = make_parser().parse_args(argv)
    report = build_report(args)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
