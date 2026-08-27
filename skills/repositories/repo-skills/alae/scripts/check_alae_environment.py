#!/usr/bin/env python3
"""Safely check an ALAE runtime environment and optional checkout imports.

This helper does not download checkpoints, start training, open a GUI, or run
metric scripts. It only imports packages/source modules and optionally allocates
a tiny CUDA tensor when torch reports CUDA availability.

Examples:
  python scripts/check_alae_environment.py --repo-root <ALAE-checkout>
  python scripts/check_alae_environment.py --repo-root <ALAE-checkout> --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


CORE_IMPORTS = [
    "torch",
    "torchvision",
    "yacs",
    "dareblopy",
    "dlutils",
]
OPTIONAL_IMPORTS = [
    "bimpy",       # interactive_demo.py GUI
    "tensorflow",  # TF1-style TFRecord prep and legacy metrics
    "dnnlib",      # legacy StyleGAN metric/principal-direction helpers
]
SAFE_SOURCE_IMPORTS = [
    "defaults",
    "launcher",
    "model",
    "net",
    "checkpointer",
    "dataloader",
    "scheduler",
    "lod_driver",
    "tracker",
    "custom_adam",
    "lreq",
    "losses",
    "registry",
    "utils",
]


def add(results: List[Dict[str, Any]], level: str, check: str, message: str, **detail: Any) -> None:
    item: Dict[str, Any] = {"level": level, "check": check, "message": message}
    item.update({key: value for key, value in detail.items() if value is not None})
    results.append(item)


def import_module(name: str):
    module = importlib.import_module(name)
    version = getattr(module, "__version__", None)
    return module, version


def check_python(results: List[Dict[str, Any]]) -> None:
    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info >= (3, 8):
        add(
            results,
            "WARN",
            "python-version",
            "ALAE's TensorFlow 1.x support workflows often require Python 3.7; core PyTorch routes may still work on newer Python.",
            version=version,
        )
    else:
        add(results, "OK", "python-version", "Python version is compatible with legacy TensorFlow 1.x package availability.", version=version)


def check_imports(results: List[Dict[str, Any]], modules: List[str], optional: bool = False) -> None:
    for name in modules:
        try:
            _, version = import_module(name)
            add(results, "OK", f"import:{name}", "module imports", version=version or "unknown")
        except Exception as exc:  # pragma: no cover - environment-dependent
            add(
                results,
                "WARN" if optional else "ERROR",
                f"import:{name}",
                "module import failed" if not optional else "optional module import failed",
                error=f"{type(exc).__name__}: {exc}",
            )


def check_torch_cuda(results: List[Dict[str, Any]], skip_cuda: bool = False) -> None:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        add(results, "ERROR", "torch-cuda", "torch is not importable", error=f"{type(exc).__name__}: {exc}")
        return

    cuda_available = False
    device_count = 0
    cuda_runtime = getattr(getattr(torch, "version", None), "cuda", None)
    try:
        cuda_available = bool(torch.cuda.is_available())
        device_count = int(torch.cuda.device_count())
    except Exception as exc:  # pragma: no cover - unusual torch failures
        add(results, "ERROR", "torch-cuda", "torch.cuda query failed", error=f"{type(exc).__name__}: {exc}")
        return

    if not cuda_available:
        add(
            results,
            "ERROR",
            "torch-cuda",
            "CUDA is not available to torch; ALAE training and generation scripts call torch.cuda directly.",
            torch_version=getattr(torch, "__version__", "unknown"),
            cuda_runtime=cuda_runtime,
            device_count=device_count,
        )
        return

    detail: Dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", "unknown"),
        "cuda_runtime": cuda_runtime,
        "device_count": device_count,
    }
    try:
        detail["device0"] = torch.cuda.get_device_name(0)
        detail["capability0"] = list(torch.cuda.get_device_capability(0))
    except Exception:
        pass

    if skip_cuda:
        add(results, "OK", "torch-cuda", "CUDA is visible to torch; tiny allocation skipped by request", **detail)
        return

    try:
        tensor = torch.empty((1,), device="cuda")
        detail["tensor_device"] = str(tensor.device)
        add(results, "OK", "torch-cuda", "CUDA is visible and a tiny tensor allocation succeeded", **detail)
    except Exception as exc:  # pragma: no cover - backend-specific
        add(results, "ERROR", "torch-cuda", "CUDA is visible but tiny tensor allocation failed", error=f"{type(exc).__name__}: {exc}", **detail)


def check_tensorflow_legacy(results: List[Dict[str, Any]]) -> None:
    try:
        tf = importlib.import_module("tensorflow")
    except Exception:
        return
    has_session = hasattr(tf, "Session")
    has_python_io = hasattr(tf, "python_io")
    if has_session and has_python_io:
        add(results, "OK", "tensorflow-1-api", "TensorFlow exposes TF1-style Session and python_io APIs", version=getattr(tf, "__version__", "unknown"))
    else:
        add(
            results,
            "WARN",
            "tensorflow-1-api",
            "TensorFlow imports but does not expose top-level TF1 APIs used by ALAE data-prep scripts",
            version=getattr(tf, "__version__", "unknown"),
            Session=has_session,
            python_io=has_python_io,
        )


def check_repo_source(results: List[Dict[str, Any]], repo_root: Path) -> None:
    if not repo_root.is_dir():
        add(results, "ERROR", "repo-root", "--repo-root is not a directory", path=str(repo_root))
        return
    if not (repo_root / "README.md").is_file() or not (repo_root / "train_alae.py").is_file():
        add(results, "WARN", "repo-root", "directory does not look like an ALAE checkout root", path=str(repo_root))
    already_on_path = str(repo_root) in sys.path or str(repo_root.resolve()) in [str(Path(p).resolve()) for p in sys.path if p]
    sys.path.insert(0, str(repo_root))
    if already_on_path or str(repo_root) in os.environ.get("PYTHONPATH", ""):
        add(results, "OK", "pythonpath", "checkout root is already on the Python import path", path=str(repo_root))
    else:
        add(results, "WARN", "pythonpath", "native ALAE subdirectory scripts need PYTHONPATH or a checkout-root working directory", path=str(repo_root))
    check_imports(results, SAFE_SOURCE_IMPORTS, optional=False)


def print_results(results: List[Dict[str, Any]], as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return
    width = max([len(item["level"]) for item in results] + [5])
    for item in results:
        detail = {key: value for key, value in item.items() if key not in {"level", "check", "message"}}
        suffix = ""
        if detail:
            suffix = " | " + json.dumps(detail, sort_keys=True)
        print("{level:<{width}} {check}: {message}{suffix}".format(width=width, suffix=suffix, **item))


def exit_code(results: List[Dict[str, Any]], strict: bool, soft: bool) -> int:
    if soft:
        return 0
    if any(item["level"] == "ERROR" for item in results):
        return 1
    if strict and any(item["level"] == "WARN" for item in results):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ALAE dependency, CUDA, TF1-style API, and optional checkout imports safely.")
    parser.add_argument("--repo-root", help="Optional ALAE checkout root for source import checks.")
    parser.add_argument("--skip-cuda", action="store_true", help="Do not allocate a tiny CUDA tensor even if torch sees CUDA.")
    parser.add_argument("--skip-source", action="store_true", help="Do not import ALAE source modules from --repo-root.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--soft", action="store_true", help="Always exit 0 after reporting findings.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    results: List[Dict[str, Any]] = []
    check_python(results)
    check_imports(results, CORE_IMPORTS, optional=False)
    check_imports(results, OPTIONAL_IMPORTS, optional=True)
    check_torch_cuda(results, skip_cuda=args.skip_cuda)
    check_tensorflow_legacy(results)
    if args.repo_root and not args.skip_source:
        check_repo_source(results, Path(args.repo_root).expanduser().resolve())
    elif not args.repo_root and not args.skip_source:
        add(results, "WARN", "repo-root", "No --repo-root supplied; source module checks were skipped")
    print_results(results, args.json)
    return exit_code(results, args.strict, args.soft)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
