#!/usr/bin/env python3
"""Safely inspect ADK runtime-service imports and signatures.

This diagnostic imports base runtime-service classes, prints selected
constructor/method signatures, and reports whether the optional SQLAlchemy DB
session service is available. It does not open databases, read credentials,
start servers, initialize code executors, or call cloud services.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


@dataclass
class ImportResult:
  name: str
  ok: bool
  module: str | None = None
  error: str | None = None


@dataclass
class SignatureResult:
  name: str
  ok: bool
  signature: str | None = None
  error: str | None = None


def _import_attr(module_name: str, attr_name: str) -> tuple[Any | None, ImportResult]:
  qualified = f"{module_name}.{attr_name}"
  try:
    module = importlib.import_module(module_name)
    attr = getattr(module, attr_name)
  except Exception as exc:  # pylint: disable=broad-exception-caught
    return None, ImportResult(name=qualified, ok=False, error=f"{type(exc).__name__}: {exc}")
  return attr, ImportResult(name=qualified, ok=True, module=getattr(attr, "__module__", module_name))


def _signature(target: Any, display_name: str) -> SignatureResult:
  try:
    return SignatureResult(name=display_name, ok=True, signature=str(inspect.signature(target)))
  except Exception as exc:  # pylint: disable=broad-exception-caught
    return SignatureResult(name=display_name, ok=False, error=f"{type(exc).__name__}: {exc}")


def collect() -> dict[str, Any]:
  imports_to_check = [
      ("google.adk", "Runner"),
      ("google.adk.runners", "InMemoryRunner"),
      ("google.adk.apps.app", "App"),
      ("google.adk.sessions", "InMemorySessionService"),
      ("google.adk.memory", "InMemoryMemoryService"),
      ("google.adk.artifacts", "InMemoryArtifactService"),
      ("google.adk.plugins", "BasePlugin"),
      ("google.adk.plugins", "PluginManager"),
      ("google.adk.code_executors", "BaseCodeExecutor"),
      ("google.adk.code_executors", "UnsafeLocalCodeExecutor"),
      ("google.adk.environment", "LocalEnvironment"),
      ("google.adk.telemetry", "TelemetryConfig"),
  ]

  imported: dict[str, Any] = {}
  import_results: list[ImportResult] = []
  for module_name, attr_name in imports_to_check:
    attr, result = _import_attr(module_name, attr_name)
    import_results.append(result)
    if attr is not None:
      imported[result.name] = attr

  optional_db_attr, optional_db_result = _import_attr(
      "google.adk.sessions", "DatabaseSessionService"
  )

  signature_targets = [
      (imported.get("google.adk.Runner"), "Runner"),
      (imported.get("google.adk.runners.InMemoryRunner"), "InMemoryRunner"),
      (imported.get("google.adk.apps.app.App"), "App"),
      (imported.get("google.adk.sessions.InMemorySessionService"), "InMemorySessionService"),
      (imported.get("google.adk.memory.InMemoryMemoryService"), "InMemoryMemoryService"),
      (imported.get("google.adk.artifacts.InMemoryArtifactService"), "InMemoryArtifactService"),
      (imported.get("google.adk.plugins.BasePlugin"), "BasePlugin"),
      (imported.get("google.adk.plugins.PluginManager"), "PluginManager"),
      (optional_db_attr, "DatabaseSessionService"),
  ]

  signature_results: list[SignatureResult] = []
  for target, display_name in signature_targets:
    if target is None:
      signature_results.append(SignatureResult(name=display_name, ok=False, error="not imported"))
    else:
      signature_results.append(_signature(target, display_name))

  runner = imported.get("google.adk.Runner")
  if runner is not None:
    for method_name in ("run", "run_async", "run_live", "run_debug", "close"):
      method = getattr(runner, method_name, None)
      signature_results.append(
          _signature(method, f"Runner.{method_name}")
          if method is not None
          else SignatureResult(name=f"Runner.{method_name}", ok=False, error="not found")
      )

  base_plugin = imported.get("google.adk.plugins.BasePlugin")
  if base_plugin is not None:
    for callback_name in (
        "on_user_message_callback",
        "before_run_callback",
        "on_event_callback",
        "after_run_callback",
        "before_model_callback",
        "after_model_callback",
        "before_tool_callback",
        "after_tool_callback",
        "on_tool_error_callback",
        "close",
    ):
      callback = getattr(base_plugin, callback_name, None)
      signature_results.append(
          _signature(callback, f"BasePlugin.{callback_name}")
          if callback is not None
          else SignatureResult(name=f"BasePlugin.{callback_name}", ok=False, error="not found")
      )

  return {
      "python": sys.version.split()[0],
      "base_imports": [asdict(item) for item in import_results],
      "optional_db_extra": asdict(optional_db_result),
      "signatures": [asdict(item) for item in signature_results],
      "safety": {
          "opens_databases": False,
          "reads_credentials": False,
          "starts_network_services": False,
          "starts_code_executors": False,
      },
  }


def print_text(report: dict[str, Any]) -> None:
  print(f"Python: {report['python']}")
  print("\nBase runtime imports:")
  for item in report["base_imports"]:
    status = "ok" if item["ok"] else "missing"
    detail = item.get("module") or item.get("error") or ""
    print(f"  [{status}] {item['name']} {detail}")

  db = report["optional_db_extra"]
  print("\nOptional DB extra:")
  if db["ok"]:
    print(f"  [ok] {db['name']} {db.get('module') or ''}")
  else:
    print(f"  [missing] {db['name']} {db.get('error') or ''}")
    print('  Install DB support in the active environment with: pip install "google-adk[db]"')

  print("\nSelected signatures:")
  for item in report["signatures"]:
    if item["ok"]:
      print(f"  {item['name']}{item['signature']}")
    else:
      print(f"  {item['name']}: {item.get('error') or 'unavailable'}")

  print("\nSafety:")
  for key, value in report["safety"].items():
    print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Safely inspect ADK runtime-service imports/signatures and optional "
          "DB-extra availability without touching databases or credentials."
      )
  )
  parser.add_argument(
      "--json",
      action="store_true",
      help="Print the report as JSON for automated checks.",
  )
  args = parser.parse_args(argv)

  report = collect()
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print_text(report)

  base_ok = all(item["ok"] for item in report["base_imports"])
  return 0 if base_ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
