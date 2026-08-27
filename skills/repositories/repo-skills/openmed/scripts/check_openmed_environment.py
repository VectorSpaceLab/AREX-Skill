#!/usr/bin/env python3
"""Inspect an OpenMed installation without invoking models or services.

The script checks importability, package version, CLI availability, selected
public APIs, and optional backend/module presence. It is safe for synthetic or
empty environments: no model download, network call, server listener, or PHI
processing is performed.

Example:
    python check_openmed_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

OPTIONAL_MODULES = {
    "fastapi": "service extra",
    "mcp": "mcp extra",
    "transformers": "hf/model extra",
    "torch": "torch/gliner/runtime extra",
    "onnxruntime": "onnx-runtime extra",
    "mlx": "mlx extra on Apple Silicon",
    "coremltools": "coreml extra",
    "pdfplumber": "multimodal PDF parser",
    "pydicom": "multimodal DICOM parser",
    "pandas": "pandas/table extra",
    "polars": "polars/table extra",
    "duckdb": "duckdb/table extra",
}


def _import_status(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        version = None
        try:
            version = metadata.version(module.split(".")[0])
        except metadata.PackageNotFoundError:
            version = getattr(imported, "__version__", None)
        return {"available": True, "version": version}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def inspect_environment(run_cli: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "openmed": _import_status("openmed"),
        "apis": {},
        "cli": {},
        "optional_modules": {},
    }

    if payload["openmed"].get("available"):
        import inspect
        import openmed

        for name in ["analyze_text", "extract_pii", "deidentify", "reidentify", "list_models"]:
            obj = getattr(openmed, name, None)
            payload["apis"][name] = str(inspect.signature(obj)) if obj else "missing"
        payload["openmed"]["package_version"] = getattr(openmed, "__version__", None)

    cli_path = shutil.which("openmed")
    if cli_path is None:
        sibling = Path(sys.executable).with_name("openmed")
        if sibling.exists():
            cli_path = str(sibling)
    payload["cli"]["path"] = cli_path
    if run_cli and cli_path:
        proc = subprocess.run(
            [cli_path, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
        payload["cli"].update(
            {
                "help_exit_code": proc.returncode,
                "help_first_line": (proc.stdout or proc.stderr).splitlines()[:1],
                "commands_seen": [
                    name
                    for name in [
                        "analyze",
                        "batch",
                        "deid",
                        "pii",
                        "risk",
                        "fhir",
                        "omop",
                        "ground",
                        "models",
                        "doctor",
                        "verify-pdf",
                    ]
                    if name in proc.stdout
                ],
            }
        )

    for module, purpose in OPTIONAL_MODULES.items():
        status = _import_status(module)
        status["purpose"] = purpose
        payload["optional_modules"][module] = status

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenMed import, CLI, and optional module availability.")
    parser.add_argument("--json", action="store_true", help="Emit full JSON payload.")
    parser.add_argument("--skip-cli", action="store_true", help="Do not run `openmed --help`.")
    args = parser.parse_args()

    payload = inspect_environment(run_cli=not args.skip_cli)
    ok = payload["openmed"].get("available") is True
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OpenMed environment check:", "ok" if ok else "failed")
        print("Python:", payload["python"])
        print("OpenMed:", payload["openmed"])
        print("CLI:", payload["cli"].get("path") or "not found")
        missing = [name for name, status in payload["optional_modules"].items() if not status["available"]]
        print("Missing optional modules:", ", ".join(missing) if missing else "none")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
