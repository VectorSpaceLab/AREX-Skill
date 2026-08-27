#!/usr/bin/env python3
"""Safe VLMEvalKit installation and API-surface diagnostic.

This script imports selected public objects, prints signatures, and optionally
checks that `vlmutil` can list a small dataset group. It does not download
datasets, call providers, start services, or run model inference.
"""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any


def capture(label: str, func) -> dict[str, Any]:
    try:
        value = func()
        return {"label": label, "ok": True, "value": value}
    except Exception as err:  # pragma: no cover - diagnostic path
        return {"label": label, "ok": False, "error": f"{type(err).__name__}: {err}"}


def module_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(capture("distribution_version", lambda: metadata.version("vlmeval")))

    def root_version() -> str:
        import vlmeval

        return getattr(vlmeval, "__version__", "unknown")

    checks.append(capture("vlmeval.__version__", root_version))

    def litellm_signature() -> str:
        from vlmeval.api.litellm_api import LiteLLMAPI

        return str(inspect.signature(LiteLLMAPI.__init__))

    checks.append(capture("LiteLLMAPI.__init__", litellm_signature))

    def api_pipeline_signature() -> str:
        from vlmeval.inference_api import APIEvalPipeline

        return str(inspect.signature(APIEvalPipeline.__init__))

    checks.append(capture("APIEvalPipeline.__init__", api_pipeline_signature))

    def dataset_signature() -> str:
        from vlmeval.dataset import build_dataset

        return str(inspect.signature(build_dataset))

    checks.append(capture("build_dataset", dataset_signature))

    def supported_vlm_count() -> int:
        from vlmeval.config import supported_VLM

        return len(supported_VLM)

    checks.append(capture("supported_VLM_count", supported_vlm_count))
    return checks


def vlmutil_check(timeout: int) -> dict[str, Any]:
    exe = shutil.which("vlmutil")
    if not exe:
        return {"label": "vlmutil dlist l1", "ok": False, "error": "vlmutil not found on PATH"}
    try:
        proc = subprocess.run(
            [exe, "dlist", "l1"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as err:  # pragma: no cover - diagnostic path
        return {"label": "vlmutil dlist l1", "ok": False, "error": f"{type(err).__name__}: {err}"}
    return {
        "label": "vlmutil dlist l1",
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_preview": proc.stdout[:500],
        "stderr_preview": proc.stderr[:500],
    }


def cuda_check() -> dict[str, Any]:
    def probe() -> dict[str, Any]:
        import torch

        out = {
            "torch": getattr(torch, "__version__", "unknown"),
            "torch_cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            out["device0"] = torch.cuda.get_device_name(0)
            out["capability0"] = torch.cuda.get_device_capability(0)
        return out

    return capture("torch_cuda", probe)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a VLMEvalKit installation without running benchmarks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    parser.add_argument("--skip-vlmutil", action="store_true", help="Skip console entry-point check.")
    parser.add_argument("--cuda", action="store_true", help="Probe torch CUDA availability with no allocation.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for console checks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = module_checks()
    if not args.skip_vlmutil:
        checks.append(vlmutil_check(args.timeout))
    if args.cuda:
        checks.append(cuda_check())

    if args.json:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
    else:
        for item in checks:
            status = "ok" if item.get("ok") else "FAIL"
            print(f"[{status}] {item['label']}")
            if item.get("ok"):
                value = item.get("value", item.get("stdout_preview", ""))
                if value not in (None, ""):
                    print(f"  {value}")
            else:
                print(f"  {item.get('error') or item.get('stderr_preview')}")

    return 0 if all(item.get("ok") for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
