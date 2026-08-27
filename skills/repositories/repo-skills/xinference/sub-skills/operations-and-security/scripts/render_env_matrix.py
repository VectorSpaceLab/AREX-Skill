#!/usr/bin/env python3
"""Print a static Xinference environment matrix without reading live env values.

The output is intentionally synthetic: it is built from code- and doc-backed
defaults only, and it never inspects the current process environment.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EnvVar:
    name: str
    default: str
    meaning: str
    note: str = ""


@dataclass(frozen=True)
class Section:
    title: str
    rows: Sequence[EnvVar]


SECTIONS: Sequence[Section] = (
    Section(
        "Connection defaults",
        (
            EnvVar(
                "XINFERENCE_ENDPOINT",
                "http://127.0.0.1:9997",
                "Client-side default endpoint.",
                "Used by CLI and SDK convenience code.",
            ),
        ),
    ),
    Section(
        "Home, cache, and model source",
        (
            EnvVar(
                "XINFERENCE_HOME",
                "~/.xinference",
                "Base directory for persisted Xinference state.",
                "Other writable paths are derived from this root.",
            ),
            EnvVar(
                "XINFERENCE_LAUNCH_HISTORY_DB_PATH",
                "<XINFERENCE_HOME>/launch_history.db",
                "Web UI launch-history store.",
                "Shared across clients so the history is reusable.",
            ),
            EnvVar(
                "XINFERENCE_MONITOR_CONFIG_DB_PATH",
                "<XINFERENCE_HOME>/monitor_config.db",
                "Persistent monitor configuration store.",
                "Used by the admin monitoring configuration APIs.",
            ),
            EnvVar(
                "XINFERENCE_MODEL_SRC",
                "huggingface",
                "Default model hub for built-ins.",
                "Use `modelscope` when that source is preferred.",
            ),
            EnvVar(
                "XINFERENCE_CSG_TOKEN",
                "unset",
                "CSGHub model-source token.",
                "Only needed when that source is used.",
            ),
            EnvVar(
                "XINFERENCE_CSG_ENDPOINT",
                "https://hub-stg.opencsg.com/",
                "CSGHub endpoint.",
                "Override only when your deployment uses a different endpoint.",
            ),
            EnvVar(
                "XINFERENCE_MODEL_DOWNLOAD_WORKERS",
                "2",
                "Parallel model-download worker count.",
                "Lower values reduce contention on small hosts.",
            ),
            EnvVar(
                "XINFERENCE_DOWNLOAD_MAX_ATTEMPTS",
                "3",
                "Retry budget for model downloads.",
                "Helps with transient network failures.",
            ),
            EnvVar(
                "XINFERENCE_TRUST_REMOTE_CODE",
                "off",
                "Allow model-provided remote code.",
                "Leave off unless the model source is trusted.",
            ),
        ),
    ),
    Section(
        "Health, metrics, and logging",
        (
            EnvVar(
                "XINFERENCE_HEALTH_CHECK_FAILURE_THRESHOLD",
                "5",
                "Failed startup health checks tolerated before startup fails.",
            ),
            EnvVar(
                "XINFERENCE_HEALTH_CHECK_INTERVAL",
                "5",
                "Seconds between startup health checks.",
            ),
            EnvVar(
                "XINFERENCE_HEALTH_CHECK_TIMEOUT",
                "10",
                "Seconds allowed for each startup health check.",
            ),
            EnvVar(
                "XINFERENCE_DISABLE_HEALTH_CHECK",
                "off",
                "Disable startup health checks.",
                "Use only when the surrounding orchestration handles readiness.",
            ),
            EnvVar(
                "XINFERENCE_DISABLE_METRICS",
                "off",
                "Disable the supervisor /metrics endpoint and worker exporter.",
                "When enabled, metrics endpoints disappear rather than being hidden.",
            ),
            EnvVar(
                "XINFERENCE_HTTP_REQUEST_TIMEOUT",
                "120",
                "Maximum seconds to receive a complete HTTP request.",
                "Protects against slow-request abuse.",
            ),
            EnvVar(
                "XINFERENCE_HTTP_TIMEOUT_KEEP_ALIVE",
                "5",
                "Idle keep-alive timeout between requests.",
            ),
            EnvVar(
                "XINFERENCE_HTTP_LIMIT_CONCURRENCY",
                "unset",
                "Concurrent-request cap for the HTTP server.",
                "Unset means unlimited; use with care on public endpoints.",
            ),
            EnvVar(
                "XINFERENCE_TCP_REQUEST_TIMEOUT",
                "5",
                "TCP request timeout used by internal request handling.",
            ),
            EnvVar(
                "XINFERENCE_SSE_PING_ATTEMPTS_SECONDS",
                "600",
                "Server-sent-events keepalive ping interval.",
            ),
            EnvVar(
                "XINFERENCE_LOG_DIR",
                "<XINFERENCE_HOME>/logs",
                "Directory for application and audit logs.",
                "Audit logs live under this directory as `audit.log`.",
            ),
            EnvVar(
                "XINFERENCE_LOG_CONSOLE",
                "true",
                "Mirror logs to the console.",
            ),
            EnvVar(
                "XINFERENCE_LOG_FORMAT",
                "text",
                "Log format.",
                "`json` is available for machine parsing.",
            ),
            EnvVar(
                "XINFERENCE_LOG_DOWNLOAD_PROGRESS",
                "sampled",
                "How download progress is logged when console logging is off.",
                "Use `full` sparingly; it is noisier.",
            ),
            EnvVar(
                "XINFERENCE_LOG_ROTATION",
                "daily+size",
                "Log rotation mode.",
            ),
            EnvVar(
                "XINFERENCE_LOG_RETENTION_DAYS",
                "30",
                "Log retention window.",
            ),
            EnvVar(
                "XINFERENCE_LOG_MAX_BYTES",
                "104857600",
                "Maximum bytes per log file.",
            ),
            EnvVar(
                "XINFERENCE_LOG_BACKUP_COUNT",
                "300",
                "Number of rotated log files kept.",
            ),
        ),
    ),
    Section(
        "OpenTelemetry (optional)",
        (
            EnvVar("XINFERENCE_ENABLE_OTEL", "false", "Enable OTEL export and instrumentation."),
            EnvVar("XINFERENCE_OTLP_BASE_ENDPOINT", "http://localhost:4318", "Base OTLP endpoint."),
            EnvVar("XINFERENCE_OTLP_TRACE_ENDPOINT", "<base>/v1/traces", "Trace export endpoint."),
            EnvVar("XINFERENCE_OTLP_METRIC_ENDPOINT", "<base>/v1/metrics", "Metric export endpoint."),
            EnvVar("XINFERENCE_OTLP_API_KEY", "unset", "Bearer token sent with OTLP requests."),
            EnvVar(
                "XINFERENCE_OTEL_EXPORTER_OTLP_PROTOCOL",
                "http/protobuf",
                "OTLP transport protocol.",
            ),
            EnvVar("XINFERENCE_OTEL_EXPORTER_TYPE", "otlp", "Exporter family selector."),
            EnvVar("XINFERENCE_OTEL_SAMPLING_RATE", "0.1", "Trace sampling rate."),
            EnvVar(
                "XINFERENCE_OTEL_BATCH_EXPORT_SCHEDULE_DELAY",
                "5000",
                "Span processor schedule delay in milliseconds.",
            ),
            EnvVar("XINFERENCE_OTEL_MAX_QUEUE_SIZE", "2048", "Maximum span queue size."),
            EnvVar(
                "XINFERENCE_OTEL_MAX_EXPORT_BATCH_SIZE",
                "512",
                "Maximum spans per export batch.",
            ),
            EnvVar(
                "XINFERENCE_OTEL_METRIC_EXPORT_INTERVAL",
                "60000",
                "Metric export interval in milliseconds.",
            ),
            EnvVar(
                "XINFERENCE_OTEL_BATCH_EXPORT_TIMEOUT",
                "10000",
                "Span export timeout in milliseconds.",
            ),
            EnvVar(
                "XINFERENCE_OTEL_METRIC_EXPORT_TIMEOUT",
                "30000",
                "Metric export timeout in milliseconds.",
            ),
        ),
    ),
    Section(
        "Launch and concurrency",
        (
            EnvVar("XINFERENCE_MAX_TOKENS", "unset", "Global max-token override."),
            EnvVar("XINFERENCE_BATCH_SIZE", "32", "Default server batch size."),
            EnvVar("XINFERENCE_BATCH_INTERVAL", "0.003", "Default batching interval in seconds."),
            EnvVar(
                "XINFERENCE_ALLOW_MULTI_REPLICA_PER_GPU",
                "1",
                "Allow multiple replicas to share one GPU.",
            ),
            EnvVar(
                "XINFERENCE_LAUNCH_STRATEGY",
                "IDLE_FIRST_LAUNCH_STRATEGY",
                "GPU allocation strategy for replicas.",
            ),
            EnvVar(
                "XINFERENCE_MAX_CONCURRENT_LAUNCHES",
                "5",
                "Maximum concurrent model launches per worker.",
            ),
            EnvVar(
                "XINFERENCE_STATUS_GATHER_TIMEOUT",
                "10",
                "Seconds allowed for status collection.",
            ),
            EnvVar(
                "XINFERENCE_STATUS_REPORT_MULTIPLIER",
                "3",
                "Heartbeat multiplier for full status reports.",
            ),
            EnvVar(
                "XINFERENCE_LIST_MODELS_PER_WORKER_TIMEOUT",
                "60",
                "Timeout for per-worker list-models RPCs.",
            ),
            EnvVar(
                "XINFERENCE_LIST_MODELS_DEBOUNCE_SECONDS",
                "3",
                "Debounce window for repeated list-models refreshes.",
            ),
            EnvVar(
                "XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT",
                "unset",
                "Limit on automatic actor-recovery attempts.",
            ),
            EnvVar(
                "XINFERENCE_TEXT_TO_IMAGE_BATCHING_SIZE",
                "unset",
                "Enable text-to-image continuous batching by image size.",
            ),
        ),
    ),
    Section(
        "Frontend",
        (
            EnvVar(
                "XINFERENCE_FRONTEND_DIST_DIR",
                "unset",
                "Serve a custom Web UI static export.",
                "If unset, Xinference uses the bundled export when available.",
            ),
        ),
    ),
    Section(
        "Auth, OIDC, and audit",
        (
            EnvVar(
                "XINFERENCE_AUTH_ADVANCED",
                "1",
                "Enable database-backed authentication.",
                "Set false only for intentionally open deployments.",
            ),
            EnvVar(
                "XINFERENCE_AUTH_DB_PATH",
                "<XINFERENCE_HOME>/auth/auth.db",
                "SQLite database for users, permissions, API keys, and refresh tokens.",
            ),
            EnvVar(
                "XINFERENCE_AUTH_JWT_SECRET_KEY",
                "auto-generated",
                "JWT signing secret.",
                "Persisted on first run when unset.",
            ),
            EnvVar(
                "XINFERENCE_AUTH_ENCRYPTION_KEY",
                "auto-generated",
                "Encryption key for stored API keys.",
                "Persisted on first run when unset.",
            ),
            EnvVar(
                "XINFERENCE_ACCESS_TOKEN_EXPIRE_MINUTES",
                "30",
                "Access-token lifetime in minutes.",
            ),
            EnvVar(
                "XINFERENCE_PASSWORD_MIN_LENGTH",
                "8",
                "Minimum password length enforced by login and reset flows.",
            ),
            EnvVar("XINFERENCE_OIDC_ENABLED", "0", "Enable OIDC single sign-on."),
            EnvVar("XINFERENCE_OIDC_ISSUER", "unset", "OIDC issuer URL."),
            EnvVar("XINFERENCE_OIDC_CLIENT_ID", "unset", "OIDC client ID."),
            EnvVar("XINFERENCE_OIDC_CLIENT_SECRET", "unset", "OIDC client secret."),
            EnvVar("XINFERENCE_OIDC_REDIRECT_URI", "unset", "OIDC callback URL."),
            EnvVar(
                "XINFERENCE_AUDIT_LOG_RETENTION_DAYS",
                "90",
                "Audit-log retention window.",
            ),
            EnvVar(
                "XINFERENCE_AUDIT_ES_INDEX",
                "xinference-audit-*",
                "Elasticsearch index pattern used by audit searches.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_IP_MAX_FAILURES",
                "10",
                "Invalid-key failures allowed per IP.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_IP_WINDOW_SECONDS",
                "300",
                "Time window for the IP failure counter.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_IP_BAN_SECONDS",
                "3600",
                "Ban duration for an IP.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_KEY_MAX_FAILURES",
                "5",
                "Invalid-key failures allowed per IP/key pair.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_KEY_WINDOW_SECONDS",
                "300",
                "Time window for the IP/key failure counter.",
            ),
            EnvVar(
                "XINFERENCE_RATE_LIMIT_KEY_BAN_SECONDS",
                "3600",
                "Ban duration for an IP/key pair.",
            ),
            EnvVar(
                "XINFERENCE_ALLOWED_IPS",
                "unset",
                "Restrict access to selected IPs or CIDR blocks.",
            ),
            EnvVar(
                "XINFERENCE_TRUSTED_PROXIES",
                "unset",
                "Only trust forwarded client-IP headers from these peers.",
            ),
            EnvVar(
                "XINFERENCE_ES_URL",
                "unset",
                "Point audit search and related admin views at Elasticsearch.",
            ),
        ),
    ),
    Section(
        "Virtual env behavior",
        (
            EnvVar(
                "XINFERENCE_ENABLE_VIRTUAL_ENV",
                "1",
                "Enable per-model virtual environments.",
            ),
            EnvVar(
                "XINFERENCE_VIRTUAL_ENV_SKIP_INSTALLED",
                "1",
                "Skip packages already present in system site-packages.",
            ),
            EnvVar(
                "XINFERENCE_VIRTUAL_ENV_OFFLINE_INSTALL",
                "0",
                "Use offline wheel-only installation behavior.",
            ),
        ),
    ),
)


def _escape_md(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", "<br>")


def _format_markdown(sections: Sequence[Section]) -> str:
    lines: list[str] = ["# Xinference environment matrix", ""]
    lines.append(
        "Defaults are static and do not inspect the live process environment."
    )
    lines.append("")
    for section in sections:
        lines.extend([f"## {section.title}", "", "| Variable | Default | Meaning | Note |", "| --- | --- | --- | --- |"])
        for row in section.rows:
            lines.append(
                "| "
                + " | ".join(
                    _escape_md(value)
                    for value in (row.name, row.default, row.meaning, row.note)
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_text(sections: Sequence[Section]) -> str:
    lines: list[str] = [
        "Xinference environment matrix",
        "",
        "Defaults are static and do not inspect the live process environment.",
        "",
    ]
    for section in sections:
        lines.append(section.title)
        lines.append("-" * len(section.title))
        for row in section.rows:
            line = f"- {row.name}: {row.default} — {row.meaning}"
            if row.note:
                line += f" ({row.note})"
            lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="render_env_matrix.py",
        description="Print a static Xinference environment matrix without reading live env values.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "text"),
        default="markdown",
        help="Output format for the matrix.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.format == "markdown":
        output = _format_markdown(SECTIONS)
    else:
        output = _format_text(SECTIONS)
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
