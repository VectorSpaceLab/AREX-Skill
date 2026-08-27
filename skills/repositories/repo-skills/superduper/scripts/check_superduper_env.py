#!/usr/bin/env python3
"""Check a Python environment for Superduper base and optional plugins.

This diagnostic is safe by default: it imports modules, inspects metadata, and
reports the known console-script caveat. It never installs packages, opens
network connections, reads credentials, starts services, downloads models, or
mutates databases.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any


KNOWN_PLUGIN_MODULES = {
    "mongodb": "superduper_mongodb",
    "sql": "superduper_sql",
    "snowflake": "superduper_snowflake",
    "redis": "superduper_redis",
    "chromadb": "superduper_chromadb",
    "lance": "superduper_lance",
    "qdrant": "superduper_qdrant",
    "openai": "superduper_openai",
    "anthropic": "superduper_anthropic",
    "cohere": "superduper_cohere",
    "jina": "superduper_jina",
    "llamacpp": "superduper_llamacpp",
    "vllm": "superduper_vllm",
    "sentence_transformers": "superduper_sentence_transformers",
    "transformers": "superduper_transformers",
    "torch": "superduper_torch",
    "sklearn": "superduper_sklearn",
    "pillow": "superduper_pillow",
    "template": "superduper_template",
}


def normalize_plugin_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if normalized.startswith("superduper_"):
        normalized = normalized[len("superduper_") :]
    aliases = {
        "mongo": "mongodb",
        "mongomock": "mongodb",
        "sqlite": "sql",
        "duckdb": "sql",
        "postgres": "sql",
        "postgresql": "sql",
        "chroma": "chromadb",
        "hf": "transformers",
        "huggingface": "transformers",
        "pytorch": "torch",
        "pil": "pillow",
    }
    return aliases.get(normalized, normalized)


def dist_version(name: str) -> str | None:
    candidates = [name, name.replace("_", "-"), name.replace("-", "_")]
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return None


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        return {
            "module": module,
            "ok": True,
            "version": getattr(mod, "__version__", dist_version(module)),
            "exports": sorted([x for x in getattr(mod, "__all__", [])]) if hasattr(mod, "__all__") else None,
        }
    except Exception as exc:
        return {
            "module": module,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "install_hint": f"python -m pip install {module}",
        }


def check_base() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False}
    try:
        import inspect
        import superduper
        from superduper import Listener, ObjectModel, VectorIndex, superduper as connect
    except Exception as exc:
        result.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "install_hint": "python -m pip install superduper-framework",
            }
        )
        return result

    result.update(
        {
            "ok": True,
            "module_version": getattr(superduper, "__version__", None),
            "distribution_version": dist_version("superduper-framework"),
            "signatures": {
                "superduper": str(inspect.signature(connect)),
                "ObjectModel": str(inspect.signature(ObjectModel)),
                "Listener": str(inspect.signature(Listener)),
                "VectorIndex": str(inspect.signature(VectorIndex)),
            },
        }
    )
    return result


def check_cli(timeout: float) -> dict[str, Any]:
    exe = shutil.which("superduper")
    if exe is None:
        return {"found": False, "ok": False, "note": "No superduper executable on PATH."}
    try:
        completed = subprocess.run(
            [exe, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"found": True, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    output = (completed.stdout + completed.stderr).strip()
    return {
        "found": True,
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "output_excerpt": output[:600],
        "snapshot_warning": "This Superduper snapshot is known to fail if the console script points at missing superduper.__main__.",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Superduper base import, optional plugin imports, and CLI state.")
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Plugin key/module to import-check. Repeatable. Examples: mongodb, sql, openai, torch.",
    )
    parser.add_argument(
        "--all-known-plugins",
        action="store_true",
        help="Check all known first-party plugin import modules.",
    )
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="Also run `superduper --help` with a short timeout and report the known CLI caveat.",
    )
    parser.add_argument("--cli-timeout", type=float, default=5.0, help="Timeout seconds for --check-cli.")
    parser.add_argument("--as-json", action="store_true", help="Emit JSON only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    selected_plugins: list[str]
    if args.all_known_plugins:
        selected_plugins = list(KNOWN_PLUGIN_MODULES)
    else:
        selected_plugins = [normalize_plugin_name(p) for p in args.plugin]

    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "base": check_base(),
        "plugins": {},
        "notes": [
            "Import success does not prove credentials, external services, GPU kernels, or model weights are available.",
            "Use sub-skill helpers for Datalayer, component, vector, or plugin-specific smokes.",
        ],
    }
    for key in selected_plugins:
        module = KNOWN_PLUGIN_MODULES.get(key, f"superduper_{key}")
        result["plugins"][key] = import_status(module)

    if args.check_cli:
        result["cli"] = check_cli(args.cli_timeout)

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Superduper environment check")
        print("============================")
        print(json.dumps(result, indent=2, sort_keys=True))

    ok = bool(result["base"].get("ok"))
    missing_requested = any(not info.get("ok") for info in result["plugins"].values())
    if not ok or missing_requested:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
