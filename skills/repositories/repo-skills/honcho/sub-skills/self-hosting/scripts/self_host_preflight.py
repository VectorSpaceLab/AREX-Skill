#!/usr/bin/env python3
"""Self-hosted Honcho preflight helper.

Run from a Honcho repository root after creating `.env` (or pass
`--env-file`). The script performs non-secret static checks, optional
`/health`, and an optional DB-backed workspace smoke request.

It deliberately does not import Honcho internals, run migrations, or mutate the
embedding schema. Use the repository-native scripts for those operations.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}
_VECTOR_TYPES = {"pgvector", "turbopuffer", "lancedb"}
_SUPPORTED_TRANSPORTS = {"openai", "anthropic", "gemini"}


@dataclass
class Finding:
    level: str
    message: str


def _strip_inline_comment(value: str) -> str:
    """Strip shell-style comments outside single/double quotes."""
    quote: str | None = None
    escaped = False
    out: list[str] = []
    for ch in value:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and quote == '"':
            out.append(ch)
            escaped = True
            continue
        if ch in {'"', "'"}:
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            out.append(ch)
            continue
        if ch == "#" and quote is None:
            break
        out.append(ch)
    return "".join(out).strip()


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(path: pathlib.Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            print(f"WARN: ignoring {path}:{lineno}: no '=' found", file=sys.stderr)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            print(f"WARN: ignoring {path}:{lineno}: invalid key {key!r}", file=sys.stderr)
            continue
        env[key] = _unquote(_strip_inline_comment(value))
    return env


def as_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    return default


def has_any(env: dict[str, str], keys: Iterable[str]) -> bool:
    return any(bool(env.get(k)) for k in keys)


def add(finds: list[Finding], level: str, message: str) -> None:
    finds.append(Finding(level, message))


def static_checks(env: dict[str, str], repo_root: pathlib.Path) -> list[Finding]:
    finds: list[Finding] = []

    expected_files = [
        "src/main.py",
        "src/deriver/__main__.py",
        "alembic.ini",
        "scripts/configure_embeddings.py",
        "scripts/generate_jwt.py",
    ]
    missing = [p for p in expected_files if not (repo_root / p).exists()]
    if missing:
        add(
            finds,
            "WARN",
            "current directory does not look like a complete Honcho repo; missing "
            + ", ".join(missing),
        )
    else:
        add(finds, "OK", "repository shape contains API, deriver, Alembic, and helper scripts")

    db_uri = env.get("DB_CONNECTION_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    if not db_uri:
        add(finds, "FAIL", "DB_CONNECTION_URI is empty")
    elif not db_uri.startswith("postgresql+psycopg://"):
        add(finds, "FAIL", "DB_CONNECTION_URI must start with postgresql+psycopg://")
    else:
        add(finds, "OK", "DB_CONNECTION_URI uses postgresql+psycopg://")

    auth_enabled = as_bool(env.get("AUTH_USE_AUTH"), default=False)
    if auth_enabled and not env.get("AUTH_JWT_SECRET"):
        add(finds, "FAIL", "AUTH_USE_AUTH=true requires AUTH_JWT_SECRET")
    elif auth_enabled:
        add(finds, "OK", "auth is enabled and AUTH_JWT_SECRET is set")
    else:
        add(finds, "WARN", "AUTH_USE_AUTH=false; acceptable for local development, not production")

    if env.get("VECTOR_STORE_DIMENSIONS"):
        add(finds, "WARN", "VECTOR_STORE_DIMENSIONS is deprecated; use EMBEDDING_VECTOR_DIMENSIONS")

    dim_raw = env.get("EMBEDDING_VECTOR_DIMENSIONS", "1536")
    try:
        dim = int(dim_raw)
        if dim <= 0:
            raise ValueError
        add(finds, "OK", f"EMBEDDING_VECTOR_DIMENSIONS parses as {dim}")
    except ValueError:
        add(finds, "FAIL", f"EMBEDDING_VECTOR_DIMENSIONS must be a positive integer, got {dim_raw!r}")

    vector_type = env.get("VECTOR_STORE_TYPE", "pgvector").strip().lower()
    if vector_type not in _VECTOR_TYPES:
        add(finds, "FAIL", f"VECTOR_STORE_TYPE must be one of {sorted(_VECTOR_TYPES)}, got {vector_type!r}")
    elif vector_type == "turbopuffer" and not env.get("VECTOR_STORE_TURBOPUFFER_API_KEY"):
        add(finds, "FAIL", "VECTOR_STORE_TYPE=turbopuffer requires VECTOR_STORE_TURBOPUFFER_API_KEY")
    elif vector_type == "lancedb":
        add(finds, "WARN", "VECTOR_STORE_TYPE=lancedb requires the optional LanceDB dependency or INSTALL_LANCEDB=true Docker build")
    else:
        add(finds, "OK", f"VECTOR_STORE_TYPE={vector_type}")

    embedding_transport = env.get("EMBEDDING_MODEL_CONFIG__TRANSPORT", "openai").strip().lower()
    if embedding_transport not in _SUPPORTED_TRANSPORTS:
        add(finds, "WARN", f"embedding transport {embedding_transport!r} is not one of {sorted(_SUPPORTED_TRANSPORTS)}")
    embed_messages = as_bool(env.get("EMBED_MESSAGES"), default=True)
    if embed_messages:
        needed_key = f"LLM_{embedding_transport.upper()}_API_KEY"
        override_key = env.get("EMBEDDING_MODEL_CONFIG__OVERRIDES__API_KEY_ENV")
        if override_key and env.get(override_key):
            add(finds, "OK", f"embedding API key override {override_key} is set")
        elif not env.get(needed_key):
            add(finds, "WARN", f"EMBED_MESSAGES=true and {needed_key} is not set; startup may fail unless config.toml supplies credentials")
        else:
            add(finds, "OK", f"embedding provider key {needed_key} is set")

    # Current defaults use OpenAI for all text-generation features. Warn rather
    # than fail because deployments may use config.toml or per-feature key envs.
    if not has_any(env, ("LLM_OPENAI_API_KEY", "LLM_ANTHROPIC_API_KEY", "LLM_GEMINI_API_KEY")):
        add(finds, "WARN", "no LLM provider key found in environment/.env; current defaults need LLM_OPENAI_API_KEY")

    feature_transports = {
        "DERIVER_MODEL_CONFIG__TRANSPORT": "openai",
        "SUMMARY_MODEL_CONFIG__TRANSPORT": "openai",
        "DREAM_DEDUCTION_MODEL_CONFIG__TRANSPORT": "openai",
        "DREAM_INDUCTION_MODEL_CONFIG__TRANSPORT": "openai",
        "DIALECTIC_LEVELS__minimal__MODEL_CONFIG__TRANSPORT": "openai",
        "DIALECTIC_LEVELS__low__MODEL_CONFIG__TRANSPORT": "openai",
        "DIALECTIC_LEVELS__medium__MODEL_CONFIG__TRANSPORT": "openai",
        "DIALECTIC_LEVELS__high__MODEL_CONFIG__TRANSPORT": "openai",
        "DIALECTIC_LEVELS__max__MODEL_CONFIG__TRANSPORT": "openai",
    }
    for key, default in feature_transports.items():
        transport = env.get(key, default).strip().lower()
        if transport not in _SUPPORTED_TRANSPORTS:
            add(finds, "WARN", f"{key}={transport!r} is not a built-in transport")
            continue
        provider_key = f"LLM_{transport.upper()}_API_KEY"
        if env.get(key) and not env.get(provider_key):
            add(finds, "WARN", f"{key} selects {transport!r} but {provider_key} is not set")

    if as_bool(env.get("CACHE_ENABLED"), default=False):
        cache_url = env.get("CACHE_URL", "redis://localhost:6379/0?suppress=true")
        if not cache_url.startswith("redis://") and not cache_url.startswith("rediss://"):
            add(finds, "WARN", f"CACHE_ENABLED=true but CACHE_URL does not look like redis/rediss: {cache_url!r}")
        else:
            add(finds, "OK", "cache is enabled and CACHE_URL looks like Redis")

    return finds


def request_json(method: str, url: str, *, payload: dict[str, object] | None = None, token: str | None = None, timeout: float = 5.0) -> tuple[int, str]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - operator-supplied local URL
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def http_checks(base_url: str, *, workspace_smoke: bool, token: str | None) -> list[Finding]:
    finds: list[Finding] = []
    base = base_url.rstrip("/")
    try:
        status, body = request_json("GET", f"{base}/health")
        if status == 200 and '"ok"' in body:
            add(finds, "OK", f"GET {base}/health returned 200")
        else:
            add(finds, "WARN", f"GET {base}/health returned {status}: {body[:200]}")
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic should report all failures
        add(finds, "WARN", f"GET {base}/health failed: {exc}")
        return finds

    if workspace_smoke:
        name = f"preflight-{int(time.time())}"
        try:
            status, body = request_json(
                "POST",
                f"{base}/v3/workspaces",
                payload={"name": name},
                token=token,
            )
            if 200 <= status < 300:
                add(finds, "OK", f"POST /v3/workspaces succeeded for {name!r}")
            elif status in {401, 403}:
                add(finds, "FAIL", f"workspace smoke got {status}; pass --api-key when auth is enabled")
            else:
                add(finds, "FAIL", f"workspace smoke returned {status}: {body[:400]}")
        except Exception as exc:  # noqa: BLE001
            add(finds, "FAIL", f"workspace smoke failed: {exc}")
    return finds


def print_findings(findings: list[Finding]) -> None:
    order = {"FAIL": 0, "WARN": 1, "OK": 2}
    for finding in sorted(findings, key=lambda f: (order.get(f.level, 9), f.message)):
        print(f"{finding.level}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight a self-hosted Honcho configuration")
    parser.add_argument("--env-file", default=".env", help="dotenv file to read before overlaying the current process environment")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Honcho API base URL for HTTP checks")
    parser.add_argument("--skip-http", action="store_true", help="skip /health check")
    parser.add_argument("--workspace-smoke", action="store_true", help="also POST a throwaway workspace to verify DB+migrations+auth")
    parser.add_argument("--api-key", default=os.environ.get("HONCHO_API_KEY"), help="Bearer token for --workspace-smoke when auth is enabled; defaults to HONCHO_API_KEY")
    args = parser.parse_args(argv)

    repo_root = pathlib.Path.cwd()
    file_env = load_env_file(repo_root / args.env_file)
    merged = {**file_env, **os.environ}

    findings = static_checks(merged, repo_root)
    if not args.skip_http:
        findings.extend(http_checks(args.base_url, workspace_smoke=args.workspace_smoke, token=args.api_key))

    print_findings(findings)
    if any(f.level == "FAIL" for f in findings):
        return 2
    if any(f.level == "WARN" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
