#!/usr/bin/env python3
"""Safe MaaNTE dependency/backend inspection helper.

This script does not launch MaaFramework tasks or touch a game window. It only
checks importability of public dependencies and prints optional backend status.
Example:
    python scripts/check_maante_environment.py --summary
    python scripts/check_maante_environment.py --repo-root /path/to/MaaNTE
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from pathlib import Path
from typing import Any


def _status(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _import_check(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # optional deps can fail during import
        return _status(module_name, False, f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", "unknown")
    return _status(module_name, True, f"version={version}")


def _onnxruntime_check() -> dict[str, Any]:
    try:
        ort = importlib.import_module("onnxruntime")
        providers = ort.get_available_providers()
    except Exception as exc:
        return _status("onnxruntime", False, f"{type(exc).__name__}: {exc}")
    return _status("onnxruntime", True, f"version={ort.__version__}; providers={providers}")


def _maafw_check() -> dict[str, Any]:
    try:
        import maa  # noqa: F401
        from maa.agent.agent_server import AgentServer
        from maa.custom_action import CustomAction
        from maa.custom_recognition import CustomRecognition
        from maa.context import Context
    except Exception as exc:
        return _status("maafw/maa", False, f"{type(exc).__name__}: {exc}")
    required = [
        hasattr(AgentServer, "custom_action"),
        hasattr(AgentServer, "custom_recognition"),
        hasattr(CustomAction, "RunResult"),
        hasattr(CustomRecognition, "AnalyzeResult"),
        hasattr(Context, "run_task"),
        hasattr(Context, "run_recognition"),
    ]
    return _status("maafw/maa", all(required), "core binding symbols present")


def _repo_shape_check(repo_root: Path | None) -> list[dict[str, Any]]:
    if repo_root is None:
        return []
    checks = []
    for rel in [
        "assets/interface.json",
        "assets/resource/tasks",
        "assets/resource/base/pipeline",
        "agent/main.py",
        "agent/custom/action/__init__.py",
        "requirements.txt",
    ]:
        checks.append(_status(f"repo:{rel}", (repo_root / rel).exists(), "exists" if (repo_root / rel).exists() else "missing"))
    return checks


def run(repo_root: Path | None) -> dict[str, Any]:
    modules = [
        "cv2",
        "numpy",
        "PIL",
        "scipy",
        "sklearn",
        "librosa",
        "mido",
        "requests",
        "websockets",
        "scapy",
        "soundcard",
    ]
    results = [_maafw_check(), _onnxruntime_check()]
    results.extend(_import_check(name) for name in modules)
    results.extend(_repo_shape_check(repo_root))
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "results": results,
        "notes": [
            "This helper does not prove Win32 controller, DirectML, audio loopback, coordinate capture, or live game recognition behavior.",
            "A soundcard import failure on a headless Linux host usually means no PulseAudio/PipeWire service, not necessarily a MaaNTE source error.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional MaaNTE checkout to shape-check.")
    parser.add_argument("--summary", action="store_true", help="Print a compact text summary instead of JSON.")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else None
    report = run(repo_root)
    if args.summary:
        print(f"Python: {report['python']} | Platform: {report['platform']}")
        failures = 0
        for item in report["results"]:
            mark = "OK" if item["ok"] else "WARN"
            if not item["ok"]:
                failures += 1
            print(f"[{mark}] {item['name']}: {item['detail']}")
        for note in report["notes"]:
            print(f"NOTE: {note}")
        return 0 if failures == 0 else 2

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if all(item["ok"] for item in report["results"] if not item["name"].startswith("soundcard")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
