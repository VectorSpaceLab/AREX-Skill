#!/usr/bin/env python3
"""Inspect LangExtract provider routing without calling any model API.

Examples:
  python check_provider_routes.py
  python check_provider_routes.py gemini-3.5-flash gpt-4o gemma2:2b
  python check_provider_routes.py --skip-plugins --json

The script imports LangExtract, loads built-in provider registrations, optionally
loads installed provider plugins, and resolves model IDs to provider classes. It
never sends prompts to a provider and never prints secret environment values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

DEFAULT_MODEL_IDS = [
    "gemini-3.5-flash",
    "gpt-4o",
    "gpt-5-mini",
    "gemma2:2b",
    "llama3.2:1b",
    "qwen2.5:7b",
    "gpt-oss:20b",
]

SECRET_ENV_NAMES = [
    "GEMINI_API_KEY",
    "LANGEXTRACT_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "OLLAMA_BASE_URL",
]


def _import_langextract() -> Any:
    try:
        import langextract as lx  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pragma: no cover - user diagnostic path
        raise SystemExit(
            "Could not import langextract in this Python environment. "
            "Install langextract before running the route checker. "
            f"Original error: {exc}"
        ) from exc
    return lx


def _load_registrations(lx: Any, *, skip_plugins: bool) -> tuple[Any, list[str]]:
    warnings: list[str] = []
    from langextract.providers import router  # pylint: disable=import-outside-toplevel

    lx.providers.load_builtins_once()
    if skip_plugins:
        warnings.append("Plugin discovery skipped by --skip-plugins.")
    else:
        try:
            lx.providers.load_plugins_once()
        except Exception as exc:  # pragma: no cover - load_plugins_once is normally defensive
            warnings.append(f"Plugin discovery raised {type(exc).__name__}: {exc}")
    return router, warnings


def _credential_signals() -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in SECRET_ENV_NAMES}


def _resolve(router: Any, model_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model_id in model_ids:
        try:
            provider_cls = router.resolve(model_id)
            rows.append(
                {
                    "model_id": model_id,
                    "status": "ok",
                    "provider_class": provider_cls.__name__,
                    "provider_module": provider_cls.__module__,
                }
            )
        except Exception as exc:  # route errors are the point of this helper
            rows.append(
                {
                    "model_id": model_id,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect LangExtract provider route resolution without network/API calls."
    )
    parser.add_argument(
        "model_ids",
        nargs="*",
        help="Model IDs to resolve. Defaults cover Gemini, OpenAI/GPT, and Ollama patterns.",
    )
    parser.add_argument(
        "--skip-plugins",
        action="store_true",
        help="Load built-in provider patterns only; do not discover installed plugins.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lx = _import_langextract()
    router, warnings = _load_registrations(lx, skip_plugins=args.skip_plugins)
    model_ids = args.model_ids or DEFAULT_MODEL_IDS
    rows = _resolve(router, model_ids)
    payload = {
        "provider_patterns": router.list_providers(),
        "resolved": rows,
        "credential_env_present": _credential_signals(),
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if all(row["status"] == "ok" for row in rows) else 1

    print("LangExtract provider route check")
    print("Credential variables present (values redacted):")
    for name, present in payload["credential_env_present"].items():
        print(f"  {name}: {'set' if present else 'not set'}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print("\nRegistered provider patterns:")
    for patterns, priority in payload["provider_patterns"]:
        joined = ", ".join(patterns)
        print(f"  priority {priority}: {joined}")
    print("\nResolution:")
    for row in rows:
        if row["status"] == "ok":
            print(f"  {row['model_id']}: {row['provider_class']} ({row['provider_module']})")
        else:
            print(f"  {row['model_id']}: ERROR {row['error_type']}: {row['error']}")
    return 0 if all(row["status"] == "ok" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
