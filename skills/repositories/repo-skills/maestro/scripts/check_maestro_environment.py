#!/usr/bin/env python3
"""Check installed Maestro package imports, optional model routes, and backend visibility.

This diagnostic is safe by default: it does not download models, contact
Roboflow, read credentials, or start training. It reports import/version facts
from the Python interpreter that runs the script.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

MODEL_MODULES = {
    "common": [
        "maestro",
        "maestro.cli.main",
        "maestro.trainer.common.datasets.jsonl",
        "maestro.trainer.common.datasets.coco",
        "maestro.trainer.common.datasets.roboflow",
        "maestro.trainer.common.metrics",
    ],
    "florence-2": [
        "maestro.trainer.models.florence_2.core",
        "maestro.trainer.models.florence_2.checkpoints",
        "maestro.trainer.models.florence_2.detection",
        "maestro.trainer.models.florence_2.inference",
    ],
    "paligemma-2": [
        "maestro.trainer.models.paligemma_2.core",
        "maestro.trainer.models.paligemma_2.checkpoints",
        "maestro.trainer.models.paligemma_2.inference",
    ],
    "qwen-2-5-vl": [
        "maestro.trainer.models.qwen_2_5_vl.core",
        "maestro.trainer.models.qwen_2_5_vl.checkpoints",
        "maestro.trainer.models.qwen_2_5_vl.detection",
        "maestro.trainer.models.qwen_2_5_vl.inference",
    ],
}

DISTRIBUTIONS = [
    "maestro",
    "torch",
    "transformers",
    "peft",
    "bitsandbytes",
    "qwen-vl-utils",
    "lightning",
    "supervision",
    "evaluate",
]


def distribution_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for name in DISTRIBUTIONS:
        try:
            values[name] = version(name)
        except PackageNotFoundError:
            values[name] = None
    return values


def import_modules(groups: list[str]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for group in groups:
        for module_name in MODEL_MODULES[group]:
            try:
                importlib.import_module(module_name)
            except Exception as exc:  # pragma: no cover - depends on user's environment
                results[module_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            else:
                results[module_name] = {"ok": True}
    return results


def backend_probe(check_cuda: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"torch_imported": False}
    try:
        import torch  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - depends on user's environment
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result.update(
        {
            "torch_imported": True,
            "torch_version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
            "mps_available": bool(getattr(getattr(torch, "backends", None), "mps", None).is_available())
            if hasattr(getattr(torch, "backends", None), "mps")
            else False,
        }
    )

    if check_cuda and result["cuda_available"]:
        try:
            tensor = torch.tensor([1.0], device="cuda")
            result["cuda_tensor_smoke"] = float((tensor + 1).cpu()[0])
        except Exception as exc:  # pragma: no cover - depends on user's environment
            result["cuda_tensor_error"] = f"{type(exc).__name__}: {exc}"
    return result


def parse_models(raw: str) -> list[str]:
    if raw == "all":
        return list(MODEL_MODULES)
    selected = [part.strip() for part in raw.split(",") if part.strip()]
    invalid = [name for name in selected if name not in MODEL_MODULES]
    if invalid:
        raise argparse.ArgumentTypeError(f"unknown model group(s): {', '.join(invalid)}")
    return selected or ["common"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely check installed Maestro imports, versions, and backend visibility.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--models",
        type=parse_models,
        default=["common"],
        help="Comma-separated groups from common,florence-2,paligemma-2,qwen-2-5-vl, or all.",
    )
    parser.add_argument("--check-cuda", action="store_true", help="If CUDA is visible, run a tiny tensor allocation.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    groups = args.models
    if "common" not in groups:
        groups = ["common", *groups]

    report = {
        "python": sys.version.split()[0],
        "distributions": distribution_versions(),
        "imports": import_modules(groups),
        "backend": backend_probe(args.check_cuda),
    }
    ok = all(item.get("ok") for item in report["imports"].values()) and report["backend"].get("torch_imported", False)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Distributions:")
        for name, dist_version in report["distributions"].items():
            print(f"  {name}: {dist_version or 'not installed'}")
        print("Imports:")
        for module_name, item in report["imports"].items():
            status = "ok" if item.get("ok") else item.get("error")
            print(f"  {module_name}: {status}")
        print("Backend:")
        for key, value in report["backend"].items():
            print(f"  {key}: {value}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
