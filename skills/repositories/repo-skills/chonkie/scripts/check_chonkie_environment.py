#!/usr/bin/env python3
"""Safe Chonkie environment diagnostic.

This helper checks package importability, selected optional dependency groups,
CLI help availability, and non-network API/class imports. It does not download
models, call provider APIs, start servers, or write to datastores.

Examples:
    python scripts/check_chonkie_environment.py --json
    python scripts/check_chonkie_environment.py --require cli api table code
    python scripts/check_chonkie_environment.py --skip-cli
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import shutil
import subprocess
import sys
from typing import Any

OPTIONAL_GROUPS: dict[str, dict[str, list[str] | str]] = {
    "base": {
        "modules": ["chonkie", "chonkie_core", "numpy", "tokie", "tenacity", "httpx"],
        "hint": "python -m pip install chonkie",
    },
    "cli": {"modules": ["typer", "rich"], "hint": "python -m pip install 'chonkie[cli]'"},
    "api": {
        "modules": ["fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "jsonschema"],
        "hint": "python -m pip install 'chonkie[api]'",
    },
    "table": {
        "modules": ["pandas", "tabulate", "openpyxl", "lxml"],
        "hint": "python -m pip install 'chonkie[table]'",
    },
    "code": {
        "modules": ["tree_sitter", "tree_sitter_language_pack"],
        "hint": "python -m pip install 'chonkie[code]'",
    },
    "semantic": {
        "modules": ["model2vec", "tokenizers"],
        "hint": "python -m pip install 'chonkie[semantic]'",
    },
    "st": {
        "modules": ["sentence_transformers", "tokenizers", "accelerate"],
        "hint": "python -m pip install 'chonkie[st]'",
    },
    "neural": {
        "modules": ["transformers", "torch"],
        "hint": "python -m pip install 'chonkie[neural]'",
    },
    "openai": {"modules": ["openai", "pydantic"], "hint": "python -m pip install 'chonkie[openai]'"},
    "gemini": {"modules": ["google.genai", "pydantic"], "hint": "python -m pip install 'chonkie[gemini]'"},
    "handshakes": {
        "modules": ["chromadb", "qdrant_client", "lancedb", "pymilvus", "pymongo", "vecs", "pinecone", "turbopuffer", "weaviate", "elasticsearch"],
        "hint": "install only the datastore-specific extra you need, e.g. 'chonkie[qdrant]'",
    },
    "datasets": {"modules": ["datasets"], "hint": "python -m pip install 'chonkie[datasets]'"},
}

CHONKIE_IMPORTS = [
    "chonkie",
    "chonkie.pipeline",
    "chonkie.chunker",
    "chonkie.chef",
    "chonkie.refinery",
    "chonkie.porters",
    "chonkie.cloud.pipeline",
]

SAFE_CLASSES = [
    ("chonkie", "RecursiveChunker"),
    ("chonkie", "TokenChunker"),
    ("chonkie", "SentenceChunker"),
    ("chonkie", "Pipeline"),
    ("chonkie.api.main", "app"),
]


def module_available(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
        return {"module": name, "available": spec is not None, "error": None}
    except Exception as exc:  # namespace import edge cases
        return {"module": name, "available": False, "error": f"{type(exc).__name__}: {exc}"}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def check_imports() -> list[dict[str, Any]]:
    results = []
    for module_name in CHONKIE_IMPORTS:
        try:
            module = importlib.import_module(module_name)
            results.append({"module": module_name, "status": "ok", "file_known": bool(getattr(module, "__file__", None))})
        except Exception as exc:
            results.append({"module": module_name, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return results


def check_safe_classes() -> list[dict[str, Any]]:
    results = []
    for module_name, attr in SAFE_CLASSES:
        try:
            module = importlib.import_module(module_name)
            getattr(module, attr)
            results.append({"target": f"{module_name}.{attr}", "status": "ok"})
        except Exception as exc:
            results.append({"target": f"{module_name}.{attr}", "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return results


def check_groups(groups: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in groups:
        info = OPTIONAL_GROUPS.get(group)
        if not info:
            out[group] = {"status": "unknown-group", "knownGroups": sorted(OPTIONAL_GROUPS)}
            continue
        modules = [module_available(str(m)) for m in info["modules"]]  # type: ignore[index]
        missing = [m["module"] for m in modules if not m["available"]]
        out[group] = {
            "status": "ok" if not missing else "missing",
            "missing": missing,
            "modules": modules,
            "installHint": info["hint"],
        }
    return out


def run_cli_help(command: str, timeout: float) -> dict[str, Any]:
    args = [command, "--help"]
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "command": " ".join(args),
            "returncode": proc.returncode,
            "status": "ok" if proc.returncode == 0 else "error",
            "stdoutPreview": proc.stdout[:500],
            "stderrPreview": proc.stderr[:500],
        }
    except FileNotFoundError:
        return {"command": " ".join(args), "status": "missing", "error": "console command not found"}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(args), "status": "timeout", "error": f"timed out after {timeout}s"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an installed Chonkie environment without network calls.")
    parser.add_argument("--json", action="store_true", help="Emit JSON diagnostics.")
    parser.add_argument("--require", nargs="*", default=["base"], help="Optional groups to check; use names such as cli api table code semantic handshakes.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip console-script help check.")
    parser.add_argument("--cli-command", default=None, help="Console command path/name to use for help check. Defaults to PATH lookup for 'chonkie'.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Timeout for CLI help subprocess.")
    args = parser.parse_args()

    chonkie_version = dist_version("chonkie")
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution": {"chonkie": chonkie_version},
        "imports": check_imports(),
        "safeClasses": check_safe_classes(),
        "groups": check_groups(args.require),
        "cli": None,
        "notes": [
            "This helper does not download models, call providers, start servers, or write to datastores.",
            "Missing optional modules are capability gates; install only the extra required for the user's task.",
            "Credential presence is not checked here to avoid encouraging secret disclosure.",
        ],
    }

    if not args.skip_cli:
        command = args.cli_command or shutil.which("chonkie") or "chonkie"
        report["cli"] = run_cli_help(command, args.timeout)

    failures = []
    failures.extend(item for item in report["imports"] if item["status"] != "ok")
    failures.extend(item for item in report["safeClasses"] if item["status"] != "ok")
    for group_name, group_report in report["groups"].items():
        if group_report["status"] == "unknown-group":
            failures.append({"group": group_name, "error": "unknown optional group"})
    if report["cli"] and report["cli"].get("status") not in {"ok"}:
        failures.append({"cli": report["cli"]})

    report["status"] = "ok" if not failures else "attention"
    report["failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Chonkie distribution: {chonkie_version or 'not installed'}")
        print(f"Status: {report['status']}")
        for group, group_report in report["groups"].items():
            missing = group_report.get("missing", [])
            if missing:
                print(f"[{group}] missing {', '.join(missing)}; {group_report.get('installHint')}")
            else:
                print(f"[{group}] ok")
        if report["cli"]:
            print(f"CLI: {report['cli']['status']} ({report['cli']['command']})")
        if failures:
            print("Failures require attention; rerun with --json for details.")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
