#!/usr/bin/env python3
"""Preflight CUDA and q8_kernels availability for advanced-control workflows.

This script is intentionally safe:
- it does not load models
- it does not import ComfyUI
- it only checks torch CUDA visibility and q8_kernels importability
"""

from __future__ import annotations

import argparse
import json


def probe_torch() -> dict:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - import failure path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    info: dict[str, object] = {
        "ok": True,
        "version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if info["cuda_available"]:
        try:
            info["device_name"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - device probe path
            info["device_name_error"] = f"{type(exc).__name__}: {exc}"
    return info


def probe_q8() -> dict:
    try:
        import q8_kernels as q8_module
        import q8_kernels.functional.ops  # noqa: F401
        import q8_kernels.integration.patch_transformer  # noqa: F401
        import q8_kernels.integration.patch_vae  # noqa: F401
    except Exception as exc:  # pragma: no cover - import failure path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "ok": True,
        "version": getattr(q8_module, "__version__", None),
        "module": getattr(q8_module, "__file__", None),
    }


def format_human(report: dict) -> str:
    torch_info = report["torch"]
    q8_info = report["q8_kernels"]
    lines = ["torch:"]
    if torch_info.get("ok"):
        lines.append(f"  version: {torch_info.get('version')}")
        lines.append(f"  cuda_version: {torch_info.get('cuda_version')}")
        lines.append(f"  cuda_available: {torch_info.get('cuda_available')}")
        lines.append(f"  device_count: {torch_info.get('device_count')}")
        if torch_info.get("cuda_available"):
            if "device_name" in torch_info:
                lines.append(f"  device_name: {torch_info.get('device_name')}")
            elif "device_name_error" in torch_info:
                lines.append(f"  device_name_error: {torch_info.get('device_name_error')}")
    else:
        lines.append(f"  error: {torch_info.get('error')}")

    lines.append("q8_kernels:")
    if q8_info.get("ok"):
        lines.append(f"  version: {q8_info.get('version')}")
    else:
        lines.append(f"  error: {q8_info.get('error')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check torch CUDA visibility and q8_kernels importability without loading any models."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when CUDA or q8_kernels is unavailable.",
    )
    args = parser.parse_args()

    report = {"torch": probe_torch(), "q8_kernels": probe_q8()}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_human(report))

    strict_ok = bool(report["torch"].get("ok")) and bool(report["torch"].get("cuda_available")) and bool(report["q8_kernels"].get("ok"))
    if args.strict and not strict_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
