#!/usr/bin/env python3
"""Check a StudioGAN checkout and Python runtime without running training.

This helper is intentionally read-only. It imports common StudioGAN runtime
packages, optionally verifies CUDA availability, checks a user-supplied
StudioGAN checkout for public scripts, and can run safe CLI help commands.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

DEPENDENCY_IMPORTS = {
    "torch": "torch",
    "torchvision": "torchvision",
    "yaml": "yaml",
    "h5py": "h5py",
    "numpy": "numpy",
    "PIL": "PIL",
    "scipy": "scipy",
    "sklearn": "sklearn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "tqdm": "tqdm",
    "wandb": "wandb",
    "kornia": "kornia",
    "timm": "timm",
}


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check StudioGAN runtime imports, CUDA, checkout scripts, and optional CLI help without training."
    )
    parser.add_argument("--repo-root", help="Path to a StudioGAN checkout containing src/main.py and src/evaluate.py.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if PyTorch CUDA is unavailable.")
    parser.add_argument("--run-cli-help", action="store_true", help="Run src/main.py -h and src/evaluate.py -h with PYTHONPATH=<repo>/src.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text lines.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for each help command. Default: 30.")
    return parser


def import_dependencies() -> Dict[str, str]:
    results: Dict[str, str] = {}
    for label, module_name in DEPENDENCY_IMPORTS.items():
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "ok")
            results[label] = f"ok:{version}"
        except Exception as exc:  # noqa: BLE001 - report concise diagnostic.
            results[label] = f"missing:{type(exc).__name__}:{exc}"
    return results


def check_cuda(require_cuda: bool) -> Dict[str, object]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": f"torch import failed: {exc}", "required": require_cuda}

    available = bool(torch.cuda.is_available())
    info: Dict[str, object] = {
        "status": "ok" if available or not require_cuda else "failed",
        "required": require_cuda,
        "torch": getattr(torch, "__version__", None),
        "torch_cuda": getattr(torch.version, "cuda", None),
        "cuda_available": available,
        "device_count": int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0,
    }
    if available:
        try:
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["allocation"] = "ok"
        except Exception as exc:  # noqa: BLE001
            info["status"] = "failed" if require_cuda else "warning"
            info["allocation"] = f"failed:{type(exc).__name__}:{exc}"
    return info


def normalize_repo_root(value: Optional[str]) -> Optional[Path]:
    if value is None:
        return None
    return Path(value).expanduser().resolve(strict=False)


def check_checkout(repo_root: Optional[Path]) -> Dict[str, object]:
    if repo_root is None:
        return {"status": "skipped", "reason": "--repo-root not supplied"}
    expected = ["README.md", "src/main.py", "src/evaluate.py", "src/config.py", "src/configs"]
    missing = [rel for rel in expected if not (repo_root / rel).exists()]
    return {
        "status": "ok" if not missing else "failed",
        "repo_root_supplied": True,
        "missing": missing,
    }


def run_help(repo_root: Path, script_rel: str, timeout: float) -> Dict[str, object]:
    script = repo_root / script_rel
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "-h"],
            cwd=str(repo_root),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"script": script_rel, "status": "failed", "error": "timeout"}
    return {
        "script": script_rel,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = make_parser().parse_args(argv)
    repo_root = normalize_repo_root(args.repo_root)

    result: Dict[str, object] = {
        "dependencies": import_dependencies(),
        "cuda": check_cuda(args.require_cuda),
        "checkout": check_checkout(repo_root),
        "cli_help": [],
        "notes": [
            "This helper does not train, evaluate metrics, download datasets or weights, login to W&B, or compile StyleGAN custom ops."
        ],
    }

    if args.run_cli_help:
        if repo_root is None:
            result["cli_help"] = [{"status": "failed", "error": "--repo-root is required for --run-cli-help"}]
        else:
            result["cli_help"] = [
                run_help(repo_root, "src/main.py", args.timeout),
                run_help(repo_root, "src/evaluate.py", args.timeout),
            ]

    failed = False
    for value in result["dependencies"].values():  # type: ignore[union-attr]
        if isinstance(value, str) and value.startswith("missing:"):
            failed = True
    if isinstance(result["cuda"], dict) and result["cuda"].get("status") == "failed":
        failed = True
    if isinstance(result["checkout"], dict) and result["checkout"].get("status") == "failed":
        failed = True
    for item in result.get("cli_help", []):
        if isinstance(item, dict) and item.get("status") == "failed":
            failed = True

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Dependency imports:")
        for label, status in result["dependencies"].items():  # type: ignore[union-attr]
            print(f"  {label}: {status}")
        print("CUDA:", result["cuda"])
        print("Checkout:", result["checkout"])
        if args.run_cli_help:
            print("CLI help:", result["cli_help"])
        for note in result["notes"]:  # type: ignore[union-attr]
            print("NOTE:", note)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
