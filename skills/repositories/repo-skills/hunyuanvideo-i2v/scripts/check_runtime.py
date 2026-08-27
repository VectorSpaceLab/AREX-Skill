#!/usr/bin/env python3
"""Check HunyuanVideo-I2V runtime imports and optional CUDA backends.

Safe by default: only imports modules, inspects versions/signatures, and can
perform a tiny CUDA tensor allocation when requested.

Example (run from the real checkout root):
  python "$SKILL_ROOT/scripts/check_runtime.py" --repo-root "$CHECKOUT_ROOT" --check-imports --check-decord --check-omegaconf
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


def _add_repo_root(repo_root: str | None) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).resolve()))


def _probe_module(name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"module": name}
    try:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            module = importlib.import_module(name)
        result["ok"] = True
        result["version"] = getattr(module, "__version__", None)
        result["file"] = getattr(module, "__file__", None)
        if stdout.getvalue().strip():
            result["import_stdout"] = stdout.getvalue().strip()[-500:]
        if stderr.getvalue().strip():
            result["import_stderr"] = stderr.getvalue().strip()[-500:]
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["ok"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HunyuanVideo-I2V runtime imports and CUDA smoke state")
    parser.add_argument("--repo-root", default=None, help="Path to the HunyuanVideo-I2V checkout to add to PYTHONPATH")
    parser.add_argument("--check-cuda", action="store_true", help="Allocate a tiny CUDA tensor if torch reports CUDA support")
    parser.add_argument("--check-flash-attn", action="store_true", help="Import flash_attn")
    parser.add_argument("--check-deepspeed", action="store_true", help="Import deepspeed")
    parser.add_argument("--check-decord", action="store_true", help="Import decord (required by HyVAE extraction)")
    parser.add_argument("--check-omegaconf", action="store_true", help="Import omegaconf (required by HyVAE extraction)")
    parser.add_argument("--check-imports", action="store_true", help="Import the HunyuanVideo-I2V package modules")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    _add_repo_root(args.repo_root)

    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    # Core package probes.
    if args.check_imports or not (args.check_flash_attn or args.check_deepspeed or args.check_decord or args.check_omegaconf or args.check_cuda):
        for mod in [
            "hyvideo",
            "hyvideo.config",
            "hyvideo.inference",
            "hyvideo.modules",
            "hyvideo.vae",
        ]:
            item = _probe_module(mod)
            checks.append(item)
            if not item.get("ok"):
                failures.append(f"{mod}: {item['error']}")

    torch_item = _probe_module("torch")
    checks.append(torch_item)
    if not torch_item.get("ok"):
        failures.append(f"torch: {torch_item['error']}")
    else:
        import torch

        checks.append(
            {
                "module": "torch.cuda",
                "ok": True,
                "version": getattr(torch.version, "cuda", None),
                "available": torch.cuda.is_available(),
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "device_name_0": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            }
        )
        if args.check_cuda:
            try:
                x = torch.ones(1, device="cuda")
                checks.append({"module": "cuda-smoke", "ok": True, "value": float(x.sum().item())})
            except Exception as exc:  # pragma: no cover - diagnostic path
                checks.append({"module": "cuda-smoke", "ok": False, "error": f"{type(exc).__name__}: {exc}"})
                failures.append(f"cuda-smoke: {type(exc).__name__}: {exc}")

    if args.check_flash_attn:
        item = _probe_module("flash_attn")
        checks.append(item)
        if not item.get("ok"):
            failures.append(f"flash_attn: {item['error']}")

    if args.check_deepspeed:
        item = _probe_module("deepspeed")
        checks.append(item)
        if not item.get("ok"):
            failures.append(f"deepspeed: {item['error']}")

    if args.check_decord:
        item = _probe_module("decord")
        checks.append(item)
        if not item.get("ok"):
            failures.append(f"decord: {item['error']}")

    if args.check_omegaconf:
        item = _probe_module("omegaconf")
        checks.append(item)
        if not item.get("ok"):
            failures.append(f"omegaconf: {item['error']}")

    summary = {"ok": not failures, "checks": checks, "failures": failures}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for item in checks:
            if item.get("ok"):
                print(f"OK {item['module']} {item.get('version', '')}".rstrip())
            else:
                print(f"FAIL {item['module']}: {item['error']}")
        if failures:
            print("Failures:")
            for failure in failures:
                print(f"- {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
