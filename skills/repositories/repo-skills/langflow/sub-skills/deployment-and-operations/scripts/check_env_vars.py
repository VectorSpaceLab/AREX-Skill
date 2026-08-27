#!/usr/bin/env python3
"""Validate common Langflow environment variables without importing Langflow."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

BOOLEAN_NAMES = {
    "DO_NOT_TRACK",
    "LANGFLOW_ALLOW_COMPONENTS_PATHS_OVERRIDE",
    "LANGFLOW_ALLOW_CUSTOM_COMPONENTS",
    "LANGFLOW_ALEMBIC_LOG_TO_STDOUT",
    "LANGFLOW_AUTO_LOGIN",
    "LANGFLOW_AUTO_SAVING",
    "LANGFLOW_BACKEND_ONLY",
    "LANGFLOW_CELERY_ENABLED",
    "LANGFLOW_CREATE_STARTER_PROJECTS",
    "LANGFLOW_DATABASE_CONNECTION_RETRY",
    "LANGFLOW_DEACTIVATE_TRACING",
    "LANGFLOW_DEV",
    "LANGFLOW_EMBEDDED_MODE",
    "LANGFLOW_ENABLE_SUPERUSER_CLI",
    "LANGFLOW_FALLBACK_TO_ENV_VAR",
    "LANGFLOW_GUNICORN_PRELOAD",
    "LANGFLOW_HIDE_GETTING_STARTED_PROGRESS",
    "LANGFLOW_HIDE_LOGOUT_BUTTON",
    "LANGFLOW_HIDE_NEW_FLOW_BUTTON",
    "LANGFLOW_HIDE_NEW_PROJECT_BUTTON",
    "LANGFLOW_HIDE_STARTER_PROJECTS",
    "LANGFLOW_LAZY_LOAD_COMPONENTS",
    "LANGFLOW_LOAD_FLOWS_OVERWRITE_ON_NAME_MATCH",
    "LANGFLOW_OPEN_BROWSER",
    "LANGFLOW_PROMETHEUS_ENABLED",
    "LANGFLOW_REMOVE_API_KEYS",
    "LANGFLOW_SAVE_DB_IN_CONFIG_DIR",
    "LANGFLOW_SKIP_AUTH_AUTO_LOGIN",
    "LANGFLOW_STORE_ENVIRONMENT_VARIABLES",
    "LANGFLOW_UPDATE_STARTER_PROJECTS",
}

INTEGER_NAMES = {
    "LANGFLOW_AUTO_SAVING_INTERVAL",
    "LANGFLOW_HEALTH_CHECK_MAX_RETRIES",
    "LANGFLOW_MAX_FILE_SIZE_UPLOAD",
    "LANGFLOW_MAX_ITEMS_LENGTH",
    "LANGFLOW_MAX_TEXT_LENGTH",
    "LANGFLOW_MAX_TRANSACTIONS_TO_KEEP",
    "LANGFLOW_MAX_VERTEX_BUILDS_PER_VERTEX",
    "LANGFLOW_MAX_VERTEX_BUILDS_TO_KEEP",
    "LANGFLOW_PORT",
    "LANGFLOW_PROMETHEUS_PORT",
    "LANGFLOW_PUBLIC_FLOW_CLEANUP_INTERVAL",
    "LANGFLOW_PUBLIC_FLOW_EXPIRATION",
    "LANGFLOW_REDIS_QUEUE_CANCEL_MARKER_TTL",
    "LANGFLOW_REDIS_QUEUE_DB",
    "LANGFLOW_REDIS_QUEUE_PORT",
    "LANGFLOW_REDIS_QUEUE_TTL",
    "LANGFLOW_WORKER_TIMEOUT",
    "LANGFLOW_WORKERS",
}

FLOAT_NAMES = {
    "LANGFLOW_REDIS_QUEUE_POLLING_STALE_THRESHOLD_S",
    "LANGFLOW_REDIS_QUEUE_POLLING_WATCHDOG_INTERVAL_S",
    "LANGFLOW_REDIS_QUEUE_STARTUP_GRACE_S",
}

KNOWN_LANGFLOW_NAMES = BOOLEAN_NAMES | INTEGER_NAMES | FLOAT_NAMES | {
    "LANGFLOW_ALGORITHM",
    "LANGFLOW_BUNDLE_URLS",
    "LANGFLOW_CACHE_TYPE",
    "LANGFLOW_COMPONENTS_INDEX_PATH",
    "LANGFLOW_COMPONENTS_PATH",
    "LANGFLOW_CONFIG_DIR",
    "LANGFLOW_DATABASE_URL",
    "LANGFLOW_EVENT_DELIVERY",
    "LANGFLOW_FRONTEND_PATH",
    "LANGFLOW_FS_TOOL_BASE_DIR",
    "LANGFLOW_HOST",
    "LANGFLOW_JOB_QUEUE_TYPE",
    "LANGFLOW_LANGCHAIN_CACHE",
    "LANGFLOW_LOAD_FLOWS_PATH",
    "LANGFLOW_LOG_DIR",
    "LANGFLOW_LOG_ENV",
    "LANGFLOW_LOG_FILE",
    "LANGFLOW_LOG_FORMAT",
    "LANGFLOW_LOG_LEVEL",
    "LANGFLOW_LOG_LEVELS",
    "LANGFLOW_LOG_REDACT_KEYS",
    "LANGFLOW_LOG_RETRIEVER_BUFFER_SIZE",
    "LANGFLOW_REDIS_HOST",
    "LANGFLOW_REDIS_PORT",
    "LANGFLOW_REDIS_QUEUE_HOST",
    "LANGFLOW_REDIS_QUEUE_URL",
    "LANGFLOW_SECRET_KEY",
    "LANGFLOW_SSL_CERT_FILE",
    "LANGFLOW_SSL_KEY_FILE",
    "LANGFLOW_SSL_CERT_FILE_PATH",
    "LANGFLOW_SSL_KEY_FILE_PATH",
    "LANGFLOW_STORAGE_TYPE",
    "LANGFLOW_SUPERUSER",
    "LANGFLOW_SUPERUSER_PASSWORD",
    "LANGFLOW_SUPERUSER_TOKEN",
}

POSTGRES_SCHEMES = {"postgresql", "postgresql+psycopg", "postgresql+psycopg2", "postgres"}
SQLITE_SCHEMES = {"sqlite"}
TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}
SENSITIVE_PATTERNS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS")
KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate common Langflow LANGFLOW_* variables and database URLs from "
            "a .env file or the current process environment. This check is offline "
            "and does not import Langflow."
        )
    )
    parser.add_argument("--env-file", type=Path, help="Path to a .env file to validate.")
    parser.add_argument(
        "--context",
        choices=("local", "docker", "docker-compose", "systemd"),
        default="local",
        help="Runtime context used for host/database warnings. Default: local.",
    )
    parser.add_argument(
        "--include-process-env",
        action="store_true",
        help="Merge current process environment with the .env file; .env values win on duplicates.",
    )
    parser.add_argument(
        "--strict-unknown",
        action="store_true",
        help="Treat unknown LANGFLOW_* variables as errors instead of warnings.",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Print non-sensitive parsed values in the summary. Sensitive values are always redacted.",
    )
    return parser.parse_args()


def strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    result: list[str] = []
    for char in value:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            result.append(char)
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            result.append(char)
            continue
        if char == "#" and quote is None:
            break
        result.append(char)
    return "".join(result).strip()


def unquote(value: str) -> str:
    value = strip_inline_comment(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value


def parse_env_file(path: Path) -> tuple[dict[str, str], list[Finding]]:
    findings: list[Finding] = []
    values: dict[str, str] = {}
    if not path.exists():
        return values, [Finding("error", f".env file does not exist: {path}")]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return values, [Finding("error", f"could not read .env file {path}: {exc}")]

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            findings.append(Finding("error", f"line {line_number}: expected KEY=VALUE syntax"))
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not KEY_PATTERN.match(key):
            findings.append(Finding("error", f"line {line_number}: invalid environment variable name {key!r}"))
            continue
        if key in values:
            findings.append(Finding("warning", f"line {line_number}: duplicate {key}; later value overrides earlier value"))
        values[key] = unquote(raw_value)
    return values, findings


def is_sensitive(name: str) -> bool:
    return any(pattern in name.upper() for pattern in SENSITIVE_PATTERNS)


def as_bool(value: str) -> bool | None:
    lowered = value.strip().lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    return None


def validate_known_values(values: dict[str, str], strict_unknown: bool) -> list[Finding]:
    findings: list[Finding] = []
    for name, value in sorted(values.items()):
        if name.startswith("LANGFLOW_") and name not in KNOWN_LANGFLOW_NAMES:
            level = "error" if strict_unknown else "warning"
            findings.append(Finding(level, f"{name}: unknown LANGFLOW_* variable; check spelling or update the helper allow-list"))
        if name in BOOLEAN_NAMES and as_bool(value) is None:
            findings.append(Finding("error", f"{name}: expected a boolean such as true/false, 1/0, yes/no; got {value!r}"))
        if name in INTEGER_NAMES:
            try:
                parsed = int(value)
            except ValueError:
                findings.append(Finding("error", f"{name}: expected an integer; got {value!r}"))
            else:
                if parsed < 0:
                    findings.append(Finding("warning", f"{name}: negative values are rarely valid; got {parsed}"))
        if name in FLOAT_NAMES:
            try:
                parsed_float = float(value)
            except ValueError:
                findings.append(Finding("error", f"{name}: expected a number; got {value!r}"))
            else:
                if parsed_float < 0:
                    findings.append(Finding("error", f"{name}: must not be negative; got {parsed_float}"))

    log_level = values.get("LANGFLOW_LOG_LEVEL")
    if log_level and log_level.lower() not in {"debug", "info", "warning", "error", "critical"}:
        findings.append(Finding("warning", f"LANGFLOW_LOG_LEVEL: unusual level {log_level!r}"))

    job_queue = values.get("LANGFLOW_JOB_QUEUE_TYPE")
    workers = int(values.get("LANGFLOW_WORKERS", "1")) if values.get("LANGFLOW_WORKERS", "1").isdigit() else 1
    if workers > 1 and job_queue != "redis":
        findings.append(Finding("error", "LANGFLOW_WORKERS > 1 requires LANGFLOW_JOB_QUEUE_TYPE=redis for shared job coordination"))
    if job_queue == "redis" and not any(values.get(name) for name in ("LANGFLOW_REDIS_QUEUE_URL", "LANGFLOW_REDIS_QUEUE_HOST", "LANGFLOW_REDIS_HOST")):
        findings.append(Finding("warning", "LANGFLOW_JOB_QUEUE_TYPE=redis is set but no Redis queue host or URL was found"))
    if values.get("LANGFLOW_REDIS_QUEUE_URL", "").startswith("redis://") and re.search(r"redis://[^@/:]+:[^@]+@", values["LANGFLOW_REDIS_QUEUE_URL"]):
        findings.append(Finding("warning", "LANGFLOW_REDIS_QUEUE_URL contains credentials over redis://; use rediss:// when TLS is required"))

    auto_login = as_bool(values.get("LANGFLOW_AUTO_LOGIN", ""))
    if auto_login is False:
        if not values.get("LANGFLOW_SUPERUSER"):
            findings.append(Finding("warning", "LANGFLOW_AUTO_LOGIN=False but LANGFLOW_SUPERUSER is not set"))
        if not values.get("LANGFLOW_SUPERUSER_PASSWORD"):
            findings.append(Finding("warning", "LANGFLOW_AUTO_LOGIN=False but LANGFLOW_SUPERUSER_PASSWORD is not set"))
    if auto_login is True:
        findings.append(Finding("warning", "LANGFLOW_AUTO_LOGIN=True grants broad visual-editor access; protect public deployments with network or proxy controls"))

    secret_key = values.get("LANGFLOW_SECRET_KEY")
    if secret_key is None:
        findings.append(Finding("warning", "LANGFLOW_SECRET_KEY is not set; use a stable strong secret for shared or persistent deployments"))
    elif len(secret_key) < 24 or secret_key.lower() in {"secret", "changeme", "change-me", "replace-me", "password"}:
        findings.append(Finding("error", "LANGFLOW_SECRET_KEY appears too short or placeholder-like"))

    if as_bool(values.get("LANGFLOW_REMOVE_API_KEYS", "false")) is True:
        findings.append(Finding("warning", "LANGFLOW_REMOVE_API_KEYS=True strips API keys/tokens from saved flows; confirm this is intentional"))

    return findings


def validate_database_url(values: dict[str, str], context: str) -> list[Finding]:
    findings: list[Finding] = []
    db_url = values.get("LANGFLOW_DATABASE_URL", "").strip()
    if not db_url:
        return findings

    parsed = urlparse(db_url)
    scheme = parsed.scheme.lower()
    if scheme in SQLITE_SCHEMES:
        if db_url in {"sqlite://", "sqlite:///", "sqlite:///:memory:"}:
            findings.append(Finding("warning", "LANGFLOW_DATABASE_URL uses transient or incomplete SQLite storage"))
        elif not db_url.startswith("sqlite:////") and not re.match(r"sqlite:///[A-Za-z]:/", db_url):
            findings.append(Finding("error", "SQLite LANGFLOW_DATABASE_URL should use an absolute path: sqlite:////absolute/path/langflow.db"))
        path = parsed.path
        if path and path != "/:memory:":
            sqlite_path = Path(path)
            if not sqlite_path.parent.exists():
                findings.append(Finding("warning", f"SQLite parent directory does not exist yet: {sqlite_path.parent}"))
        if context in {"docker", "docker-compose"}:
            findings.append(Finding("warning", "SQLite in containers is suitable only when its directory is mounted on a persistent volume"))
        return findings

    if scheme in POSTGRES_SCHEMES:
        if not parsed.hostname:
            findings.append(Finding("error", "PostgreSQL LANGFLOW_DATABASE_URL is missing a hostname"))
        if not parsed.path or parsed.path == "/":
            findings.append(Finding("error", "PostgreSQL LANGFLOW_DATABASE_URL is missing a database name"))
        if not parsed.username:
            findings.append(Finding("warning", "PostgreSQL LANGFLOW_DATABASE_URL has no username"))
        if parsed.password is None:
            findings.append(Finding("warning", "PostgreSQL LANGFLOW_DATABASE_URL has no password; confirm auth method is intentional"))
        if context == "docker-compose" and parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
            findings.append(Finding("error", "In Docker Compose, LANGFLOW_DATABASE_URL should normally use the database service name, not localhost"))
        if context == "docker" and parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
            findings.append(Finding("warning", "Inside Docker, localhost points to the Langflow container; use a reachable database host or network alias"))
        return findings

    findings.append(Finding("warning", f"LANGFLOW_DATABASE_URL uses unrecognized scheme {scheme!r}; expected sqlite or postgresql"))
    return findings


def validate_paths(values: dict[str, str], context: str) -> list[Finding]:
    findings: list[Finding] = []
    config_dir = values.get("LANGFLOW_CONFIG_DIR")
    if context in {"docker", "docker-compose"}:
        if not config_dir:
            findings.append(Finding("warning", "Set LANGFLOW_CONFIG_DIR and mount it on a persistent volume for container deployments"))
        elif not config_dir.startswith("/"):
            findings.append(Finding("warning", "Container LANGFLOW_CONFIG_DIR is usually an absolute in-container path such as /app/langflow"))
    elif config_dir and not Path(config_dir).is_absolute():
        findings.append(Finding("warning", "Local LANGFLOW_CONFIG_DIR is relative; use an absolute path for service managers and durable deployments"))

    host = values.get("LANGFLOW_HOST")
    if context in {"docker", "docker-compose"} and host in {"localhost", "127.0.0.1"}:
        findings.append(Finding("warning", "Container LANGFLOW_HOST should usually be 0.0.0.0 so published ports can reach the server"))

    log_file = values.get("LANGFLOW_LOG_FILE")
    log_dir = values.get("LANGFLOW_LOG_DIR")
    if log_file and log_dir:
        try:
            Path(log_file).resolve().relative_to(Path(log_dir).resolve())
        except ValueError:
            findings.append(Finding("warning", "LANGFLOW_LOG_FILE is not inside LANGFLOW_LOG_DIR; file log collectors may miss it"))
    return findings


def load_values(args: argparse.Namespace) -> tuple[dict[str, str], list[Finding]]:
    values: dict[str, str] = {}
    findings: list[Finding] = []
    if args.include_process_env or args.env_file is None:
        values.update(os.environ)
    if args.env_file is not None:
        parsed, parse_findings = parse_env_file(args.env_file)
        findings.extend(parse_findings)
        values.update(parsed)
    return values, findings


def sanitize_value(name: str, value: str) -> str:
    if is_sensitive(name):
        return "<redacted>"
    if name.endswith("_URL"):
        parsed = urlparse(value)
        if parsed.password is not None:
            username = parsed.username or ""
            auth = f"{username}:<redacted>@" if username else "<redacted>@"
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            return parsed._replace(netloc=f"{auth}{host}{port}").geturl()
    return value


def print_summary(values: dict[str, str], findings: list[Finding], show_values: bool) -> None:
    langflow_values = {key: value for key, value in sorted(values.items()) if key.startswith("LANGFLOW_") or key == "DO_NOT_TRACK"}
    print(f"Checked {len(langflow_values)} Langflow-related variable(s).")
    if show_values and langflow_values:
        print("\nValues:")
        for key, value in langflow_values.items():
            print(f"  {key}={sanitize_value(key, value)}")
    if findings:
        print("\nFindings:")
        for finding in findings:
            print(f"  [{finding.level.upper()}] {finding.message}")
    else:
        print("No issues found.")


def main() -> int:
    args = parse_args()
    values, findings = load_values(args)
    findings.extend(validate_known_values(values, args.strict_unknown))
    findings.extend(validate_database_url(values, args.context))
    findings.extend(validate_paths(values, args.context))
    print_summary(values, findings, args.show_values)
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
