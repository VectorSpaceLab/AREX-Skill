#!/usr/bin/env python3
"""Safe environment check for ClearerVoice-Studio workflows.

This script does not load model checkpoints, download weights, read audio, or
start training. It checks importability, signatures, optional CUDA visibility,
FFmpeg availability, and optional SpeechScore source-layout imports.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


def distribution_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def check_clearvoice() -> dict[str, Any]:
    result: dict[str, Any] = {"importable": False}
    try:
        clearvoice = importlib.import_module("clearvoice")
        ClearVoice = getattr(clearvoice, "ClearVoice")
        result.update(
            {
                "importable": True,
                "distribution_version": distribution_version("clearvoice"),
                "module_version": getattr(clearvoice, "__version__", None),
                "constructor": str(inspect.signature(ClearVoice)),
                "call": str(inspect.signature(ClearVoice.__call__)),
                "write": str(inspect.signature(ClearVoice.write)),
            }
        )
    except Exception as exc:  # keep diagnostic human-readable
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check_torch() -> dict[str, Any]:
    result: dict[str, Any] = {"importable": False}
    try:
        torch = importlib.import_module("torch")
        result.update(
            {
                "importable": True,
                "version": getattr(torch, "__version__", None),
                "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
            }
        )
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            result["cuda_device_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check_speechscore(speechscore_dir: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {"checked": speechscore_dir is not None, "importable": False}
    if speechscore_dir is None:
        result["note"] = "pass --speechscore-dir to check source-layout SpeechScore imports"
        return result
    speechscore_dir = speechscore_dir.resolve()
    if not (speechscore_dir / "speechscore.py").exists():
        result["error"] = "--speechscore-dir must contain speechscore.py"
        return result

    old_cwd = Path.cwd()
    sys.path.insert(0, str(speechscore_dir))
    try:
        os.chdir(speechscore_dir)
        module = importlib.import_module("speechscore")
        factory = getattr(module, "SpeechScore")
        scorer = factory(["SNR", "SISDR"])
        result.update(
            {
                "importable": True,
                "factory_signature": str(inspect.signature(factory)),
                "lightweight_metric_object": str(scorer),
            }
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["recovery"] = (
            "Install the repository runtime requirements; for pyworld/pkg_resources failures, "
            "use a setuptools version that still provides pkg_resources."
        )
    finally:
        try:
            sys.path.remove(str(speechscore_dir))
        except ValueError:
            pass
        os.chdir(old_cwd)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check ClearerVoice-Studio runtime prerequisites safely.")
    parser.add_argument("--speechscore-dir", type=Path, help="Optional SpeechScore component directory containing speechscore.py.")
    parser.add_argument("--json", action="store_true", help="Print JSON; default is human-readable JSON too, but compact callers can parse it.")
    args = parser.parse_args(argv)

    report = {
        "clearvoice": check_clearvoice(),
        "torch": check_torch(),
        "ffmpeg": {"available": shutil.which("ffmpeg") is not None, "path_known": bool(shutil.which("ffmpeg"))},
        "speechscore": check_speechscore(args.speechscore_dir),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["clearvoice"].get("importable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
