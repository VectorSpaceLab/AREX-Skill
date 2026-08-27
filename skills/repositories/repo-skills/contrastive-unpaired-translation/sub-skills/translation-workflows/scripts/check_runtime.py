#!/usr/bin/env python3
"""Check CUT-family runtime imports and a tiny CUDA smoke test.

This helper is safe: it only imports modules, prints verified runtime facts,
and optionally allocates one tiny CUDA tensor when --check-cuda is set.

Example:
    python scripts/check_runtime.py --repo-root /path/to/checkout --check-cuda
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib.metadata import version as package_version
from pathlib import Path

REQUIRED_IMPORTS = [
    "train",
    "test",
    "options.base_options",
    "options.train_options",
    "options.test_options",
    "data.base_dataset",
    "data.unaligned_dataset",
    "data.singleimage_dataset",
    "models.base_model",
    "models.cut_model",
    "models.sincut_model",
    "models.networks",
    "util.visualizer",
    "util.html",
]
OPTIONAL_IMPORTS = [
    "models.cycle_gan_model",
    "visdom",
    "dominate",
    "GPUtil",
    "cv2",
]


def add_repo_root(repo_root: str) -> Path:
    path = Path(repo_root).resolve()
    if not path.exists():
        raise SystemExit(f"repo root does not exist: {path}")
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path


def safe_import(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {
            "ok": True,
            "module": name,
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # pragma: no cover - surfaced to user
        return {
            "ok": False,
            "module": name,
            "error": f"{type(exc).__name__}: {exc}",
        }


def safe_signature(obj) -> str | None:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None


def build_summary(repo_root: Path, check_cuda: bool) -> tuple[dict[str, object], bool]:
    failed = False
    summary: dict[str, object] = {
        "repo_root": str(repo_root),
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "packages": {},
        "required_imports": {},
        "optional_imports": {},
        "signatures": {},
        "cuda": None,
    }

    try:
        import torch
        import torchvision
    except Exception as exc:
        summary["packages"]["torch"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return summary, True

    summary["packages"]["torch"] = {
        "ok": True,
        "version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    summary["packages"]["torchvision"] = {
        "ok": True,
        "version": torchvision.__version__,
    }

    for pkg in ["visdom", "dominate", "GPUtil", "opencv-python-headless", "packaging", "fsspec", "sympy"]:
        try:
            summary["packages"][pkg] = {"ok": True, "version": package_version(pkg)}
        except Exception:
            summary["packages"][pkg] = {"ok": False}

    for name in REQUIRED_IMPORTS:
        result = safe_import(name)
        summary["required_imports"][name] = result
        if not result["ok"]:
            failed = True

    for name in OPTIONAL_IMPORTS:
        summary["optional_imports"][name] = safe_import(name)

    try:
        from data import create_dataset

        summary["signatures"]["data.create_dataset"] = safe_signature(create_dataset)
    except Exception as exc:
        summary["signatures"]["data.create_dataset"] = f"ERROR: {type(exc).__name__}: {exc}"
        failed = True

    try:
        from models import create_model

        summary["signatures"]["models.create_model"] = safe_signature(create_model)
    except Exception as exc:
        summary["signatures"]["models.create_model"] = f"ERROR: {type(exc).__name__}: {exc}"
        failed = True

    for label, module_name, attr_path in [
        ("BaseOptions.__init__", "options.base_options", "BaseOptions.__init__"),
        ("TrainOptions.__init__", "options.train_options", "TrainOptions.__init__"),
        ("TestOptions.__init__", "options.test_options", "TestOptions.__init__"),
        ("CUTModel.modify_commandline_options", "models.cut_model", "CUTModel.modify_commandline_options"),
        ("SinCUTModel.modify_commandline_options", "models.sincut_model", "SinCUTModel.modify_commandline_options"),
    ]:
        try:
            obj = importlib.import_module(module_name)
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
            summary["signatures"][label] = safe_signature(obj)
        except Exception as exc:
            summary["signatures"][label] = f"ERROR: {type(exc).__name__}: {exc}"
            failed = True

    if check_cuda:
        try:
            if not torch.cuda.is_available():
                summary["cuda"] = {"ok": False, "error": "CUDA not available"}
                failed = True
            else:
                tensor = torch.tensor([1.0], device="cuda")
                summary["cuda"] = {
                    "ok": True,
                    "device_name": torch.cuda.get_device_name(0),
                    "device_capability": list(torch.cuda.get_device_capability(0)),
                    "tensor": tensor.tolist(),
                }
        except Exception as exc:  # pragma: no cover - surfaced to user
            summary["cuda"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            failed = True
    return summary, failed


def render_human(summary: dict[str, object]) -> None:
    print(f"repo_root: {summary['repo_root']}")
    print(f"python: {summary['python']['version']} ({summary['python']['executable']})")
    for name, info in summary["packages"].items():
        if info.get("ok"):
            version = info.get("version")
            extra = []
            if name == "torch":
                extra.append(f"cuda={info.get('cuda_version')}")
                extra.append(f"available={info.get('cuda_available')}")
                extra.append(f"devices={info.get('device_count')}")
            tail = f" ({', '.join(extra)})" if extra else ""
            print(f"package {name}: {version}{tail}")
        else:
            print(f"package {name}: missing")
    print("required imports:")
    for name, info in summary["required_imports"].items():
        if info.get("ok"):
            print(f"  {name}: {info.get('file')}")
        else:
            print(f"  {name}: ERROR {info.get('error')}")
    print("optional imports:")
    for name, info in summary["optional_imports"].items():
        if info.get("ok"):
            print(f"  {name}: {info.get('file')}")
        else:
            print(f"  {name}: missing ({info.get('error')})")
    if summary.get("cuda") is not None:
        print(f"cuda smoke: {summary['cuda']}")
    print("signatures:")
    for name, sig in summary["signatures"].items():
        print(f"  {name}: {sig}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check CUT-family imports and runtime facts from a repo root.")
    parser.add_argument("--repo-root", required=True, help="Path to the checkout that contains train.py and the package modules.")
    parser.add_argument("--check-cuda", action="store_true", help="Fail if CUDA is unavailable or a tiny CUDA allocation fails.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    args = parser.parse_args(argv)

    repo_root = add_repo_root(args.repo_root)
    summary, failed = build_summary(repo_root, args.check_cuda)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        render_human(summary)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
