#!/usr/bin/env python3
"""Inspect ADK tooling APIs and optional integration extras safely.

This diagnostic performs local imports and signature inspection only. It does
not start MCP servers, open network connections, read credentials, or write
files. Use it before wiring ADK tools or integration toolsets in an environment.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from importlib import metadata
from typing import Any


CORE_OBJECTS: tuple[tuple[str, str], ...] = (
    ("google.adk.tools", "FunctionTool"),
    ("google.adk.tools", "LongRunningFunctionTool"),
    ("google.adk.tools", "BaseTool"),
    ("google.adk.tools.base_toolset", "BaseToolset"),
    ("google.adk.tools", "ToolContext"),
    ("google.adk.tools", "AgentTool"),
    ("google.adk.tools", "TransferToAgentTool"),
    ("google.adk.auth.auth_tool", "AuthConfig"),
    ("google.adk.auth.auth_credential", "AuthCredential"),
)

OPTIONAL_MODULES: tuple[tuple[str, str, str], ...] = (
    ("mcp", "mcp", "Install/select google-adk[mcp] for MCP toolsets."),
    (
        "extensions_retrieval",
        "google.adk.tools.retrieval",
        "Install/select google-adk[extensions] for extension-backed retrieval helpers.",
    ),
    (
        "google_api_client",
        "googleapiclient.discovery",
        "Install/select google-adk[tools] for Google API discovery clients.",
    ),
    (
        "gcp_bigquery",
        "google.cloud.bigquery",
        "Install/select google-adk[gcp] for BigQuery/cloud toolsets.",
    ),
    (
        "db_sqlalchemy",
        "sqlalchemy",
        "Install/select google-adk[db] for SQLAlchemy-backed persistence.",
    ),
    (
        "a2a_sdk",
        "a2a.types",
        "Install/select google-adk[a2a] for A2A helpers.",
    ),
    (
        "toolbox_sdk",
        "toolbox_core",
        "Install/select google-adk[toolbox] or google-adk[extensions] for ToolboxToolset.",
    ),
)

OPTIONAL_ADK_OBJECTS: tuple[tuple[str, str, str], ...] = (
    (
        "mcp_toolset",
        "google.adk.tools.mcp_tool.mcp_toolset",
        "McpToolset",
    ),
    (
        "mcp_stdio_params",
        "google.adk.tools.mcp_tool.mcp_session_manager",
        "StdioConnectionParams",
    ),
    (
        "openapi_toolset",
        "google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset",
        "OpenAPIToolset",
    ),
    (
        "google_api_toolset",
        "google.adk.tools.google_api_tool.google_api_toolset",
        "GoogleApiToolset",
    ),
    (
        "apihub_toolset",
        "google.adk.tools.apihub_tool.apihub_toolset",
        "APIHubToolset",
    ),
    (
        "application_integration_toolset",
        "google.adk.tools.application_integration_tool.application_integration_toolset",
        "ApplicationIntegrationToolset",
    ),
    (
        "data_agent_toolset",
        "google.adk.tools.data_agent.data_agent_toolset",
        "DataAgentToolset",
    ),
    ("pubsub_toolset", "google.adk.tools.pubsub.pubsub_toolset", "PubSubToolset"),
    (
        "bigtable_toolset",
        "google.adk.tools.bigtable.bigtable_toolset",
        "BigtableToolset",
    ),
    ("spanner_toolset", "google.adk.tools.spanner.spanner_toolset", "SpannerToolset"),
    ("toolbox_toolset", "google.adk.tools.toolbox_toolset", "ToolboxToolset"),
    ("a2a_to_a2a", "google.adk.a2a.utils.agent_to_a2a", "to_a2a"),
)


def _distribution_version() -> str | None:
  for dist_name in ("google-adk", "google_adk"):
    try:
      return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
      continue
  return None


def _safe_import(module_name: str) -> tuple[Any | None, str | None]:
  try:
    return importlib.import_module(module_name), None
  except Exception as exc:  # pylint: disable=broad-exception-caught
    return None, f"{type(exc).__name__}: {exc}"


def _signature_for(module_name: str, attr_name: str) -> dict[str, Any]:
  module, error = _safe_import(module_name)
  if error:
    return {"available": False, "error": error}
  try:
    attr = getattr(module, attr_name)
  except AttributeError as exc:
    return {"available": False, "error": f"AttributeError: {exc}"}

  try:
    target = attr.__init__ if inspect.isclass(attr) else attr
    signature = str(inspect.signature(target))
  except Exception as exc:  # pylint: disable=broad-exception-caught
    signature = f"<signature unavailable: {type(exc).__name__}: {exc}>"
  return {
      "available": True,
      "object": f"{module_name}.{attr_name}",
      "signature": signature,
  }


def _optional_module_status() -> dict[str, dict[str, Any]]:
  statuses: dict[str, dict[str, Any]] = {}
  for key, module_name, hint in OPTIONAL_MODULES:
    module, error = _safe_import(module_name)
    status: dict[str, Any] = {
        "module": module_name,
        "available": error is None,
        "hint": hint,
    }
    if module is not None:
      status["file"] = getattr(module, "__file__", None)
    if error:
      status["error"] = error
    statuses[key] = status
  return statuses


def _optional_adk_object_status() -> dict[str, dict[str, Any]]:
  statuses: dict[str, dict[str, Any]] = {}
  for key, module_name, attr_name in OPTIONAL_ADK_OBJECTS:
    statuses[key] = _signature_for(module_name, attr_name)
  return statuses


def _core_status() -> dict[str, Any]:
  signatures = {
      attr_name: _signature_for(module_name, attr_name)
      for module_name, attr_name in CORE_OBJECTS
  }

  function_tool_probe: dict[str, Any]
  try:
    from google.adk.tools import FunctionTool

    def local_echo(name: str) -> dict[str, str]:
      """Return a local echo response."""
      return {"echo": name}

    tool = FunctionTool(local_echo)
    function_tool_probe = {
        "ok": True,
        "name": tool.name,
        "description": tool.description,
    }
  except Exception as exc:  # pylint: disable=broad-exception-caught
    function_tool_probe = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

  return {"signatures": signatures, "function_tool_probe": function_tool_probe}


def collect_report() -> dict[str, Any]:
  return {
      "python": {
          "version": sys.version.split()[0],
          "implementation": platform.python_implementation(),
      },
      "google_adk": {
          "distribution_version": _distribution_version(),
          "import_root": "google.adk",
      },
      "core": _core_status(),
      "optional_modules": _optional_module_status(),
      "optional_adk_objects": _optional_adk_object_status(),
      "safety": {
          "network": False,
          "credentials_read": False,
          "subprocesses_started": False,
          "files_written": False,
      },
  }


def _print_text(report: dict[str, Any]) -> None:
  version = report["google_adk"]["distribution_version"] or "not installed"
  print(f"google-adk distribution: {version}")
  print(f"python: {report['python']['implementation']} {report['python']['version']}")
  print("\nCore signatures:")
  for name, status in report["core"]["signatures"].items():
    if status["available"]:
      print(f"  OK   {name}{status['signature']}")
    else:
      print(f"  MISS {name}: {status['error']}")

  probe = report["core"]["function_tool_probe"]
  if probe["ok"]:
    print(
        "\nFunctionTool probe: OK "
        f"name={probe['name']!r} description={probe['description']!r}"
    )
  else:
    print(f"\nFunctionTool probe: FAIL {probe['error']}")

  print("\nOptional modules:")
  for key, status in report["optional_modules"].items():
    label = "OK" if status["available"] else "MISS"
    print(f"  {label:<4} {key}: {status['module']}")
    if not status["available"]:
      print(f"       {status['error']}")
      print(f"       {status['hint']}")

  print("\nOptional ADK integration objects:")
  for key, status in report["optional_adk_objects"].items():
    label = "OK" if status["available"] else "MISS"
    if status["available"]:
      print(f"  {label:<4} {key}: {status['signature']}")
    else:
      print(f"  {label:<4} {key}: {status['error']}")

  print("\nSafety: no network, credential reads, subprocesses, or file writes performed.")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description=(
          "Safely inspect installed ADK tool APIs and optional integration extras."
      )
  )
  parser.add_argument(
      "--json",
      action="store_true",
      help="Print the diagnostic report as JSON instead of text.",
  )
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  report = collect_report()
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    _print_text(report)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
