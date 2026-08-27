#!/usr/bin/env python3
"""Safe MOSS-TTS environment diagnostic.

This helper performs metadata/import/optional-dependency checks without
loading models, downloading weights, starting services, or importing heavy
modules unless requested by name. It can optionally add a user's MOSS-TTS
checkout to sys.path to diagnose the current package exposure caveat.

Examples:
  python scripts/check_moss_tts_environment.py --json
  python scripts/check_moss_tts_environment.py --repo-root ./MOSS-TTS --check-optional torch transformers
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_IMPORTS = [
    "moss_tts_delay.llama_cpp.pipeline",
    "moss_tts_delay.tts_robust_normalizer_single_script",
]
OPTIONAL_IMPORTS = [
    "torch",
    "transformers",
    "torchaudio",
    "torchcodec",
    "flash_attn",
    "onnxruntime",
    "tensorrt",
    "fastapi",
    "gradio",
    "diffusers",
]


def module_status(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report real symptom
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(mod, "__version__", None)
    path = getattr(mod, "__file__", None)
    result: dict[str, Any] = {"name": name, "ok": True}
    if version:
        result["version"] = str(version)
    if path:
        result["module_file"] = str(path)
    return result


def distribution_status(name: str) -> dict[str, Any]:
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        return {"name": name, "ok": False, "error": "PackageNotFoundError"}
    return {"name": name, "ok": True, "version": version}


def command_help_status(command: str) -> dict[str, Any]:
    exe = shutil.which(command)
    if exe is None:
        return {"command": command, "ok": False, "error": "not found on PATH"}
    try:
        proc = subprocess.run(
            [exe, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    output = (proc.stdout or proc.stderr).splitlines()
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "first_line": output[0] if output else "",
    }


def torch_backend_summary() -> dict[str, Any]:
    status = module_status("torch")
    if not status.get("ok"):
        return status
    import torch  # type: ignore

    result = {
        "name": "torch-backend",
        "ok": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_compiled": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            result["cuda_device_name_0"] = torch.cuda.get_device_name(0)
            result["cuda_capability_0"] = tuple(torch.cuda.get_device_capability(0))
        except Exception as exc:  # noqa: BLE001
            result["cuda_query_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a MOSS-TTS environment without loading models.")
    parser.add_argument("--repo-root", help="Optional MOSS-TTS checkout root to prepend to sys.path for import exposure diagnosis.")
    parser.add_argument("--check-optional", nargs="*", default=[], choices=OPTIONAL_IMPORTS + ["all"], help="Optional dependency modules to import. Use 'all' for the common optional set.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe --help check for moss-tts-llama-cpp when present on PATH.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    added_repo_root = None
    if args.repo_root:
        root = Path(args.repo_root).expanduser().resolve()
        if root.exists():
            sys.path.insert(0, str(root))
            added_repo_root = str(root)

    optionals = OPTIONAL_IMPORTS if "all" in args.check_optional else args.check_optional
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "cwd": os.getcwd(),
        "repo_root_added": added_repo_root,
        "distributions": [distribution_status("moss-tts"), distribution_status("moss-soundeffect-v2")],
        "required_imports": [module_status(name) for name in DEFAULT_IMPORTS],
        "optional_imports": [module_status(name) for name in optionals],
        "torch_backend": torch_backend_summary() if "torch" in optionals or "all" in args.check_optional else None,
        "cli": [command_help_status("moss-tts-llama-cpp")] if args.check_cli else [],
        "notes": [
            "This helper does not load models, download weights, start services, or run generation/training.",
            "If distribution metadata passes but required imports fail, inspect the package exposure caveat in this skill's installation profiles.",
        ],
    }

    ok = all(item.get("ok") for item in report["distributions"][:1]) and all(
        item.get("ok") for item in report["required_imports"]
    )
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for item in report["distributions"]:
            print(f"dist {item['name']}: {'ok ' + item.get('version', '') if item.get('ok') else 'missing'}")
        for item in report["required_imports"]:
            print(f"import {item['name']}: {'ok' if item.get('ok') else item.get('error')}")
        for item in report["optional_imports"]:
            print(f"optional {item['name']}: {'ok' if item.get('ok') else item.get('error')}")
        if report["cli"]:
            for item in report["cli"]:
                print(f"cli {item['command']}: {'ok' if item.get('ok') else item.get('error')}")
        print("overall:", "ok" if ok else "needs attention")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
