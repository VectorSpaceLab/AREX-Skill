#!/usr/bin/env python3
"""Non-invasive SpeechRecognition environment probe.

Checks package metadata, import wiring, CLI help, Vosk model presence, and
optional dependency groups. It never downloads models, runs the microphone demo,
or validates cloud authentication.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any

MIN_PYTHON = (3, 10)

OPTIONAL_GROUPS: dict[str, dict[str, Any]] = {
    "cli-help-support": {
        "extra": None,
        "modules": ["tqdm"],
        "install": "python -m pip install tqdm",
        "purpose": "Required by the 3.17.0 sprc CLI import path, although not declared as an official extra.",
    },
    "audio": {
        "extra": "audio",
        "modules": ["pyaudio"],
        "install": 'python -m pip install "SpeechRecognition[audio]"',
        "purpose": "Microphone capture via PyAudio and host PortAudio.",
    },
    "pocketsphinx": {
        "extra": "pocketsphinx",
        "modules": ["pocketsphinx"],
        "install": 'python -m pip install "SpeechRecognition[pocketsphinx]"',
        "purpose": "Offline CMU PocketSphinx recognizer.",
    },
    "google-cloud": {
        "extra": "google-cloud",
        "modules": ["google.cloud.speech"],
        "install": 'python -m pip install "SpeechRecognition[google-cloud]"',
        "purpose": "Google Cloud Speech-to-Text V1 SDK; authentication is not checked.",
    },
    "whisper-local": {
        "extra": "whisper-local",
        "modules": ["whisper", "soundfile"],
        "install": 'python -m pip install "SpeechRecognition[whisper-local]"',
        "purpose": "Local OpenAI Whisper adapter; model weights are not loaded or downloaded.",
    },
    "faster-whisper": {
        "extra": "faster-whisper",
        "modules": ["faster_whisper", "soundfile"],
        "install": 'python -m pip install "SpeechRecognition[faster-whisper]"',
        "purpose": "Local Faster-Whisper adapter; model weights are not loaded or downloaded.",
    },
    "openai": {
        "extra": "openai",
        "modules": ["openai", "httpx"],
        "install": 'python -m pip install "SpeechRecognition[openai]"',
        "purpose": "OpenAI or OpenAI-compatible transcription API SDK; authentication is not checked.",
    },
    "groq": {
        "extra": "groq",
        "modules": ["groq", "httpx"],
        "install": 'python -m pip install "SpeechRecognition[groq]"',
        "purpose": "Groq Whisper API SDK; authentication is not checked.",
    },
    "cohere-api": {
        "extra": "cohere-api",
        "modules": ["cohere"],
        "install": 'python -m pip install "SpeechRecognition[cohere-api]"',
        "purpose": "Cohere Transcribe SDK; authentication is not checked.",
    },
    "assemblyai": {
        "extra": "assemblyai",
        "modules": ["requests"],
        "install": 'python -m pip install "SpeechRecognition[assemblyai]"',
        "purpose": "AssemblyAI legacy method HTTP dependency; service authentication is not checked.",
    },
    "vosk": {
        "extra": "vosk",
        "modules": ["vosk"],
        "install": 'python -m pip install "SpeechRecognition[vosk]"',
        "purpose": "Vosk Python package; model directory is checked separately and never downloaded.",
    },
    "audio-split": {
        "extra": "audio-split",
        "modules": ["librosa", "numpy"],
        "install": 'python -m pip install "SpeechRecognition[audio-split]"',
        "purpose": "Silence-aware AudioData splitting.",
    },
    "dev": {
        "extra": "dev",
        "modules": ["pytest", "pytest_randomly", "respx", "numpy", "pytest_httpserver", "mypy"],
        "install": 'python -m pip install "SpeechRecognition[dev]"',
        "purpose": "Repository maintainer tests and type checks; not needed for normal use.",
    },
}


def _safe_find_spec(module_name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:  # namespace-package parent failures are reported here
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "found" if spec else "missing"}


def _safe_import(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    result: dict[str, Any] = {"status": "imported"}
    if isinstance(version, str):
        result["version"] = version
    return result


def _package_metadata() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        dist_version = metadata.version("SpeechRecognition")
        meta = metadata.metadata("SpeechRecognition")
    except metadata.PackageNotFoundError as exc:
        result["status"] = "missing"
        result["error"] = f"PackageNotFoundError: {exc}"
        return result
    except Exception as exc:
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result.update(
        {
            "status": "found",
            "distribution": "SpeechRecognition",
            "version": dist_version,
            "requires_python": meta.get("Requires-Python"),
            "requires_dist": meta.get_all("Requires-Dist") or [],
        }
    )
    return result


def _probe_package(show_paths: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"metadata": _package_metadata()}
    try:
        import speech_recognition as sr
    except Exception as exc:
        result["import"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        return result

    recognizer = sr.Recognizer()
    methods = sorted(name for name in dir(recognizer) if name.startswith("recognize_"))
    pkg_file = getattr(sr, "__file__", None)
    pkg_dir = Path(pkg_file).resolve().parent if pkg_file else None
    vosk_dir = pkg_dir / "models" / "vosk" if pkg_dir else None

    result["import"] = {
        "status": "ok",
        "module": "speech_recognition",
        "module_version_attr": getattr(sr, "__version__", None),
        "recognizer_methods": methods,
    }
    if pkg_dir is not None:
        result["vosk_model"] = {
            "expected_location": "speech_recognition/models/vosk inside the installed package",
            "exists": bool(vosk_dir and vosk_dir.exists()),
            "entry_count": len(list(vosk_dir.iterdir())) if vosk_dir and vosk_dir.exists() else 0,
        }
        if show_paths:
            result["import"]["module_file"] = str(pkg_file)
            result["vosk_model"]["path"] = str(vosk_dir)
    return result


def _resolve_sprc() -> str | None:
    """Find sprc on PATH or beside the running Python executable."""
    path_match = shutil.which("sprc")
    if path_match:
        return path_match
    python_dir = Path(sys.executable).resolve().parent
    candidates = [python_dir / "sprc", python_dir / "sprc.exe"]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _run_help(argv: list[str], timeout: float, show_paths: bool = False) -> dict[str, Any]:
    exe = argv[0]
    if exe == "sprc":
        sprc_path = _resolve_sprc()
        if sprc_path is None:
            return {"status": "missing-executable", "argv": argv}
        argv = [sprc_path, *argv[1:]]

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        completed = subprocess.run(
            argv,
            cwd=tempfile.gettempdir(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        public_argv = ["sprc" if Path(argv[0]).name == "sprc" else argv[0], *argv[1:]]
        return {"status": "timeout", "argv": public_argv, "error": str(exc)}
    except Exception as exc:
        public_argv = ["sprc" if Path(argv[0]).name == "sprc" else argv[0], *argv[1:]]
        return {"status": "error", "argv": public_argv, "error": f"{type(exc).__name__}: {exc}"}

    public_argv = ["sprc" if Path(argv[0]).name == "sprc" else argv[0], *argv[1:]]
    result: dict[str, Any] = {
        "status": "ok" if completed.returncode == 0 else "failed",
        "argv": public_argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout[:4000],
        "stderr": completed.stderr[:4000],
    }
    if show_paths:
        result["resolved_argv0"] = argv[0]
    return result


def _probe_cli(timeout: float, show_paths: bool = False) -> dict[str, Any]:
    sprc_path = _resolve_sprc()
    result: dict[str, Any] = {
        "sprc_available": sprc_path is not None,
        "commands": {},
        "interactive_demo": {
            "command": f"{Path(sys.executable).name} -m speech_recognition",
            "status": "not-run",
            "reason": "interactive microphone demo; can block and can call a network recognizer",
        },
    }
    if show_paths and sprc_path:
        result["sprc_path"] = sprc_path

    commands = {
        "sprc --help": ["sprc", "--help"],
        "sprc download --help": ["sprc", "download", "--help"],
        "sprc download vosk --help": ["sprc", "download", "vosk", "--help"],
        "python -m speech_recognition.cli --help": [sys.executable, "-m", "speech_recognition.cli", "--help"],
        "python -m speech_recognition.cli download vosk --help": [
            sys.executable,
            "-m",
            "speech_recognition.cli",
            "download",
            "vosk",
            "--help",
        ],
    }
    for label, argv in commands.items():
        result["commands"][label] = _run_help(argv, timeout=timeout, show_paths=show_paths)
    return result


def _probe_optional(import_optional: bool = False) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for group, info in OPTIONAL_GROUPS.items():
        module_results = {}
        for module_name in info["modules"]:
            module_results[module_name] = (
                _safe_import(module_name) if import_optional else _safe_find_spec(module_name)
            )
        present = all(value["status"] in {"found", "imported"} for value in module_results.values())
        groups[group] = {
            "extra": info["extra"],
            "install": info["install"],
            "purpose": info["purpose"],
            "status": "available" if present else "incomplete",
            "modules": module_results,
        }
    return groups


def _collect(args: argparse.Namespace) -> dict[str, Any]:
    python_ok = sys.version_info >= MIN_PYTHON
    data: dict[str, Any] = {
        "tool": "check_speech_recognition_env.py",
        "non_invasive": True,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "meets_minimum_3_10": python_ok,
        },
        "package": _probe_package(show_paths=args.show_paths),
        "optional_groups": _probe_optional(import_optional=not args.find_spec_only),
    }
    if not args.skip_cli:
        data["cli"] = _probe_cli(timeout=args.timeout, show_paths=args.show_paths)
    else:
        data["cli"] = {"status": "skipped"}
    data["warnings"] = _warnings(data)
    return data


def _warnings(data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not data["python"]["meets_minimum_3_10"]:
        warnings.append("Python is older than SpeechRecognition's >=3.10 requirement.")

    package_import = data.get("package", {}).get("import", {})
    if package_import.get("status") != "ok":
        error = package_import.get("error", "unknown import failure")
        warnings.append(f"speech_recognition import failed: {error}")
        if "No module named 'aifc'" in error or "No module named 'audioop'" in error:
            warnings.append(
                "On Python 3.13+, install through package metadata so standard-aifc and audioop-lts are installed."
            )

    cli = data.get("cli", {})
    for label, result in cli.get("commands", {}).items():
        if result.get("status") not in {"ok"}:
            stderr = result.get("stderr", "") or result.get("error", "")
            warnings.append(f"CLI check failed for {label}: {result.get('status')}")
            if "No module named 'tqdm'" in stderr:
                warnings.append("Install tqdm in this environment; SpeechRecognition 3.17.0 CLI imports it unconditionally.")
            if "No module named 'aifc'" in stderr or "No module named 'audioop'" in stderr:
                warnings.append(
                    "CLI import hit Python 3.13+ compatibility modules; reinstall SpeechRecognition through package metadata."
                )

    vosk_model = data.get("package", {}).get("vosk_model", {})
    optional_vosk = data.get("optional_groups", {}).get("vosk", {})
    if optional_vosk.get("status") == "available" and not vosk_model.get("exists", False):
        warnings.append("The vosk module is available, but the package Vosk model directory is missing; run sprc download vosk after approving side effects.")

    return warnings


def _print_human(data: dict[str, Any]) -> None:
    print("SpeechRecognition environment check")
    print("===================================")
    py = data["python"]
    print(f"Python: {py['version']} ({'OK' if py['meets_minimum_3_10'] else 'too old for >=3.10'})")

    meta = data.get("package", {}).get("metadata", {})
    if meta.get("status") == "found":
        print(f"Distribution: {meta.get('distribution')} {meta.get('version')} (Requires-Python: {meta.get('requires_python')})")
    else:
        print(f"Distribution: {meta.get('status', 'unknown')} {meta.get('error', '')}")

    imp = data.get("package", {}).get("import", {})
    if imp.get("status") == "ok":
        methods = imp.get("recognizer_methods", [])
        print(f"Import: speech_recognition OK; {len(methods)} recognize_* methods wired")
        if methods:
            print("Methods: " + ", ".join(methods))
    else:
        print(f"Import: {imp.get('status', 'unknown')} {imp.get('error', '')}")

    vosk = data.get("package", {}).get("vosk_model", {})
    if vosk:
        state = "present" if vosk.get("exists") else "missing"
        print(f"Vosk model directory: {state} ({vosk.get('expected_location')})")

    cli = data.get("cli", {})
    if cli.get("status") == "skipped":
        print("CLI: skipped")
    elif cli:
        print(f"sprc executable: {'found' if cli.get('sprc_available') else 'missing'}")
        for label, result in cli.get("commands", {}).items():
            print(f"CLI help: {label}: {result.get('status')} (exit {result.get('returncode', 'n/a')})")

    print("\nOptional dependency groups")
    for group, info in data.get("optional_groups", {}).items():
        missing = [name for name, value in info["modules"].items() if value["status"] not in {"found", "imported"}]
        if missing:
            print(f"- {group}: incomplete; missing/error modules: {', '.join(missing)}; install: {info['install']}")
        else:
            print(f"- {group}: available")

    warnings = data.get("warnings", [])
    if warnings:
        print("\nWarnings")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nWarnings: none")

    print("\nNo models were downloaded, no microphone demo was run, and no authentication was checked.")


def _should_fail(data: dict[str, Any], args: argparse.Namespace) -> bool:
    if not data["python"]["meets_minimum_3_10"]:
        return True
    if data.get("package", {}).get("import", {}).get("status") != "ok":
        return True
    if args.require_cli:
        for result in data.get("cli", {}).get("commands", {}).values():
            if result.get("status") != "ok":
                return True
    for group in args.require_extra:
        info = data.get("optional_groups", {}).get(group)
        if info is None or info.get("status") != "available":
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--show-paths", action="store_true", help="include local resolved paths in output")
    parser.add_argument("--skip-cli", action="store_true", help="skip sprc/module CLI help probes")
    parser.add_argument("--require-cli", action="store_true", help="exit nonzero if CLI help probes fail")
    parser.add_argument(
        "--require-extra",
        action="append",
        default=[],
        choices=sorted(OPTIONAL_GROUPS),
        help="require an optional group to be available; may be repeated",
    )
    parser.add_argument(
        "--find-spec-only",
        action="store_true",
        help="use importlib.find_spec for optional modules instead of importing them; default imports optional modules but does not download models or check authentication",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds for each CLI help command")
    args = parser.parse_args(argv)

    data = _collect(args)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        _print_human(data)
    return 1 if _should_fail(data, args) else 0


if __name__ == "__main__":
    raise SystemExit(main())
