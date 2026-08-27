#!/usr/bin/env python3
"""Read-only RAGFlow deployment configuration validator."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ALLOWED_DOCKER_ENGINES = {"elasticsearch", "infinity", "opensearch", "oceanbase", "seekdb"}
ALLOWED_HELM_ENGINES = {"elasticsearch", "infinity", "opensearch"}
ALLOWED_DEVICES = {"cpu", "gpu"}
DEFAULT_SECRET_VALUES = {
    "infini_rag_flow",
    "infini_rag_flow_OS_01",
    "infini_rag_flow_helm",
    "rag_flow",
    "xxx",
}
ACTIVE_PORTS = {
    "always": [
        "SVR_WEB_HTTP_PORT",
        "SVR_WEB_HTTPS_PORT",
        "SVR_HTTP_PORT",
        "ADMIN_SVR_HTTP_PORT",
        "SVR_MCP_PORT",
        "GO_HTTP_PORT",
        "GO_ADMIN_PORT",
        "EXPOSE_MYSQL_PORT",
        "MINIO_PORT",
        "MINIO_CONSOLE_PORT",
        "REDIS_PORT",
    ],
    "elasticsearch": ["ES_PORT", "KIBANA_PORT"],
    "opensearch": ["OS_PORT"],
    "infinity": ["INFINITY_THRIFT_PORT", "INFINITY_HTTP_PORT", "INFINITY_PSQL_PORT"],
    "oceanbase": ["OCEANBASE_PORT"],
    "seekdb": ["SEEKDB_PORT"],
    "ragflow-go": ["NATS_PORT"],
    "tei-cpu": ["TEI_PORT"],
    "tei-gpu": ["TEI_PORT"],
}


class Report:
    def __init__(self) -> None:
        self.infos: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def print(self) -> None:
        for label, items in (("INFO", self.infos), ("WARN", self.warnings), ("ERROR", self.errors)):
            for item in items:
                print(f"{label}: {item}")
        print(
            f"Summary: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), {len(self.infos)} info message(s)."
        )


_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")
_ENV_LINE_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def strip_inline_comment(value: str) -> str:
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def expand_shell_defaults(value: str, env: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        default = match.group(2)
        current = env.get(key, os.environ.get(key, ""))
        if current:
            return current
        return default or ""

    previous = None
    current = value
    for _ in range(10):
        if current == previous:
            break
        previous = current
        current = _VAR_PATTERN.sub(replace, current)
    return current


def parse_dotenv(text: str, report: Report) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_LINE_PATTERN.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        value = strip_quotes(strip_inline_comment(raw_value))
        env[key] = expand_shell_defaults(value, env)
    if env:
        report.info(f"Loaded {len(env)} key(s) from env-style file.")
    return env


def parse_values_env_block(text: str, report: Report) -> Dict[str, str]:
    env: Dict[str, str] = {}
    in_env = False
    env_indent: Optional[int] = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        stripped = raw_line.strip()
        if stripped == "env:":
            in_env = True
            env_indent = indent
            continue
        if in_env and env_indent is not None and indent <= env_indent:
            break
        if not in_env:
            continue
        if stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        value = strip_quotes(strip_inline_comment(raw_value))
        if value:
            env[key] = expand_shell_defaults(value, env)
    if env:
        report.info(f"Loaded {len(env)} key(s) from values.yaml env block.")
    return env


def load_env_file(path: Path, report: Report) -> Tuple[Dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    env = parse_dotenv(text, report)
    if not env and re.search(r"^env:\s*$", text, flags=re.MULTILINE):
        env = parse_values_env_block(text, report)
    if not env:
        report.warn(f"No environment keys parsed from {path}.")
    return env, text


def render_template(text: str, env: Dict[str, str]) -> str:
    return expand_shell_defaults(text, env)


def split_profiles(value: str) -> List[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def get_env(env: Dict[str, str], key: str, default: str = "") -> str:
    return env.get(key, default).strip()


def section_block(text: str, name: str) -> str:
    pattern = re.compile(rf"^{re.escape(name)}:\s*\n((?:[ \t]+.*\n|\s*\n)*)", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1) if match else ""


def first_section_value(text: str, section: str, key: str) -> str:
    block = section_block(text, section)
    if not block:
        return ""
    pattern = re.compile(rf"^\s+{re.escape(key)}:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(block)
    return strip_quotes(match.group(1)) if match else ""


def require_keys(env: Dict[str, str], keys: Iterable[str], report: Report, context: str) -> None:
    for key in keys:
        if not get_env(env, key):
            report.warn(f"{context}: {key} is unset or empty.")


def validate_doc_engine(env: Dict[str, str], rendered_conf: str, deployment: str, report: Report) -> str:
    doc_engine = get_env(env, "DOC_ENGINE", "infinity" if deployment == "helm" else "elasticsearch").lower()
    allowed = ALLOWED_HELM_ENGINES if deployment == "helm" else ALLOWED_DOCKER_ENGINES
    if doc_engine not in allowed:
        report.error(f"DOC_ENGINE={doc_engine!r} is not supported for {deployment}; allowed: {', '.join(sorted(allowed))}.")
        return doc_engine

    if deployment != "helm":
        device = get_env(env, "DEVICE", "cpu").lower()
        if device not in ALLOWED_DEVICES:
            report.error(f"DEVICE={device!r} is invalid; expected cpu or gpu.")
        profiles = split_profiles(get_env(env, "COMPOSE_PROFILES", f"{doc_engine},{device}"))
        if doc_engine not in profiles:
            report.error(f"COMPOSE_PROFILES does not include selected DOC_ENGINE={doc_engine}.")
        if device and device not in profiles:
            report.warn(f"COMPOSE_PROFILES does not include selected DEVICE={device}.")

    engine_requirements = {
        "elasticsearch": ("es", ["ES_HOST", "ES_PORT", "ELASTIC_PASSWORD"]),
        "infinity": ("infinity", ["INFINITY_HOST", "INFINITY_THRIFT_PORT"]),
        "opensearch": ("os", ["OS_HOST", "OS_PORT", "OPENSEARCH_PASSWORD"]),
        "oceanbase": ("oceanbase", ["OCEANBASE_HOST", "OCEANBASE_PORT", "OCEANBASE_USER", "OCEANBASE_PASSWORD"]),
        "seekdb": ("seekdb", ["SEEKDB_HOST", "SEEKDB_PORT", "SEEKDB_USER", "SEEKDB_PASSWORD"]),
    }
    section, keys = engine_requirements.get(doc_engine, ("", []))
    if deployment == "helm" and not rendered_conf:
        secret_keys = [key for key in keys if "PASSWORD" in key]
        require_keys(env, secret_keys, report, f"DOC_ENGINE={doc_engine}")
        report.info("Helm chart templates selected engine host and port variables during rendering.")
    else:
        require_keys(env, keys, report, f"DOC_ENGINE={doc_engine}")
    if rendered_conf and section and not section_block(rendered_conf, section):
        report.error(f"service config is missing required top-level section {section!r} for DOC_ENGINE={doc_engine}.")
    return doc_engine


def validate_credentials(env: Dict[str, str], rendered_conf: str, report: Report) -> None:
    checks = [
        ("mysql", "password", "MYSQL_PASSWORD"),
        ("mysql", "name", "MYSQL_DBNAME"),
        ("minio", "user", "MINIO_USER"),
        ("minio", "password", "MINIO_PASSWORD"),
        ("redis", "password", "REDIS_PASSWORD"),
        ("es", "password", "ELASTIC_PASSWORD"),
        ("os", "password", "OPENSEARCH_PASSWORD"),
    ]
    for section, key, env_key in checks:
        env_value = get_env(env, env_key)
        conf_value = first_section_value(rendered_conf, section, key) if rendered_conf else ""
        if env_value and conf_value and env_value != conf_value:
            report.error(f"{section}.{key}={conf_value!r} does not match {env_key}={env_value!r}.")

    sensitive_keys = [
        "ELASTIC_PASSWORD",
        "OPENSEARCH_PASSWORD",
        "MYSQL_PASSWORD",
        "MINIO_PASSWORD",
        "REDIS_PASSWORD",
        "OCEANBASE_PASSWORD",
        "SEEKDB_PASSWORD",
    ]
    for key in sensitive_keys:
        value = get_env(env, key)
        if value in DEFAULT_SECRET_VALUES:
            report.warn(f"{key} uses a documented default or placeholder value; change it for non-local deployments.")


def validate_ports(env: Dict[str, str], doc_engine: str, report: Report) -> None:
    profiles = set(split_profiles(get_env(env, "COMPOSE_PROFILES", "")))
    active_keys = list(ACTIVE_PORTS["always"])
    active_keys.extend(ACTIVE_PORTS.get(doc_engine, []))
    for profile in profiles:
        active_keys.extend(ACTIVE_PORTS.get(profile, []))

    seen: Dict[str, str] = {}
    for key in dict.fromkeys(active_keys):
        value = get_env(env, key)
        if not value or not value.isdigit():
            continue
        previous = seen.get(value)
        if previous:
            report.warn(f"Host port {value} is assigned to both {previous} and {key}; confirm this is intentional.")
        else:
            seen[value] = key

    minio_port = get_env(env, "MINIO_PORT")
    redis_port = get_env(env, "REDIS_PORT")
    if minio_port and minio_port != "9000":
        report.info("MINIO_PORT is host-facing; service_conf minio.host may still need the backend-reachable API port.")
    if redis_port and redis_port != "6379":
        report.info("REDIS_PORT is host-facing; source-mode service_conf may need a matching backend-reachable Redis port.")


def validate_embedding(env: Dict[str, str], rendered_conf: str, report: Report) -> None:
    profiles = set(split_profiles(get_env(env, "COMPOSE_PROFILES", "")))
    tei_enabled = bool({"tei-cpu", "tei-gpu"} & profiles)
    if tei_enabled:
        require_keys(env, ["TEI_HOST", "TEI_PORT", "TEI_MODEL"], report, "TEI profile")
    if rendered_conf and re.search(r"api_key:\s*['\"]?xxx['\"]?", rendered_conf):
        report.warn("service config still contains placeholder API key value 'xxx' in at least one model/provider section.")
    if rendered_conf and "http://:80" in rendered_conf:
        report.error("service config renders an empty TEI base_url host.")


def validate_mode(env: Dict[str, str], rendered_conf: str, deployment: str, doc_engine: str, report: Report) -> None:
    if deployment == "source":
        report.info("Source mode requires Python 3.13, uv dependencies, base services, PYTHONPATH, API server, and task executor processes.")
        rendered = rendered_conf or ""
        internal_hosts = ["mysql", "minio", "redis", "es01", "infinity", "opensearch01", "oceanbase", "seekdb"]
        used_internal = [host for host in internal_hosts if re.search(rf"\b{re.escape(host)}\b", rendered)]
        if used_internal:
            report.warn(
                "Source mode service config uses Docker-style hostnames "
                f"({', '.join(sorted(set(used_internal)))}); ensure they resolve from the host process or switch to reachable host/ports."
            )
    if deployment == "helm":
        if doc_engine not in ALLOWED_HELM_ENGINES:
            report.error(f"Helm does not support DOC_ENGINE={doc_engine}; choose one of {', '.join(sorted(ALLOWED_HELM_ENGINES))}.")
        report.info("Helm defaults can differ from Docker defaults; verify rendered manifests with helm template before apply.")


def validate_service_conf(rendered_conf: str, report: Report) -> None:
    if not rendered_conf:
        return
    for section in ["ragflow", "mysql", "minio", "redis"]:
        if not section_block(rendered_conf, section):
            report.error(f"service config is missing expected top-level section {section!r}.")
    if "${" in rendered_conf:
        unresolved = sorted(set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)", rendered_conf)))
        if unresolved:
            report.warn(f"service config still contains unresolved placeholders: {', '.join(unresolved)}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate RAGFlow .env/values and service_conf consistency without modifying files or contacting services."
    )
    parser.add_argument("--env", type=Path, help="Path to a Docker .env file or a Helm values.yaml file.")
    parser.add_argument("--service-conf", type=Path, help="Path to service_conf.yaml or service_conf.yaml.template.")
    parser.add_argument(
        "--deployment",
        choices=["docker", "source", "helm"],
        default="docker",
        help="Deployment context for mode-specific checks.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are present.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = Report()

    env: Dict[str, str] = {}
    if args.env:
        if not args.env.exists():
            report.error(f"Env file not found: {args.env}")
        else:
            env, _ = load_env_file(args.env, report)
    else:
        report.warn("No --env file provided; only service-conf structural checks can run.")

    rendered_conf = ""
    if args.service_conf:
        if not args.service_conf.exists():
            report.error(f"Service config file not found: {args.service_conf}")
        else:
            service_text = args.service_conf.read_text(encoding="utf-8")
            rendered_conf = render_template(service_text, env)
            report.info("Loaded and rendered service config with available environment values.")
    else:
        report.warn("No --service-conf file provided; cross-file checks are limited.")

    doc_engine = validate_doc_engine(env, rendered_conf, args.deployment, report)
    validate_service_conf(rendered_conf, report)
    validate_credentials(env, rendered_conf, report)
    validate_ports(env, doc_engine, report)
    validate_embedding(env, rendered_conf, report)
    validate_mode(env, rendered_conf, args.deployment, doc_engine, report)

    report.print()
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
