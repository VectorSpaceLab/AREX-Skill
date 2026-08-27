#!/usr/bin/env python3
"""Safe DeepLabCut install and backend probe.

This script imports DeepLabCut, reports version/public API availability, and can
optionally probe PyTorch and launcher behavior. It does not create projects,
launch a GUI, download models, train networks, or write DeepLabCut outputs.

Examples:
  python scripts/check_deeplabcut_install.py
  python scripts/check_deeplabcut_install.py --check-torch --check-launcher
  python scripts/check_deeplabcut_install.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any

CORE_EXPORTS = [
    "create_new_project",
    "add_new_videos",
    "extract_frames",
    "check_labels",
    "create_training_dataset",
    "train_network",
    "evaluate_network",
    "analyze_videos",
    "convert_detections2tracklets",
    "stitch_tracklets",
    "video_inference_superanimal",
    "filterpredictions",
    "create_labeled_video",
    "triangulate",
    "export_model",
]


@dataclass
class ProbeResult:
    status: str
    python: str
    deeplabcut_imported: bool
    deeplabcut_version: str | None
    missing_exports: list[str]
    optional: dict[str, Any]
    warnings: list[str]
    errors: list[str]


def probe_deeplabcut() -> tuple[Any | None, str | None, list[str], list[str]]:
    warnings: list[str] = []
    try:
        dlc = importlib.import_module("deeplabcut")
    except Exception as exc:  # noqa: BLE001
        return None, None, CORE_EXPORTS, [f"DeepLabCut import failed: {exc}"]

    version = getattr(dlc, "__version__", None)
    missing = [name for name in CORE_EXPORTS if not hasattr(dlc, name)]
    if missing:
        warnings.append("Some expected public exports are missing; package/API version may differ from this skill.")
    return dlc, version, missing, warnings


def probe_torch() -> dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # noqa: BLE001
        return {"imported": False, "error": str(exc)}

    info: dict[str, Any] = {
        "imported": True,
        "version": getattr(torch, "__version__", None),
        "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": False,
        "cuda_device_count": 0,
    }
    try:
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["cuda_device_count"] = int(torch.cuda.device_count())
        if info["cuda_available"]:
            info["cuda_device_0"] = torch.cuda.get_device_name(0)
            info["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["cuda_tiny_allocation"] = "ok"
    except Exception as exc:  # noqa: BLE001
        info["cuda_error"] = str(exc)
    try:
        info["mps_available"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception as exc:  # noqa: BLE001
        info["mps_error"] = str(exc)
    return info


def probe_launcher(timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"dlc_executable": shutil.which("dlc")}
    if not result["dlc_executable"]:
        result["available"] = False
        result["error"] = "No dlc executable found on PATH."
        return result
    try:
        proc = subprocess.run(
            [result["dlc_executable"], "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        result.update(
            {
                "available": True,
                "returncode": proc.returncode,
                "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
                "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
                "note": "In DeepLabCut 3.0.1, dlc invokes the GUI/lite launcher rather than the click workflow command group.",
            }
        )
    except Exception as exc:  # noqa: BLE001
        result.update({"available": True, "error": str(exc)})
    return result


def probe_click_group() -> dict[str, Any]:
    try:
        cli = importlib.import_module("deeplabcut.cli")
        main = getattr(cli, "main")
        return {"imported": True, "commands": sorted(main.commands)}
    except Exception as exc:  # noqa: BLE001
        return {"imported": False, "error": str(exc)}


def build_result(args: argparse.Namespace) -> ProbeResult:
    dlc, version, missing, messages = probe_deeplabcut()
    optional: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    if dlc is None:
        errors.extend(messages)
    else:
        warnings.extend(messages)

    if args.check_torch:
        optional["torch"] = probe_torch()
    if args.check_launcher:
        optional["launcher"] = probe_launcher(args.launcher_timeout)
        optional["deeplabcut_cli_group"] = probe_click_group()

    status = "ok" if dlc is not None and not missing else "warning"
    if dlc is None:
        status = "error"
    return ProbeResult(
        status=status,
        python=sys.version.split()[0],
        deeplabcut_imported=dlc is not None,
        deeplabcut_version=version,
        missing_exports=missing,
        optional=optional,
        warnings=warnings,
        errors=errors,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe a DeepLabCut installation.")
    parser.add_argument("--check-torch", action="store_true", help="Probe PyTorch, CUDA, and MPS availability.")
    parser.add_argument("--check-launcher", action="store_true", help="Run a bounded dlc launcher help/lite probe and inspect deeplabcut.cli.")
    parser.add_argument("--launcher-timeout", type=float, default=8.0, help="Seconds before aborting launcher probe.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable report.")
    args = parser.parse_args(argv)

    result = build_result(args)
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"status: {result.status}")
        print(f"python: {result.python}")
        print(f"deeplabcut_imported: {result.deeplabcut_imported}")
        print(f"deeplabcut_version: {result.deeplabcut_version}")
        if result.missing_exports:
            print("missing_exports: " + ", ".join(result.missing_exports))
        for key, value in result.optional.items():
            print(f"{key}: {json.dumps(value, sort_keys=True)}")
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")

    return 0 if result.status in {"ok", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
