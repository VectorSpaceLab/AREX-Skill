#!/usr/bin/env python3
"""Check MiroFish environment settings and optional backend health.

This helper is standalone and safe: it reads an env file or process environment,
warns about common configuration mistakes, and can query /health over HTTP. It
does not import MiroFish, call an LLM provider, or mutate Zep Cloud resources.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, Tuple

REQUIRED = ("LLM_API_KEY", "ZEP_API_KEY")
OPTIONAL = (
    "LLM_BASE_URL",
    "LLM_MODEL_NAME",
    "LLM_BOOST_API_KEY",
    "LLM_BOOST_BASE_URL",
    "LLM_BOOST_MODEL_NAME",
    "FLASK_HOST",
    "FLASK_PORT",
    "FLASK_DEBUG",
    "OASIS_DEFAULT_MAX_ROUNDS",
    "REPORT_AGENT_MAX_TOOL_CALLS",
    "REPORT_AGENT_MAX_REFLECTION_ROUNDS",
    "REPORT_AGENT_TEMPERATURE",
)


def parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            print(f"warning: {path}:{line_no}: ignored line without '='", file=sys.stderr)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def merged_env(path: str | None) -> Tuple[Dict[str, str], str]:
    env = dict(os.environ)
    if path:
        parsed = parse_env_file(Path(path))
        env.update(parsed)
        return env, path
    return env, "process environment"


def check_values(env: Dict[str, str], source: str) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    print(f"Checking MiroFish configuration from {source}")
    for key in REQUIRED:
        value = env.get(key, "")
        if not value or value.startswith("your_"):
            errors.append(f"{key} is missing or still uses a placeholder")
        else:
            print(f"ok: {key} is set")
    if env.get("ZEP_API_URL"):
        errors.append("ZEP_API_URL is set, but MiroFish supports Zep Cloud only; unset it")
    boost_keys = [k for k in ("LLM_BOOST_API_KEY", "LLM_BOOST_BASE_URL", "LLM_BOOST_MODEL_NAME") if env.get(k)]
    if boost_keys and len(boost_keys) != 3:
        warnings.append("LLM_BOOST_* is partially configured; set all three boost variables or omit all of them")
    port = env.get("FLASK_PORT")
    if port:
        try:
            number = int(port)
            if not (1 <= number <= 65535):
                errors.append("FLASK_PORT must be between 1 and 65535")
        except ValueError:
            errors.append("FLASK_PORT must be an integer")
    for key in ("OASIS_DEFAULT_MAX_ROUNDS", "REPORT_AGENT_MAX_TOOL_CALLS", "REPORT_AGENT_MAX_REFLECTION_ROUNDS"):
        if env.get(key):
            try:
                if int(env[key]) < 0:
                    errors.append(f"{key} must be non-negative")
            except ValueError:
                errors.append(f"{key} must be an integer")
    if env.get("REPORT_AGENT_TEMPERATURE"):
        try:
            value = float(env["REPORT_AGENT_TEMPERATURE"])
            if not (0 <= value <= 2):
                warnings.append("REPORT_AGENT_TEMPERATURE is outside the common 0..2 range")
        except ValueError:
            errors.append("REPORT_AGENT_TEMPERATURE must be numeric")
    for key in OPTIONAL:
        if env.get(key):
            print(f"set: {key}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    print(f"config summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def check_health(base_url: str, timeout: float) -> int:
    url = base_url.rstrip("/") + "/health"
    print(f"Checking backend health at {url}")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status_code = response.status
    except urllib.error.URLError as exc:
        print(f"error: health request failed: {exc}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print(f"error: health response was not JSON: {body[:200]!r}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if status_code != 200 or payload.get("status") != "ok":
        print("error: unexpected health response", file=sys.stderr)
        return 2
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MiroFish env settings and optional backend /health.")
    parser.add_argument("--env-file", help="path to a .env file to read in addition to process environment")
    parser.add_argument("--base-url", help="backend base URL, for example http://localhost:5001")
    parser.add_argument("--timeout", type=float, default=5.0, help="health-check timeout in seconds")
    parser.add_argument("--self-test", action="store_true", help="run a built-in placeholder-detection self-test")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.self_test:
        sample = {"LLM_API_KEY": "real-key", "ZEP_API_KEY": "real-zep", "FLASK_PORT": "5001"}
        return check_values(sample, "built-in self-test")

    code = 0
    if args.env_file or not args.base_url:
        env, source = merged_env(args.env_file)
        code = max(code, check_values(env, source))
    if args.base_url:
        code = max(code, check_health(args.base_url, args.timeout))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
