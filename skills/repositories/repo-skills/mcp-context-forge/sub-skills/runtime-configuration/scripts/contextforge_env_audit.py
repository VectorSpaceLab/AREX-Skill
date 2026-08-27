#!/usr/bin/env python3
"""Audit ContextForge env files without printing secret values.

This helper is intentionally read-only.
It reports the status of the required secrets, highlights common feature flags,
and optionally compares the keys in an env file with `.env.example`.

Typical usage:
    python scripts/contextforge_env_audit.py .env
    python scripts/contextforge_env_audit.py .env --example-file .env.example

The audit shares the same weak-secret vocabulary used by the gateway's secret
initialization and validation helpers, but it never writes to disk.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - fallback for minimal environments
    dotenv_values = None

try:
    from mcpgateway._security_constants import MIN_ENTROPY, MIN_SECRET_LENGTH, WEAK_VALUES as RAW_WEAK_VALUES, calculate_entropy
except Exception:  # pragma: no cover - keeps the bundled audit usable before package install
    MIN_SECRET_LENGTH = 32
    MIN_ENTROPY = 3.5
    RAW_WEAK_VALUES = (
        "my-test-key",
        "my-test-key-but-now-longer-than-32-bytes",
        "my-test-salt",
        "changeme",
        "secret",
        "password",
        "test-secret",
        "my-secret",
        "12345678",
    )

    def calculate_entropy(text: str) -> float:
        if not text:
            return 0.0
        probabilities = [text.count(c) / len(text) for c in set(text)]
        return -sum(p * math.log2(p) for p in probabilities)

SECRET_KEYS = ("JWT_SECRET_KEY", "AUTH_ENCRYPTION_SECRET")
FEATURE_FLAGS = {
    "AUTH_REQUIRED": True,
    "MCPGATEWAY_UI_ENABLED": False,
    "MCPGATEWAY_ADMIN_API_ENABLED": False,
    "PLUGINS_ENABLED": False,
    "OBSERVABILITY_ENABLED": False,
    "API_ALLOW_BASIC_AUTH": False,
    "DOCS_ALLOW_BASIC_AUTH": False,
}
BACKEND_KEYS = {
    "DATABASE_URL": "sqlite:///./mcp.db",
    "REDIS_URL": "redis://localhost:6379/0",
}
WEAK_SECRET_VALUES = frozenset(value.lower() for value in RAW_WEAK_VALUES)


@dataclass(frozen=True)
class SecretStatus:
    """Classification for a required secret."""

    state: str
    details: str


def load_env(path: Path) -> dict[str, str]:
    """Load env-style key/value pairs from *path*.

    Missing files return an empty mapping so the caller can report a clean error.
    """

    if not path.exists():
        return {}
    if dotenv_values is None:
        return load_env_without_dotenv(path)
    return load_env_with_dotenv(path, dotenv_values)


def load_env_with_dotenv(path: Path, parser: Callable[..., dict[str, str | None]]) -> dict[str, str]:
    """Load an env file with python-dotenv, avoiding interpolation when supported."""

    try:
        raw = parser(path, interpolate=False)
    except TypeError:
        raw = parser(path)
    return {key: "" if value is None else str(value) for key, value in raw.items() if key}


def load_env_without_dotenv(path: Path) -> dict[str, str]:
    """Small fallback parser for simple KEY=value env files."""

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key] = value
    return values


def normalize_bool(value: str | None, default: bool) -> str:
    """Render a boolean-like env value without revealing secrets."""

    if value is None or not value.strip():
        return f"unset (code default: {str(default).lower()})"
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return "true"
    if lowered in {"0", "false", "no", "off"}:
        return "false"
    return f"unexpected value: {value!r}"


def classify_secret(value: str | None) -> SecretStatus:
    """Classify a secret without printing the secret itself."""

    if value is None or not value.strip():
        return SecretStatus("missing", "not set")

    cleaned = value.strip()
    lowered = cleaned.lower()
    reasons: list[str] = []

    if lowered.startswith("__replace_me__"):
        reasons.append("placeholder")
    if lowered in WEAK_SECRET_VALUES:
        reasons.append("known weak value")
    if len(cleaned) < MIN_SECRET_LENGTH:
        reasons.append(f"too short (len={len(cleaned)} < {MIN_SECRET_LENGTH})")
    entropy = calculate_entropy(cleaned)
    if entropy < MIN_ENTROPY:
        reasons.append(f"low entropy ({entropy:.2f} < {MIN_ENTROPY})")

    if reasons:
        return SecretStatus("weak", ", ".join(reasons))
    return SecretStatus("ok", f"length={len(cleaned)}, entropy={entropy:.2f}")


def classify_backend(value: str | None, default: str) -> str:
    """Summarize a backend URL without echoing credentials."""

    if value is None or not value.strip():
        parsed_default = urlparse(default)
        return f"unset (code default: {parsed_default.scheme or default})"

    parsed = urlparse(value.strip())
    scheme = parsed.scheme or "unknown"
    if scheme.startswith("sqlite"):
        return "sqlite"
    if scheme.startswith("postgresql") or scheme.startswith("postgres"):
        return scheme
    if scheme in {"redis", "rediss"}:
        return scheme
    return scheme or "unknown"


def compare_keys(env_values: dict[str, str], example_values: dict[str, str]) -> tuple[list[str], list[str]]:
    """Return the missing and extra keys compared with the example file."""

    env_keys = set(env_values)
    example_keys = set(example_values)
    missing = sorted(example_keys - env_keys)
    extra = sorted(env_keys - example_keys)
    return missing, extra


def format_sample(keys: Iterable[str], limit: int = 12) -> str:
    """Format a bounded sample of keys for display."""

    keys_list = list(keys)
    sample = keys_list[:limit]
    if not sample:
        return "none"
    if len(keys_list) > limit:
        return ", ".join(sample) + ", ..."
    return ", ".join(sample)


def render_report(env_path: Path, env_values: dict[str, str], example_path: Path | None, example_values: dict[str, str] | None) -> tuple[int, list[str]]:
    """Render the audit and return an exit code plus collected lines."""

    lines: list[str] = [f"ContextForge env audit: {env_path}"]
    exit_code = 0

    lines.append("Secrets:")
    for key in SECRET_KEYS:
        status = classify_secret(env_values.get(key))
        lines.append(f"  - {key}: {status.state} ({status.details})")
        if status.state != "ok":
            exit_code = 1

    lines.append("Feature flags:")
    for key, default in FEATURE_FLAGS.items():
        lines.append(f"  - {key}: {normalize_bool(env_values.get(key), default)}")

    lines.append("Backends:")
    for key, default in BACKEND_KEYS.items():
        lines.append(f"  - {key}: {classify_backend(env_values.get(key), default)}")

    if example_values is not None and example_path is not None:
        missing, extra = compare_keys(env_values, example_values)
        lines.append(f"Example comparison: {example_path}")
        lines.append(f"  - missing keys: {len(missing)}")
        if missing:
            lines.append(f"    sample: {format_sample(missing)}")
        lines.append(f"  - extra keys: {len(extra)}")
        if extra:
            lines.append(f"    sample: {format_sample(extra)}")

    return exit_code, lines


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        description="Audit a ContextForge env file without printing secret values.",
    )
    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env",
        help="Path to the env file to audit (default: .env)",
    )
    parser.add_argument(
        "--example-file",
        dest="example_file",
        help="Optional .env.example-style file to compare keys against",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return an exit status."""

    parser = build_parser()
    args = parser.parse_args(argv)

    env_path = Path(args.env_file).expanduser()
    env_values = load_env(env_path)
    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 2

    example_path = Path(args.example_file).expanduser() if args.example_file else None
    example_values = None
    if example_path is not None:
        example_values = load_env(example_path)
        if not example_path.exists():
            print(f"error: example file not found: {example_path}", file=sys.stderr)
            return 2

    exit_code, lines = render_report(env_path, env_values, example_path, example_values)
    for line in lines:
        print(line)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
