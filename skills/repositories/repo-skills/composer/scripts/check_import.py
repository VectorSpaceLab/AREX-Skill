#!/usr/bin/env python3
"""Safe Composer import/backend probe for agents using this repo skill."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that Composer and PyTorch import in the current Python.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--show-modules", action="store_true", help="Import key Composer submodules and report them.")
    args = parser.parse_args()

    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "composer_import_ok": False,
        "torch_import_ok": False,
    }

    try:
        import composer
        result["composer_import_ok"] = True
        result["composer_version"] = getattr(composer, "__version__", "unknown")
        try:
            result["mosaicml_distribution_version"] = metadata.version("mosaicml")
        except metadata.PackageNotFoundError:
            result["mosaicml_distribution_version"] = "not-installed"
        from composer import Trainer, Time
        result["trainer_import"] = Trainer.__name__
        result["time_parse_2ba"] = str(Time.from_timestring("2ba"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["composer_error"] = f"{type(exc).__name__}: {exc}"

    try:
        import torch
        result["torch_import_ok"] = True
        result["torch_version"] = torch.__version__
        result["cuda_available"] = bool(torch.cuda.is_available())
        result["cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
        if torch.cuda.is_available():
            result["cuda_device_0"] = torch.cuda.get_device_name(0)
            result["cuda_capability_0"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
            torch.empty((1,), device="cuda")
            result["cuda_allocation"] = "passed"
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["torch_error"] = f"{type(exc).__name__}: {exc}"

    if args.show_modules and result.get("composer_import_ok"):
        modules = [
            "composer.trainer",
            "composer.models",
            "composer.algorithms",
            "composer.functional",
            "composer.callbacks",
            "composer.loggers",
            "composer.profiler",
            "composer.distributed",
            "composer.utils",
        ]
        imported: dict[str, str] = {}
        for name in modules:
            try:
                importlib.import_module(name)
                imported[name] = "ok"
            except Exception as exc:  # pragma: no cover - diagnostic path
                imported[name] = f"{type(exc).__name__}: {exc}"
        result["modules"] = imported

    ok = bool(result.get("composer_import_ok")) and bool(result.get("torch_import_ok"))
    if args.require_cuda and not result.get("cuda_available"):
        result["required_cuda"] = "missing"
        ok = False

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
