#!/usr/bin/env python3
"""Inspect installed langgraph-sdk client exports without network access."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, asdict
from typing import Any

ASYNC_EXPORTS = [
    "LangGraphClient",
    "HttpClient",
    "AssistantsClient",
    "ThreadsClient",
    "RunsClient",
    "CronClient",
    "StoreClient",
]

SYNC_EXPORTS = [
    "SyncLangGraphClient",
    "SyncHttpClient",
    "SyncAssistantsClient",
    "SyncThreadsClient",
    "SyncRunsClient",
    "SyncCronClient",
    "SyncStoreClient",
]

UTILITY_EXPORTS = [
    "_aencode_json",
    "_adecode_json",
    "_encode_json",
    "_decode_json",
    "configure_loopback_transports",
]

FACTORY_EXPORTS = ["get_client", "get_sync_client"]
AUTH_ENV_ORDER = ["LANGGRAPH_API_KEY", "LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"]


@dataclass
class ExportReport:
    ok: bool
    package_imported: bool
    client_module_imported: bool
    missing_exports: list[str]
    non_callable_factories: list[str]
    async_exports: list[str]
    sync_exports: list[str]
    utility_exports: list[str]
    auth_env_order: list[str]
    notes: list[str]


def inspect_exports() -> ExportReport:
    notes: list[str] = []
    missing: list[str] = []
    non_callable_factories: list[str] = []

    try:
        package = importlib.import_module("langgraph_sdk")
        package_imported = True
    except Exception as exc:  # pragma: no cover - depends on user environment
        return ExportReport(
            ok=False,
            package_imported=False,
            client_module_imported=False,
            missing_exports=FACTORY_EXPORTS + ASYNC_EXPORTS + SYNC_EXPORTS + UTILITY_EXPORTS,
            non_callable_factories=[],
            async_exports=[],
            sync_exports=[],
            utility_exports=[],
            auth_env_order=AUTH_ENV_ORDER,
            notes=[f"Failed to import langgraph_sdk: {exc!r}"],
        )

    try:
        client_module = importlib.import_module("langgraph_sdk.client")
        client_module_imported = True
    except Exception as exc:  # pragma: no cover - depends on user environment
        return ExportReport(
            ok=False,
            package_imported=package_imported,
            client_module_imported=False,
            missing_exports=FACTORY_EXPORTS + ASYNC_EXPORTS + SYNC_EXPORTS + UTILITY_EXPORTS,
            non_callable_factories=[],
            async_exports=[],
            sync_exports=[],
            utility_exports=[],
            auth_env_order=AUTH_ENV_ORDER,
            notes=[f"Failed to import langgraph_sdk.client: {exc!r}"],
        )

    for name in FACTORY_EXPORTS:
        if not hasattr(package, name):
            missing.append(f"langgraph_sdk.{name}")
        elif not callable(getattr(package, name)):
            non_callable_factories.append(f"langgraph_sdk.{name}")
        if not hasattr(client_module, name):
            missing.append(f"langgraph_sdk.client.{name}")
        elif not callable(getattr(client_module, name)):
            non_callable_factories.append(f"langgraph_sdk.client.{name}")

    present_async = _present_names(client_module, ASYNC_EXPORTS, missing)
    present_sync = _present_names(client_module, SYNC_EXPORTS, missing)
    present_utils = _present_names(client_module, UTILITY_EXPORTS, missing)

    if package_imported and client_module_imported:
        notes.append("No server connection attempted; this is an import/export smoke check only.")

    ok = not missing and not non_callable_factories
    return ExportReport(
        ok=ok,
        package_imported=package_imported,
        client_module_imported=client_module_imported,
        missing_exports=missing,
        non_callable_factories=non_callable_factories,
        async_exports=present_async,
        sync_exports=present_sync,
        utility_exports=present_utils,
        auth_env_order=AUTH_ENV_ORDER,
        notes=notes,
    )


def _present_names(module: Any, names: list[str], missing: list[str]) -> list[str]:
    present: list[str] = []
    for name in names:
        if hasattr(module, name):
            present.append(name)
        else:
            missing.append(f"langgraph_sdk.client.{name}")
    return present


def print_text(report: ExportReport) -> None:
    if report.ok:
        print("OK: langgraph-sdk client exports available")
    else:
        print("FAIL: langgraph-sdk client export check failed")

    print(f"package_imported: {report.package_imported}")
    print(f"client_module_imported: {report.client_module_imported}")
    print(f"auth_env_order: {', '.join(report.auth_env_order)}")
    print(f"async_exports: {', '.join(report.async_exports) or '(none)'}")
    print(f"sync_exports: {', '.join(report.sync_exports) or '(none)'}")
    print(f"utility_exports: {', '.join(report.utility_exports) or '(none)'}")

    if report.missing_exports:
        print("missing_exports:")
        for name in report.missing_exports:
            print(f"  - {name}")
    if report.non_callable_factories:
        print("non_callable_factories:")
        for name in report.non_callable_factories:
            print(f"  - {name}")
    for note in report.notes:
        print(f"note: {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect installed langgraph-sdk client exports without credentials or network calls."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    report = inspect_exports()
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
