#!/usr/bin/env python3
"""Print a safe provider availability matrix for the installed AgentScope.

This helper checks which provider-related modules import, which common
credential environment variables are set, and which provider families are
available in the current Python environment.

Examples:
    python scripts/provider_matrix.py --list
    python scripts/provider_matrix.py --check
"""
from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import os
import sys
from dataclasses import dataclass

PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "xai": "XAI_API_KEY",
    "ollama": "OLLAMA_HOST",
}

MODULE_GROUPS = {
    "chat_models": "agentscope.model",
    "credentials": "agentscope.credential",
    "embeddings": "agentscope.embedding",
    "formatters": "agentscope.formatter",
    "tts": "agentscope.tts",
}


@dataclass
class Row:
    name: str
    ok: bool
    detail: str



def _check_module(name: str) -> Row:
    try:
        importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return Row(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}")
    return Row(name=name, ok=True, detail="imported")



def _print_row(row: Row) -> None:
    status = "OK" if row.ok else "FAIL"
    print(f"[{status}] {row.name}: {row.detail}")



def _list_status() -> None:
    print(f"python: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    try:
        print(f"agentscope: {metadata.version('agentscope')}")
    except metadata.PackageNotFoundError:
        print("agentscope: NOT INSTALLED")
        return

    print("\nModule imports:")
    for name in MODULE_GROUPS.values():
        _print_row(_check_module(name))

    print("\nProvider env vars:")
    for provider, env_var in PROVIDER_ENV_VARS.items():
        value = os.environ.get(env_var)
        print(f"[{'OK' if value else 'FAIL'}] {provider}: {env_var}={'set' if value else 'unset'}")



def _check_status() -> int:
    failures = []
    for name in MODULE_GROUPS.values():
        row = _check_module(name)
        _print_row(row)
        if not row.ok:
            failures.append(row)

    print("\nProvider env vars:")
    for provider, env_var in PROVIDER_ENV_VARS.items():
        value = os.environ.get(env_var)
        row = Row(provider, bool(value), f"{env_var}={'set' if value else 'unset'}")
        _print_row(row)

    return 0 if not failures else 1



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print a readable matrix and exit.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return non-zero if one of the core provider modules fails to import.",
    )
    args = parser.parse_args()

    if args.list:
        _list_status()
        return 0

    if args.check:
        print(f"python: {sys.executable}")
        print(f"version: {sys.version.split()[0]}")
        try:
            print(f"agentscope: {metadata.version('agentscope')}")
        except metadata.PackageNotFoundError:
            print("agentscope: NOT INSTALLED")
            return 1
        return _check_status()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
