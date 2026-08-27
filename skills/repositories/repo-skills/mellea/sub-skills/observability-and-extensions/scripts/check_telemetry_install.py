#!/usr/bin/env python3
"""Check Mellea observability imports without activating sinks or exporters."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from importlib import metadata
from typing import Any

EXPECTED_MELLEA_VERSION = "0.8.0.dev0"

_FALSE_FLAGS = (
    "MELLEA_GENERATION_CHUNK_EVENTS",
    "MELLEA_LOGGER_INSECURE_HTTP_ALLOWED",
    "MELLEA_LOGS_CONSOLE",
    "MELLEA_LOGS_ENABLED",
    "MELLEA_LOGS_JSON",
    "MELLEA_LOGS_OTLP",
    "MELLEA_METRICS_CONSOLE",
    "MELLEA_METRICS_ENABLED",
    "MELLEA_METRICS_OTLP",
    "MELLEA_METRICS_PROMETHEUS",
    "MELLEA_PRICING_ENABLED",
    "MELLEA_TRACES_CONSOLE",
    "MELLEA_TRACES_CONTENT",
    "MELLEA_TRACES_ENABLED",
    "MELLEA_TRACES_OTLP",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
)

_REMOVE_VARIABLES = (
    "MELLEA_LOGS_FILE",
    "MELLEA_LOGS_WEBHOOK",
    "MELLEA_PRICING_FILE",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_LOGS_EXPORTER",
    "OTEL_METRICS_EXPORTER",
    "OTEL_METRIC_EXPORT_INTERVAL",
    "OTEL_SERVICE_NAME",
    "OTEL_TRACES_EXPORTER",
)


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify Mellea observability imports while forcing tracing, metrics, "
            "OTLP, console/file/webhook logging, pricing, and content capture off."
        )
    )
    parser.add_argument(
        "--require",
        choices=("base", "hooks", "telemetry"),
        default="base",
        help=(
            "Capability that must be installed: base Mellea, hooks (cpex), or "
            "full telemetry (hooks plus OpenTelemetry SDK/exporters)."
        ),
    )
    parser.add_argument(
        "--expected-version",
        default=EXPECTED_MELLEA_VERSION,
        help=(
            "Required Mellea version (default: %(default)s). Pass an empty string "
            "to report the installed version without enforcing it."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a deterministic JSON report instead of human-readable lines.",
    )
    return parser


def _disable_side_effects() -> None:
    """Force all Mellea signal producers and sinks off before importing Mellea."""
    for name in _FALSE_FLAGS:
        os.environ[name] = "false"
    for name in _REMOVE_VARIABLES:
        os.environ.pop(name, None)


def _module_available(name: str) -> bool:
    """Return whether an importable module spec exists without importing it."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _distribution_version(name: str) -> str | None:
    """Return an installed distribution version, or `None` when unavailable."""
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _append_check(report: dict[str, Any], name: str, passed: bool) -> None:
    """Append one named check and record a failure message when needed."""
    report["checks"].append({"name": name, "passed": passed})
    if not passed:
        report["errors"].append(name)


def _check_imports(requirement: str, expected_version: str) -> dict[str, Any]:
    """Run deterministic base and optional-dependency import checks."""
    modules = {
        "cpex.framework": _module_available("cpex.framework"),
        "opentelemetry.api": _module_available("opentelemetry"),
        "opentelemetry.sdk": _module_available("opentelemetry.sdk"),
        "opentelemetry.otlp_logs": _module_available(
            "opentelemetry.exporter.otlp.proto.grpc._log_exporter"
        ),
        "opentelemetry.otlp_metrics": _module_available(
            "opentelemetry.exporter.otlp.proto.grpc.metric_exporter"
        ),
        "opentelemetry.otlp_traces": _module_available(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
        ),
        "opentelemetry.prometheus": _module_available(
            "opentelemetry.exporter.prometheus"
        ),
    }
    report: dict[str, Any] = {
        "checks": [],
        "distribution_versions": {
            "cpex": _distribution_version("cpex"),
            "mellea": _distribution_version("mellea"),
            "opentelemetry-api": _distribution_version("opentelemetry-api"),
            "opentelemetry-sdk": _distribution_version("opentelemetry-sdk"),
        },
        "errors": [],
        "expected_mellea_version": expected_version or None,
        "mellea_version": None,
        "modules": modules,
        "ok": False,
        "requirement": requirement,
        "signals": {
            "metrics_enabled": None,
            "otlp_log_handler_created": None,
            "tracing_enabled": None,
        },
        "sinks_forced_off": True,
    }

    try:
        import mellea
        import mellea.plugins as plugins
        import mellea.telemetry as telemetry
    except Exception as exc:  # pragma: no cover - error reporting path
        report["errors"].append(f"base import failed: {type(exc).__name__}: {exc}")
        return report

    report["mellea_version"] = getattr(mellea, "__version__", None)
    _append_check(report, "import mellea", True)
    _append_check(report, "import mellea.plugins", True)
    _append_check(report, "import mellea.telemetry", True)

    if expected_version:
        _append_check(
            report,
            f"mellea version is {expected_version}",
            report["mellea_version"] == expected_version,
        )

    required_plugin_api = (
        "HookType",
        "Plugin",
        "PluginMode",
        "PluginSet",
        "block",
        "hook",
        "modify",
        "plugin_scope",
        "register",
        "unregister",
    )
    for name in required_plugin_api:
        _append_check(report, f"mellea.plugins.{name}", hasattr(plugins, name))

    required_telemetry_api = (
        "create_counter",
        "create_histogram",
        "get_otlp_log_handler",
        "is_metrics_enabled",
        "is_tracing_enabled",
        "with_context",
    )
    for name in required_telemetry_api:
        _append_check(report, f"mellea.telemetry.{name}", hasattr(telemetry, name))

    try:
        metrics_enabled = bool(telemetry.is_metrics_enabled())
        tracing_enabled = bool(telemetry.is_tracing_enabled())
        handler = telemetry.get_otlp_log_handler()
        counter = telemetry.create_counter("mellea.install_check", unit="{check}")
        histogram = telemetry.create_histogram(
            "mellea.install_check.duration", unit="s"
        )
        counter.add(1, {"result": "probe"})
        histogram.record(0.0, {"result": "probe"})
    except Exception as exc:  # pragma: no cover - error reporting path
        report["errors"].append(
            f"disabled telemetry API check failed: {type(exc).__name__}: {exc}"
        )
    else:
        report["signals"] = {
            "metrics_enabled": metrics_enabled,
            "otlp_log_handler_created": handler is not None,
            "tracing_enabled": tracing_enabled,
        }
        _append_check(report, "metrics remain disabled", not metrics_enabled)
        _append_check(report, "tracing remains disabled", not tracing_enabled)
        _append_check(report, "OTLP log handler is not created", handler is None)
        _append_check(report, "disabled metric instruments are callable", True)

    if requirement in {"hooks", "telemetry"}:
        _append_check(report, "cpex.framework is installed", modules["cpex.framework"])

    if requirement == "telemetry":
        for name in (
            "opentelemetry.api",
            "opentelemetry.sdk",
            "opentelemetry.otlp_logs",
            "opentelemetry.otlp_metrics",
            "opentelemetry.otlp_traces",
            "opentelemetry.prometheus",
        ):
            _append_check(report, f"{name} is installed", modules[name])

    report["ok"] = not report["errors"]
    return report


def _print_human(report: dict[str, Any]) -> None:
    """Print a concise stable human-readable report."""
    state = "OK" if report["ok"] else "FAILED"
    print(f"Mellea observability check: {state}")
    print(f"requirement: {report['requirement']}")
    print(f"mellea version: {report['mellea_version']}")
    print("sinks/exporters: forced off")
    print("optional modules:")
    for name, available in sorted(report["modules"].items()):
        print(f"  {name}: {'available' if available else 'missing'}")
    print("signals:")
    for name, value in sorted(report["signals"].items()):
        print(f"  {name}: {value}")
    if report["errors"]:
        print("failures:")
        for error in report["errors"]:
            print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    """Run the checker and return a process exit status."""
    args = _parser().parse_args(argv)
    _disable_side_effects()
    report = _check_imports(args.require, args.expected_version)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
