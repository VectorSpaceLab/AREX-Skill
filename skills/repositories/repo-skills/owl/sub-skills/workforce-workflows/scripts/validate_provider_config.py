#!/usr/bin/env python3
"""Check OWL provider configuration without printing secret values.

This helper is intentionally dependency-free. It reads an optional dotenv-like
file and the process environment, reports only variable names/status, and does
not call a provider or mutate the environment.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, Iterable, List

PROVIDERS = {
    "openai": [["OPENAI_API_KEY"]],
    "anthropic": [["ANTHROPIC_API_KEY"]],
    "qwen": [["QWEN_API_KEY"]],
    "deepseek": [["DEEPSEEK_API_KEY"]],
    "gemini": [["GEMINI_API_KEY", "GOOGLE_API_KEY"]],
    "groq": [["GROQ_API_KEY"]],
    "openai-compatible": [["VLLM_API_URL"], ["VLLM_MODEL_NAME"]],
}
PLACEHOLDERS = {"your_key", "your-api-key", "your_api_key", "your_id", "your_id_here", ""}


def load_dotenv(path: Path | None) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if path is None:
        return values
    if not path.is_file():
        raise FileNotFoundError(path)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def choose_value(names: Iterable[str], file_values: Dict[str, str]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name)
        if value is None:
            value = file_values.get(name)
        if value is not None:
            return name, value
    return None, None


def is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip().lower().replace(" ", "_")
    return normalized in PLACEHOLDERS or normalized.startswith("your_") or normalized.startswith("your-")


def validate(provider: str, file_values: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    for alternatives in PROVIDERS[provider]:
        name, value = choose_value(alternatives, file_values)
        if name is None or is_placeholder(value):
            errors.append("missing or placeholder: " + " or ".join(alternatives))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--env-file", type=Path, help="dotenv-like file to inspect (never printed)")
    args = parser.parse_args()
    try:
        file_values = load_dotenv(args.env_file)
    except OSError as exc:
        print(f"ERROR: cannot read env file: {exc}")
        return 2
    errors = validate(args.provider, file_values)
    if errors:
        print(f"provider={args.provider}: NOT READY")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"provider={args.provider}: required variable names are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
