#!/usr/bin/env python3
"""Validate Mem0 self-hosted/OpenMemory env files without printing secrets."""

from __future__ import annotations

import argparse
from pathlib import Path

SECRET_HINTS = ("KEY", "SECRET", "PASSWORD", "TOKEN", "DATABASE_URL")
SERVER_REQUIRED = ("POSTGRES_PASSWORD", "JWT_SECRET")
SERVER_PROVIDER_ANY = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY")
OPENMEMORY_RECOMMENDED = ("OPENAI_API_KEY",)


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def redacted_state(key: str, value: str | None) -> str:
    if value is None or value == "":
        return "missing"
    if any(hint in key.upper() for hint in SECRET_HINTS):
        return "set-redacted"
    return "set"


def check_server(values: dict[str, str]) -> tuple[list[str], list[str]]:
    failures = [key for key in SERVER_REQUIRED if not values.get(key)]
    warnings: list[str] = []
    if not any(values.get(key) for key in SERVER_PROVIDER_ANY):
        warnings.append("No common LLM/embedder provider key found; default memory writes may fail.")
    if values.get("AUTH_DISABLED", "").lower() == "true":
        warnings.append("AUTH_DISABLED=true is local-development only; never use it in production.")
    if values.get("ADMIN_API_KEY"):
        warnings.append("ADMIN_API_KEY is set; prefer per-user dashboard API keys for new deployments.")
    return failures, warnings


def check_openmemory(values: dict[str, str]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings = [f"{key} is not set; default OpenMemory examples may fail." for key in OPENMEMORY_RECOMMENDED if not values.get(key)]
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Mem0 self-hosted/OpenMemory env files with secrets redacted.")
    parser.add_argument("--env-file", required=True, help="Path to a .env-style file to inspect.")
    parser.add_argument("--target", choices=("server", "openmemory"), default="server")
    args = parser.parse_args()

    path = Path(args.env_file)
    if not path.exists():
        print(f"ERROR: env file not found: {path}")
        return 2

    values = parse_env(path)
    failures, warnings = check_server(values) if args.target == "server" else check_openmemory(values)

    keys = SERVER_REQUIRED + SERVER_PROVIDER_ANY + ("AUTH_DISABLED", "ADMIN_API_KEY", "DASHBOARD_URL")
    if args.target == "openmemory":
        keys = OPENMEMORY_RECOMMENDED + ("QDRANT_URL", "DATABASE_URL")

    print(f"Target: {args.target}")
    for key in keys:
        print(f"{key}: {redacted_state(key, values.get(key))}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for failure in failures:
        print(f"ERROR: required setting missing: {failure}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
