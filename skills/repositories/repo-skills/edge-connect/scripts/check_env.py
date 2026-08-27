#!/usr/bin/env python3
"""Check whether an EdgeConnect checkout and its legacy dependencies import cleanly.

This helper is read-only. It imports the repository modules, optionally checks a
small CUDA allocation, and instantiates the example config from a provided
checkout root.

Example:
    python scripts/check_env.py --repo-root /path/to/edge-connect --cuda
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

MODULES = [
    "src.config",
    "src.dataset",
    "src.edge_connect",
    "src.loss",
    "src.metrics",
    "src.models",
    "src.networks",
    "src.utils",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a read-only EdgeConnect environment smoke check.")
    parser.add_argument("--repo-root", required=True, help="path to the EdgeConnect checkout root")
    parser.add_argument(
        "--config",
        default="config.yml.example",
        help="config file or config directory inside the checkout (default: config.yml.example)",
    )
    parser.add_argument("--cuda", action="store_true", help="require a tiny CUDA allocation if torch reports CUDA is available")
    parser.add_argument("--json", action="store_true", help="emit a JSON report instead of human-readable output")
    return parser.parse_args(argv)


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def resolve_config_path(root: Path, value: str) -> Path:
    path = resolve_path(root, value)
    if path.is_dir():
        for candidate in (path / "config.yml", path / "config.yaml", path / "config.yml.example"):
            if candidate.exists():
                return candidate.resolve()
        raise FileNotFoundError(f"no config.yml/config.yaml/config.yml.example found in {path}")
    return path


def add_repo_to_path(repo_root: Path) -> None:
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def import_modules() -> tuple[dict[str, str], dict[str, str]]:
    imported: dict[str, str] = {}
    failures: dict[str, str] = {}
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            imported[name] = getattr(module, "__file__", "<unknown>")
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures[name] = f"{type(exc).__name__}: {exc}"
    return imported, failures


def check_config(config_path: Path) -> tuple[str | None, dict[str, Any]]:
    try:
        from src.config import Config
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"{type(exc).__name__}: {exc}", {}

    try:
        cfg = Config(str(config_path))
    except TypeError as exc:
        message = str(exc)
        if "Loader" in message:
            message = f"{message} (PyYAML 6.x is too new for src.config.Config; use PyYAML<6 or patch yaml.load)"
        return message, {}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"{type(exc).__name__}: {exc}", {}

    keys = [
        "MODE",
        "MODEL",
        "MASK",
        "EDGE",
        "NMS",
        "GPU",
        "DEBUG",
        "VERBOSE",
        "INPUT_SIZE",
    ]
    values = {key: getattr(cfg, key, None) for key in keys}
    return None, values


def check_torch(cuda_required: bool) -> tuple[dict[str, Any] | None, str | None]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"

    report: dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }

    if cuda_required:
        if not torch.cuda.is_available():
            return report, "CUDA was requested but torch.cuda.is_available() is false"
        try:
            device_name = torch.cuda.get_device_name(0)
            device_capability = torch.cuda.get_device_capability(0)
            tensor = torch.empty((1,), device="cuda")
            report.update(
                {
                    "cuda_device_name": device_name,
                    "cuda_device_capability": device_capability,
                    "cuda_allocation": tuple(tensor.shape),
                }
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            return report, f"{type(exc).__name__}: {exc}"

    return report, None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"error: repo root does not exist: {repo_root}", file=sys.stderr)
        return 1

    add_repo_to_path(repo_root)

    try:
        config_path = resolve_config_path(repo_root, args.config)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    imported, failures = import_modules()
    config_error, config_values = check_config(config_path)
    torch_report, torch_error = check_torch(args.cuda)

    report = {
        "repo_root": str(repo_root),
        "config_path": str(config_path),
        "imports": imported,
        "import_failures": failures,
        "config_values": config_values,
        "torch": torch_report,
        "config_error": config_error,
        "torch_error": torch_error,
        "cuda_requested": bool(args.cuda),
    }

    ok = not failures and config_error is None and torch_error is None

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("EdgeConnect environment check")
        print(f"repo_root: {repo_root}")
        print(f"config_path: {config_path}")
        for name, origin in imported.items():
            print(f"[OK] import {name} -> {origin}")
        for name, error in failures.items():
            print(f"[ERR] import {name} -> {error}")
        if config_error is None:
            print("[OK] config instantiation")
            if config_values:
                print("config values:")
                for key, value in config_values.items():
                    print(f"  {key}: {value}")
        else:
            print(f"[ERR] config instantiation -> {config_error}")
        if torch_report is not None:
            print("torch report:")
            for key, value in torch_report.items():
                print(f"  {key}: {value}")
        if torch_error is not None:
            print(f"[ERR] torch smoke -> {torch_error}")
        print("status: ok" if ok else "status: failed")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
