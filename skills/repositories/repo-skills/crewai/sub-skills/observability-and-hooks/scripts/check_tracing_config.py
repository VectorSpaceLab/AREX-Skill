#!/usr/bin/env python3
"""Inspect CrewAI tracing and observability configuration without sending telemetry.

The script prints selected environment-variable presence/values and package
availability. It does not import or initialize CrewAI tracing listeners, run a
Crew/Flow, contact a network endpoint, or read credential values by default.
"""

from __future__ import annotations

import argparse
from importlib import metadata
import json
import os
from typing import Iterable


CREWAI_ENV_VARS = [
    "CREWAI_TRACING_ENABLED",
    "CREWAI_DISABLE_TELEMETRY",
    "CREWAI_DISABLE_TRACKING",
    "CREWAI_USER_ID",
    "CREWAI_ORG_ID",
    "OTEL_SDK_DISABLED",
]

OTEL_ENV_VARS = [
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "OTEL_SERVICE_NAME",
    "OTEL_RESOURCE_ATTRIBUTES",
]

PROVIDER_ENV_VARS = [
    "DD_API_KEY",
    "DD_SITE",
    "DD_LLMOBS_ENABLED",
    "DD_LLMOBS_ML_APP",
    "DD_LLMOBS_AGENTLESS_ENABLED",
    "DD_APM_TRACING_ENABLED",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "LANGDB_API_KEY",
    "LANGDB_PROJECT_ID",
    "LANGDB_API_BASE_URL",
    "PHOENIX_CLIENT_HEADERS",
    "PHOENIX_COLLECTOR_ENDPOINT",
    "PATRONUS_API_KEY",
    "PORTKEY_API_KEY",
    "WANDB_API_KEY",
    "OPIK_API_KEY",
    "LANGTRACE_API_KEY",
]

PACKAGES = [
    "crewai",
    "crewai-cli",
    "crewai-tools",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp-proto-http",
    "openlit",
    "ddtrace",
    "langfuse",
    "pylangdb",
    "arize-phoenix-otel",
    "openinference-instrumentation-crewai",
    "portkey-ai",
    "opik",
    "weave",
    "mlflow",
    "patronus",
    "langtrace-python-sdk",
    "braintrust",
]

SENSITIVE_TOKENS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "HEADERS")


def is_sensitive(name: str) -> bool:
    """Return True when an env var name usually contains secret material."""
    upper_name = name.upper()
    return any(token in upper_name for token in SENSITIVE_TOKENS)


def env_status(names: Iterable[str], reveal: bool = False) -> list[dict[str, str | bool | None]]:
    """Return sanitized environment-variable status records."""
    rows: list[dict[str, str | bool | None]] = []
    for name in names:
        value = os.environ.get(name)
        present = value is not None
        if not present:
            display_value: str | None = None
        elif reveal or not is_sensitive(name):
            display_value = value
        else:
            display_value = "<set:redacted>"
        rows.append({"name": name, "present": present, "value": display_value})
    return rows


def package_status(names: Iterable[str]) -> list[dict[str, str | bool | None]]:
    """Return installed package version records without importing packages."""
    rows: list[dict[str, str | bool | None]] = []
    for name in names:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            rows.append({"name": name, "installed": False, "version": None})
        else:
            rows.append({"name": name, "installed": True, "version": version})
    return rows


def summarize_enablement(env: dict[str, str]) -> list[str]:
    """Create human-readable CrewAI tracing/telemetry observations."""
    notes: list[str] = []
    tracing = env.get("CREWAI_TRACING_ENABLED", "").lower()
    if tracing in {"true", "1"}:
        notes.append("CrewAI built-in tracing is enabled by environment when Crew/Flow tracing is not explicitly set.")
    elif tracing in {"false", "0"}:
        notes.append("CrewAI built-in tracing is disabled by environment unless Crew/Flow tracing=True overrides it.")
    else:
        notes.append("CrewAI built-in tracing has no explicit env setting; Crew/Flow tracing or stored consent decides.")

    disabled_by = [
        name
        for name in ("OTEL_SDK_DISABLED", "CREWAI_DISABLE_TELEMETRY", "CREWAI_DISABLE_TRACKING")
        if env.get(name, "").lower() == "true"
    ]
    if disabled_by:
        notes.append("Anonymous/OpenTelemetry telemetry disable switch is active: " + ", ".join(disabled_by) + ".")
    else:
        notes.append("No CrewAI anonymous telemetry disable env var is set to true.")

    endpoint = env.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        if endpoint.endswith(":4317"):
            notes.append("OTLP endpoint looks like a gRPC port; verify protocol if using an HTTP exporter.")
        elif endpoint.endswith(":4318"):
            notes.append("OTLP endpoint looks like the common HTTP collector port; verify provider path expectations.")
        else:
            notes.append("OTLP endpoint is set; verify protocol, path, and collector reachability separately.")

    return notes


def build_report(reveal: bool = False) -> dict[str, object]:
    """Build the full diagnostic report."""
    env_snapshot = dict(os.environ)
    return {
        "summary": summarize_enablement(env_snapshot),
        "environment": {
            "crewai": env_status(CREWAI_ENV_VARS, reveal=reveal),
            "otel": env_status(OTEL_ENV_VARS, reveal=reveal),
            "providers": env_status(PROVIDER_ENV_VARS, reveal=reveal),
        },
        "packages": package_status(PACKAGES),
        "safety": [
            "No CrewAI workload was run.",
            "No provider SDK was initialized.",
            "No network request was made.",
            "Sensitive env vars are redacted unless --reveal-values is used.",
        ],
    }


def print_text(report: dict[str, object]) -> None:
    """Print a compact text report."""
    print("CrewAI observability configuration check")
    print("\nSummary:")
    for note in report["summary"]:  # type: ignore[index]
        print(f"- {note}")

    environment = report["environment"]  # type: ignore[assignment]
    for group_name, rows in environment.items():  # type: ignore[union-attr]
        print(f"\nEnvironment: {group_name}")
        for row in rows:
            marker = "set" if row["present"] else "unset"
            value = row["value"]
            if value is None:
                print(f"- {row['name']}: {marker}")
            else:
                print(f"- {row['name']}: {marker} ({value})")

    print("\nPackages:")
    for row in report["packages"]:  # type: ignore[index]
        if row["installed"]:
            print(f"- {row['name']}: installed ({row['version']})")
        else:
            print(f"- {row['name']}: not installed")

    print("\nSafety:")
    for note in report["safety"]:  # type: ignore[index]
        print(f"- {note}")


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Inspect CrewAI tracing/observability env vars and package availability without sending telemetry.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--reveal-values",
        action="store_true",
        help="Print raw values for sensitive env vars. Avoid this in shared logs.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the diagnostic command."""
    args = parse_args()
    report = build_report(reveal=args.reveal_values)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
