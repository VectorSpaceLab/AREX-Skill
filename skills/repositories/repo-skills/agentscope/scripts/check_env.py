#!/usr/bin/env python3
"""Check that the installed AgentScope package and key submodules import.

This helper is safe to run from any directory after the skill has been
installed. It prints the installed package version, tries the main public
imports, and optionally reports local backend executables and common provider
or service environment variables.

Example:
    python scripts/check_env.py --show-backends
"""
from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import os
import shutil
import sys
from dataclasses import dataclass

CORE_MODULES = [
    "agentscope",
    "agentscope.agent",
    "agentscope.tool",
    "agentscope.message",
    "agentscope.event",
    "agentscope.permission",
    "agentscope.state",
    "agentscope.skill",
    "agentscope.model",
    "agentscope.embedding",
    "agentscope.formatter",
    "agentscope.tts",
    "agentscope.app",
    "agentscope.rag",
    "agentscope.workspace",
]

BACKEND_EXECUTABLES = [
    "docker",
    "bwrap",
    "container",
    "kubectl",
    "redis-server",
    "npx",
    "uvx",
]

BACKEND_ENV_VARS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY",
    "MOONSHOT_API_KEY",
    "XAI_API_KEY",
    "OLLAMA_HOST",
    "MEM0_API_KEY",
    "REME_WORKSPACE_DIR",
    "E2B_API_KEY",
    "DAYTONA_API_KEY",
    "OPENSANDBOX_DOMAIN",
    "OPENSANDBOX_API_KEY",
    "AMAP_API_KEY",
    "CLAWHUB_API_TOKEN",
    "K8S_TEST_IMAGE",
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str



def _print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else "FAIL"
    print(f"[{status}] {result.name}: {result.message}")



def _import_modules() -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in CORE_MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append(CheckResult(name, False, f"{type(exc).__name__}: {exc}"))
        else:
            results.append(CheckResult(name, True, "imported"))
    return results



def _show_backends() -> None:
    print("\nBackend executables:")
    for exe in BACKEND_EXECUTABLES:
        path = shutil.which(exe)
        print(f"  {exe}: {path or 'missing'}")

    print("\nCommon backend env vars:")
    for name in BACKEND_ENV_VARS:
        value = os.environ.get(name)
        print(f"  {name}: {'set' if value else 'unset'}")



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show-backends",
        action="store_true",
        help="Print local backend executables and common env vars.",
    )
    args = parser.parse_args()

    print(f"python: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    try:
        print(f"agentscope: {metadata.version('agentscope')}")
    except metadata.PackageNotFoundError:
        print("agentscope: NOT INSTALLED")
        return 1

    results = _import_modules()
    for result in results:
        _print_result(result)

    if args.show_backends:
        _show_backends()

    failures = [result for result in results if not result.ok]
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
