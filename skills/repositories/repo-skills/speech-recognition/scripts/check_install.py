#!/usr/bin/env python3
"""Check a SpeechRecognition installation without network, microphone, or model downloads."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

OPTIONAL_MODULES = {
    "audio": ["pyaudio"],
    "pocketsphinx": ["pocketsphinx"],
    "google-cloud": ["google.cloud.speech"],
    "vosk": ["vosk"],
    "whisper-local": ["whisper", "soundfile"],
    "faster-whisper": ["faster_whisper", "soundfile"],
    "openai": ["openai", "httpx"],
    "groq": ["groq", "httpx"],
    "cohere-api": ["cohere"],
    "assemblyai": ["requests"],
    "audio-split": ["librosa", "numpy"],
    "cli-help-support": ["tqdm"],
}


def find_module(name: str) -> str:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # noqa: BLE001
        return f"error: {type(exc).__name__}: {exc}"
    return "found" if spec else "missing"


def run_help(command: list[str], timeout: float) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"status": "missing-command", "command": command[0]}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": command}
    return {
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
    }


def build_report(timeout: float) -> dict[str, Any]:
    report: dict[str, Any] = {"python": sys.version.split()[0]}
    try:
        report["distribution"] = {
            "name": "SpeechRecognition",
            "version": metadata.version("SpeechRecognition"),
            "requires_python": metadata.metadata("SpeechRecognition").get("Requires-Python"),
        }
    except Exception as exc:  # noqa: BLE001
        report["distribution"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        import speech_recognition as sr
    except Exception as exc:  # noqa: BLE001
        report["import"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        return report

    recognizer = sr.Recognizer()
    methods = sorted(m for m in dir(recognizer) if m.startswith("recognize_"))
    report["import"] = {
        "status": "ok",
        "module": "speech_recognition",
        "version_attr": getattr(sr, "__version__", None),
        "recognizer_methods": methods,
    }

    try:
        from speech_recognition.audio import get_flac_converter
        report["flac_converter"] = "available" if get_flac_converter() else "missing"
    except Exception as exc:  # noqa: BLE001
        report["flac_converter"] = f"error: {type(exc).__name__}: {exc}"

    pkg_dir = Path(getattr(sr, "__file__", "")).resolve().parent if getattr(sr, "__file__", None) else None
    if pkg_dir:
        vosk_dir = pkg_dir / "models" / "vosk"
        report["vosk_model"] = {
            "expected_location": "speech_recognition/models/vosk inside the installed package",
            "exists": vosk_dir.exists(),
            "entry_count": len(list(vosk_dir.iterdir())) if vosk_dir.exists() else 0,
        }

    report["optional_modules"] = {group: {module: find_module(module) for module in modules} for group, modules in OPTIONAL_MODULES.items()}
    report["cli"] = {
        "sprc_on_path": bool(shutil.which("sprc")),
        "sprc_help": run_help(["sprc", "--help"], timeout) if shutil.which("sprc") else {"status": "missing-command"},
        "module_help": run_help([sys.executable, "-m", "speech_recognition.cli", "--help"], timeout),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--require-cli", action="store_true", help="exit nonzero if CLI help fails")
    parser.add_argument("--timeout", type=float, default=10.0, help="CLI help timeout in seconds")
    args = parser.parse_args(argv)

    report = build_report(args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"SpeechRecognition distribution: {report.get('distribution')}")
        print(f"Import: {report.get('import')}")
        print(f"FLAC converter: {report.get('flac_converter')}")
        print(f"CLI: {report.get('cli')}")
        print("Optional groups:")
        for group, modules in report.get("optional_modules", {}).items():
            print(f"  {group}: {modules}")

    if report.get("import", {}).get("status") != "ok":
        return 2
    if args.require_cli:
        cli = report.get("cli", {})
        if cli.get("module_help", {}).get("status") != "ok" or (cli.get("sprc_on_path") and cli.get("sprc_help", {}).get("status") != "ok"):
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
