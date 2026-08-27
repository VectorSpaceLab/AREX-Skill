#!/usr/bin/env python3
"""Check a face_recognition installation without using repo-local fixtures.

Examples:
    python scripts/check_install.py
    python scripts/check_install.py --skip-cli
    python scripts/check_install.py --json

The script reports importability, distribution versions, a tiny API smoke check,
and console-script help availability. It avoids printing local environment paths
so its output is safe to paste into issue/debug notes.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any


def version_of(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> tuple[bool, str | None, Any | None]:
    try:
        module = importlib.import_module(module_name)
        return True, None, module
    except SystemExit as exc:  # face_recognition.api can call quit() on model import failure.
        return False, f"import exited early ({exc!r})", None
    except BaseException as exc:  # keep diagnostics alive for import-time failures.
        return False, f"{type(exc).__name__}: {exc}", None


def explain_import_failure(module_name: str, error: str | None) -> str:
    if module_name == "dlib":
        return "Install dlib for this Python, or use conda/Docker when pip cannot build it."
    if module_name == "face_recognition_models":
        if error and "pkg_resources" in error:
            return "Install a setuptools build that still provides pkg_resources, e.g. python -m pip install 'setuptools<81'."
        return "Install or reinstall face_recognition_models in the same Python environment."
    if module_name == "face_recognition":
        return "Fix dlib and face_recognition_models imports first, then reinstall face_recognition if needed."
    return "Install the missing module in the Python environment used for the task."


def check_imports() -> dict[str, Any]:
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated.*")
    result: dict[str, Any] = {
        "versions": {
            "face_recognition": version_of("face_recognition"),
            "face_recognition_models": version_of("face_recognition_models"),
            "dlib": version_of("dlib"),
            "numpy": version_of("numpy"),
            "Pillow": version_of("Pillow"),
            "Click": version_of("Click"),
            "setuptools": version_of("setuptools"),
        },
        "imports": {},
        "ok": True,
    }

    modules_to_check = ["dlib", "face_recognition_models", "face_recognition"]
    imported_modules: dict[str, Any] = {}
    for module_name in modules_to_check:
        # Avoid face_recognition's import-time quit() noise when prerequisites already failed.
        if module_name == "face_recognition" and not all(result["imports"][m]["ok"] for m in ["dlib", "face_recognition_models"]):
            result["imports"][module_name] = {
                "ok": False,
                "error": "skipped because prerequisite import failed",
                "hint": explain_import_failure(module_name, None),
            }
            result["ok"] = False
            continue
        ok, error, module = import_status(module_name)
        result["imports"][module_name] = {"ok": ok}
        if ok:
            imported_modules[module_name] = module
        else:
            result["imports"][module_name]["error"] = error
            result["imports"][module_name]["hint"] = explain_import_failure(module_name, error)
            result["ok"] = False

    result["_modules"] = imported_modules
    return result


def api_smoke(face_recognition_module: Any | None) -> dict[str, Any]:
    if face_recognition_module is None:
        return {"ok": False, "error": "face_recognition import unavailable"}

    try:
        from PIL import Image
        import numpy as np
    except BaseException as exc:
        return {"ok": False, "error": f"dependency import failed: {type(exc).__name__}: {exc}"}

    try:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "blank.png"
            Image.new("RGB", (32, 32), color="white").save(image_path)
            image = face_recognition_module.load_image_file(str(image_path))
            locations = face_recognition_module.face_locations(image)
            landmarks = face_recognition_module.face_landmarks(image, face_locations=locations)
            encodings = face_recognition_module.face_encodings(image, known_face_locations=locations)
            distance = face_recognition_module.face_distance(np.zeros((1, 128), dtype=float), np.ones(128, dtype=float))
            matches = face_recognition_module.compare_faces(np.zeros((1, 128), dtype=float), np.ones(128, dtype=float))
        return {
            "ok": True,
            "loaded_shape": list(image.shape),
            "face_count": len(locations),
            "landmark_count": len(landmarks),
            "encoding_count": len(encodings),
            "synthetic_distance": float(distance[0]),
            "synthetic_match": bool(matches[0]),
        }
    except BaseException as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cli_help(command: str, timeout: int) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        sibling = Path(sys.executable).resolve().parent / command
        if sibling.exists():
            executable = str(sibling)
        else:
            return {
                "ok": False,
                "error": f"{command!r} not found on PATH or next to the current Python executable",
            }
    try:
        completed = subprocess.run(
            [executable, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except BaseException as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    combined = f"{completed.stdout}\n{completed.stderr}"
    return {
        "ok": completed.returncode == 0 and "Usage:" in combined,
        "returncode": completed.returncode,
        "has_usage": "Usage:" in combined,
        "first_line": next((line for line in combined.splitlines() if line.strip()), ""),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report = check_imports()
    face_module = report.pop("_modules", {}).get("face_recognition")
    if args.api_smoke:
        report["api_smoke"] = api_smoke(face_module)
        report["ok"] = report["ok"] and report["api_smoke"].get("ok", False)
    if not args.skip_cli:
        report["cli"] = {
            "face_recognition": cli_help("face_recognition", args.timeout),
            "face_detection": cli_help("face_detection", args.timeout),
        }
        report["ok"] = report["ok"] and all(item.get("ok", False) for item in report["cli"].values())
    return report


def print_human(report: dict[str, Any]) -> None:
    print(f"overall: {'ok' if report['ok'] else 'failed'}")
    print("versions:")
    for name, version in report["versions"].items():
        print(f"  {name}: {version or 'not installed'}")
    print("imports:")
    for name, item in report["imports"].items():
        if item["ok"]:
            print(f"  {name}: ok")
        else:
            print(f"  {name}: failed - {item.get('error')}")
            print(f"    hint: {item.get('hint')}")
    if "api_smoke" in report:
        smoke = report["api_smoke"]
        if smoke.get("ok"):
            print(
                "api_smoke: ok "
                f"shape={smoke['loaded_shape']} faces={smoke['face_count']} "
                f"distance={smoke['synthetic_distance']:.4f} match={smoke['synthetic_match']}"
            )
        else:
            print(f"api_smoke: failed - {smoke.get('error')}")
    if "cli" in report:
        print("cli:")
        for command, item in report["cli"].items():
            if item.get("ok"):
                print(f"  {command}: ok ({item.get('first_line')})")
            else:
                print(f"  {command}: failed - {item.get('error') or item}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cli", action="store_true", help="skip console script --help checks")
    parser.add_argument("--no-api-smoke", dest="api_smoke", action="store_false", help="skip the synthetic API smoke check")
    parser.add_argument("--timeout", type=int, default=15, help="seconds allowed for each CLI --help command")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.set_defaults(api_smoke=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
