#!/usr/bin/env python3
"""Safe StarVLA install/import diagnostic.

This helper does not download weights, instantiate models, start servers, run
training, or open simulator/robot connections. It only imports selected modules
and reports backend/package facts.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path
from typing import Any

MODULES = [
    "starVLA",
    "starVLA.model.tools",
    "starVLA.model.framework.base_framework",
    "starVLA.model.framework.share_tools",
    "starVLA.training.trainer_utils.trainer_tools",
    "deployment.model_server.policy_wrapper",
    "deployment.model_server.policy_norm_processor",
    "deployment.model_server.gr00t_obs_adapter",
]

DISTS = [
    "starVLA",
    "torch",
    "torchvision",
    "transformers",
    "omegaconf",
    "numpy",
    "pydantic",
    "numpydantic",
    "pyzmq",
    "websocket-client",
    "websockets",
    "accelerate",
]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check StarVLA imports and backend visibility without side effects.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional StarVLA checkout root to add to sys.path before importing. Use only for a checkout you intend to inspect.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--skip-deployment",
        action="store_true",
        help="Skip deployment.* imports when only core model/config inspection is needed.",
    )
    return parser.parse_args(argv)


def add_repo_root(repo_root: Path | None) -> str | None:
    if repo_root is None:
        return None
    root = repo_root.resolve()
    if not (root / "starVLA").exists():
        raise SystemExit(f"--repo-root does not look like a StarVLA checkout: missing {root / 'starVLA'}")
    sys.path.insert(0, str(root))
    return str(root)


def version_or_none(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "module": name, "file": getattr(module, "__file__", None), "error": None}
    except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure.
        return {"ok": False, "module": name, "file": None, "error": f"{type(exc).__name__}: {exc}"}


def torch_backend() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    info: dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if info["cuda_available"]:
        try:
            info["cuda_device_0"] = torch.cuda.get_device_name(0)
            info["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["cuda_tiny_allocation"] = True
        except Exception as exc:  # noqa: BLE001
            info["cuda_tiny_allocation"] = False
            info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return info


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

    repo_root = add_repo_root(args.repo_root)
    modules = [m for m in MODULES if not (args.skip_deployment and m.startswith("deployment."))]
    # Some StarVLA imports initialize loggers that may write warnings to stdout.
    # Keep --json stdout parseable by routing import-time chatter to stderr.
    stream_guard = contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext()
    with stream_guard:
        imports = [import_module(name) for name in modules]
        backend = torch_backend()
    result = {
        "repo_root_supplied": bool(repo_root),
        "python": sys.version.split()[0],
        "distributions": {dist: version_or_none(dist) for dist in DISTS},
        "imports": imports,
        "torch_backend": backend,
        "summary": {
            "all_imports_ok": all(item["ok"] for item in imports),
            "deployment_checked": not args.skip_deployment,
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("StarVLA install check")
        print(f"Python: {result['python']}")
        for dist, version in result["distributions"].items():
            print(f"{dist}: {version or 'not installed'}")
        print("Imports:")
        for item in imports:
            status = "OK" if item["ok"] else "FAIL"
            print(f"  {status} {item['module']}{'' if item['ok'] else ' - ' + item['error']}")
        backend = result["torch_backend"]
        if backend.get("ok"):
            print(
                "Torch backend: "
                f"torch={backend.get('version')} cuda_available={backend.get('cuda_available')} "
                f"device_count={backend.get('cuda_device_count')}"
            )
        else:
            print(f"Torch backend: FAIL - {backend.get('error')}")

    return 0 if result["summary"]["all_imports_ok"] and result["torch_backend"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
