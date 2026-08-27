#!/usr/bin/env python3
"""Summarize a DocsGPT local configuration without printing secrets.

The checker reads process environment first and then a repo-local .env file. It
is safe to run in development and CI: it redacts values, does not import the app,
and only opens network sockets when --check-services is provided.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

SECRET_HINTS = ("KEY", "SECRET", "TOKEN", "PASSWORD")
IMPORTANT_KEYS = [
    "AUTH_TYPE",
    "API_KEY",
    "INTERNAL_KEY",
    "POSTGRES_URI",
    "CELERY_BROKER_URL",
    "CACHE_REDIS_URL",
    "VECTOR_STORE",
    "LLM_NAME",
    "LLM_PROVIDER",
    "EMBEDDINGS_NAME",
    "EMBEDDINGS_BASE_URL",
    "SANDBOX_BACKEND",
    "JWT_SECRET_KEY",
    "ENCRYPTION_SECRET_KEY",
    "SCIM_ENABLED",
    "OIDC_ISSUER",
    "OIDC_CLIENT_ID",
    "OIDC_FRONTEND_URL",
]


@dataclass
class KeyStatus:
    key: str
    present: bool
    source: str
    value: str
    note: str = ""


@dataclass
class ServiceCheck:
    name: str
    configured: bool
    target: str
    reachable: bool | None
    note: str


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _redact(key: str, value: str) -> str:
    if not value:
        return ""
    if any(hint in key.upper() for hint in SECRET_HINTS):
        return "<set>"
    parsed = urlparse(value)
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        path = parsed.path or ""
        return f"{parsed.scheme}://<credentials>@{host}{port}{path}"
    return value


def _resolve_value(key: str, env_file: dict[str, str]) -> tuple[bool, str, str]:
    if key in os.environ:
        return True, "environment", os.environ[key]
    if key in env_file:
        return bool(env_file[key]), ".env", env_file[key]
    return False, "missing", ""


def _service_target(uri: str, default_port: int) -> tuple[str, int] | None:
    if not uri:
        return None
    parsed = urlparse(uri)
    if not parsed.hostname:
        return None
    return parsed.hostname, parsed.port or default_port


def _check_socket(name: str, uri: str, default_port: int, timeout: float) -> ServiceCheck:
    target = _service_target(uri, default_port)
    if not target:
        return ServiceCheck(name, False, "", None, "not configured or unparsable")
    host, port = target
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ServiceCheck(name, True, f"{host}:{port}", True, "TCP connection succeeded")
    except OSError as exc:
        return ServiceCheck(name, True, f"{host}:{port}", False, f"TCP connection failed: {exc}")


def build_report(repo: Path, check_services: bool) -> dict[str, object]:
    env_file = _parse_env_file(repo / ".env")
    keys = []
    for key in IMPORTANT_KEYS:
        present, source, value = _resolve_value(key, env_file)
        note = ""
        if key == "POSTGRES_URI" and not present:
            note = "Postgres is the canonical user-data store; set this for real app startup."
        if key == "INTERNAL_KEY" and not present:
            note = "Required for worker-to-backend internal calls in multi-process deployments."
        if key == "JWT_SECRET_KEY" and not present:
            note = "Set explicitly in production and multi-replica OIDC/session deployments."
        keys.append(KeyStatus(key, present, source, _redact(key, value), note))

    services: list[ServiceCheck] = []
    if check_services:
        env_values = {key: _resolve_value(key, env_file)[2] for key in IMPORTANT_KEYS}
        services.append(_check_socket("postgres", env_values.get("POSTGRES_URI", ""), 5432, 2.0))
        redis_uri = env_values.get("CACHE_REDIS_URL") or env_values.get("CELERY_BROKER_URL", "")
        services.append(_check_socket("redis", redis_uri, 6379, 2.0))

    warnings = [item.note for item in keys if item.note]
    if not (repo / "CONTRIBUTING.md").exists():
        warnings.append("Missing CONTRIBUTING.md; this is unexpected for DocsGPT.")
    return {
        "repo": str(repo),
        "env_file_present": (repo / ".env").exists(),
        "keys": [asdict(item) for item in keys],
        "service_checks": [asdict(item) for item in services],
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DocsGPT local config without exposing secrets")
    parser.add_argument("--repo", default=".", help="DocsGPT repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--check-services", action="store_true", help="Probe configured Postgres/Redis TCP endpoints")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "application" / "core" / "settings.py").exists():
        raise SystemExit(f"{repo} does not look like a DocsGPT checkout: missing application/core/settings.py")

    report = build_report(repo, args.check_services)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"DocsGPT repo: {repo}")
    print(f".env present: {report['env_file_present']}")
    for item in report["keys"]:  # type: ignore[index]
        status = "present" if item["present"] else "missing"
        display = f" = {item['value']}" if item["value"] else ""
        print(f"{item['key']}: {status} ({item['source']}){display}")
        if item["note"]:
            print(f"  note: {item['note']}")
    for check in report["service_checks"]:  # type: ignore[index]
        print(f"service {check['name']}: {check['target'] or 'not configured'} -> {check['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
