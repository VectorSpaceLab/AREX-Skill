#!/usr/bin/env python3
"""No-download TorchVision installation and API smoke check."""

from __future__ import annotations

import argparse
import importlib
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result = {"ok": False, "imports": {}, "checks": {}, "errors": []}

    try:
        import torch
        import torchvision
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["errors"].append(f"import torch/torchvision failed: {type(exc).__name__}: {exc}")
        print_result(result, args.json)
        return 1

    result["torch"] = getattr(torch, "__version__", "unknown")
    result["torchvision"] = getattr(torchvision, "__version__", "unknown")
    result["cuda_available"] = bool(torch.cuda.is_available())
    result["has_ops"] = bool(torchvision.extension._has_ops())

    for module_name in [
        "torchvision.models",
        "torchvision.transforms",
        "torchvision.transforms.v2",
        "torchvision.tv_tensors",
        "torchvision.datasets",
        "torchvision.io",
        "torchvision.ops",
        "torchvision.utils",
    ]:
        try:
            importlib.import_module(module_name)
            result["imports"][module_name] = "ok"
        except Exception as exc:  # pragma: no cover - diagnostic path
            result["imports"][module_name] = f"failed: {type(exc).__name__}: {exc}"
            result["errors"].append(f"{module_name}: {type(exc).__name__}: {exc}")

    try:
        from torchvision import models

        result["checks"]["models_list_sample"] = models.list_models()[:5]
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["errors"].append(f"list_models failed: {type(exc).__name__}: {exc}")

    try:
        import torch
        from torchvision.transforms import v2

        image = torch.zeros((3, 8, 8), dtype=torch.uint8)
        transformed = v2.Compose([v2.ToDtype(torch.float32, scale=True)])(image)
        result["checks"]["v2_dtype"] = str(transformed.dtype)
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["errors"].append(f"v2 transform smoke failed: {type(exc).__name__}: {exc}")

    result["ok"] = not result["errors"]
    print_result(result, args.json)
    return 0 if result["ok"] else 1


def print_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"torch={result.get('torch', 'unavailable')}")
    print(f"torchvision={result.get('torchvision', 'unavailable')}")
    print(f"cuda_available={result.get('cuda_available', 'unknown')}")
    print(f"has_ops={result.get('has_ops', 'unknown')}")
    for module_name, status in result.get("imports", {}).items():
        print(f"{module_name}: {status}")
    for check_name, value in result.get("checks", {}).items():
        print(f"{check_name}: {value}")
    if result.get("errors"):
        print("errors:")
        for error in result["errors"]:
            print(f"- {error}")


if __name__ == "__main__":
    raise SystemExit(main())
