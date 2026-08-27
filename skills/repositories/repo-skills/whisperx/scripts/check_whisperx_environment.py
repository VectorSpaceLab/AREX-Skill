#!/usr/bin/env python3
"""Safely inspect the WhisperX runtime surface.

This helper checks package importability, distribution metadata, core public
API presence, ffmpeg availability, and optional torch CUDA visibility without
loading ASR/alignment/diarization models or writing output files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from typing import Any


PUBLIC_NAMES = [
    "load_model",
    "load_audio",
    "load_align_model",
    "align",
    "assign_word_speakers",
    "setup_logging",
    "get_logger",
]


def safe_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return None, f"{type(exc).__name__}: {exc}"


def version(dist: str) -> str:
    try:
        return importlib.metadata.version(dist)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return f"unavailable ({type(exc).__name__}: {exc})"


def run_cli_help() -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "whisperx", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def build_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "package": "whisperx",
        "version": version("whisperx"),
        "python": {"executable": sys.executable, "version": sys.version},
        "import": {},
        "cli": {},
        "ffmpeg": shutil.which("ffmpeg"),
        "torch": {},
        "warnings": [],
    }

    whisperx, err = safe_import("whisperx")
    if err:
        report["warnings"].append(f"could not import whisperx: {err}")
        return report

    for name in PUBLIC_NAMES:
        obj = getattr(whisperx, name, None)
        report["import"][name] = {
            "present": obj is not None,
            "callable": callable(obj),
        }
        if obj is None:
            report["warnings"].append(f"missing public lazy API: whisperx.{name}")

    cli_code, cli_out, cli_err = run_cli_help()
    report["cli"] = {
        "help_exit_code": cli_code,
        "help_shown": "usage:" in cli_out.lower(),
        "stdout_head": cli_out.splitlines()[:8],
        "stderr_head": cli_err.splitlines()[:8],
    }

    torch_mod, err = safe_import("torch")
    if err:
        report["warnings"].append(f"could not import torch: {err}")
    else:
        cuda_available = False
        cuda_count = 0
        device_name = None
        try:
            cuda_available = bool(torch_mod.cuda.is_available())
            cuda_count = int(torch_mod.cuda.device_count()) if cuda_available else 0
            if cuda_available:
                device_name = torch_mod.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            report["warnings"].append(f"could not query CUDA: {type(exc).__name__}: {exc}")
        report["torch"] = {
            "version": getattr(torch_mod, "__version__", None),
            "cuda_available": cuda_available,
            "cuda_device_count": cuda_count,
            "cuda_device_name": device_name,
        }

    if report["ffmpeg"] is None:
        report["warnings"].append("ffmpeg executable not found")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect WhisperX runtime readiness without model execution.")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if import/CLI checks fail")
    args = parser.parse_args(argv)

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"WhisperX version: {report['version']}")
        print(f"Python: {report['python']['version'].splitlines()[0]}")
        print(f"ffmpeg: {report['ffmpeg']}")
        print("Public API presence:")
        for name, info in report["import"].items():
            print(f"  {name}: present={info['present']} callable={info['callable']}")
        print("CLI help:")
        print(f"  exit={report['cli'].get('help_exit_code')} shown={report['cli'].get('help_shown')}")
        print("Torch:")
        for key, value in report["torch"].items():
            print(f"  {key}: {value}")
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")

    if args.strict:
        if not report["import"] or not report["cli"].get("help_shown"):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
