#!/usr/bin/env python3
"""Check a local ADK Python installation without side effects.

The script imports `google.adk`, inspects distribution metadata, optionally runs
`adk --help`, and reports common optional-extra availability. It does not import
user apps, start servers, contact services, deploy, or read credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


OPTIONAL_MODULES = {
    "db": "google.adk.sessions.database_session_service",
    "mcp": "google.adk.tools.mcp_tool.mcp_toolset",
    "eval": "google.adk.evaluation",
    "a2a": "google.adk.a2a",
    "gcp-storage": "google.adk.artifacts.gcs_artifact_service",
    "lite-llm": "google.adk.models.lite_llm",
    "code-executor-container": "google.adk.code_executors.container_code_executor",
}


def _version(package: str) -> str | None:
  try:
    return importlib.metadata.version(package)
  except importlib.metadata.PackageNotFoundError:
    return None


def _import_status(module: str) -> dict[str, Any]:
  try:
    imported = importlib.import_module(module)
  except Exception as exc:  # Diagnostic output should preserve expected ImportErrors.
    return {"ok": False, "module": module, "error": f"{type(exc).__name__}: {exc}"}
  return {"ok": True, "module": module, "file": getattr(imported, "__file__", None)}


def _resolve_executable(name: str) -> str | None:
  found = shutil.which(name)
  if found:
    return found
  sibling = Path(sys.executable).with_name(name)
  if sibling.exists():
    return str(sibling)
  return None


def _adk_help(timeout: float) -> dict[str, Any]:
  executable = _resolve_executable("adk")
  if not executable:
    return {"ok": False, "error": "adk executable not found on PATH or next to current Python"}
  try:
    completed = subprocess.run(
        [executable, "--help"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
  except subprocess.TimeoutExpired:
    return {"ok": False, "executable": executable, "error": f"timed out after {timeout} seconds"}
  text = completed.stdout or completed.stderr
  commands: list[str] = []
  in_commands = False
  for line in text.splitlines():
    if line.strip() == "Commands:":
      in_commands = True
      continue
    if in_commands and line.startswith("  "):
      command = line.split()[0] if line.split() else ""
      if command:
        commands.append(command)
  return {
      "ok": completed.returncode == 0,
      "executable": executable,
      "returncode": completed.returncode,
      "commands": commands,
      "summary": "\n".join(text.splitlines()[:14]),
  }


def build_report(check_cli: bool, timeout: float) -> dict[str, Any]:
  report: dict[str, Any] = {
      "python": sys.version.split()[0],
      "distribution": {"name": "google-adk", "version": _version("google-adk")},
      "base_import": _import_status("google.adk"),
      "optional_modules": {name: _import_status(module) for name, module in OPTIONAL_MODULES.items()},
  }
  if report["base_import"]["ok"]:
    try:
      import google.adk as adk  # type: ignore

      report["google_adk_version"] = getattr(adk, "__version__", None)
    except Exception as exc:  # pragma: no cover - already covered by base import.
      report["google_adk_version_error"] = f"{type(exc).__name__}: {exc}"
  if check_cli:
    report["cli"] = _adk_help(timeout)
  return report


def main(argv: list[str]) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--no-cli", action="store_true", help="Skip `adk --help` inspection")
  parser.add_argument("--timeout", type=float, default=8.0, help="Timeout for CLI help")
  parser.add_argument("--json", action="store_true", help="Emit JSON")
  args = parser.parse_args(argv)

  report = build_report(not args.no_cli, args.timeout)
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print(f"Python: {report['python']}")
    print(f"google-adk distribution: {report['distribution']['version'] or 'not found'}")
    print(f"google.adk import: {'ok' if report['base_import']['ok'] else report['base_import']['error']}")
    if "cli" in report:
      cli = report["cli"]
      print(f"adk CLI: {'ok' if cli['ok'] else cli.get('error', 'failed')}")
      if cli.get("commands"):
        print("commands: " + ", ".join(cli["commands"]))
    missing = [name for name, status in report["optional_modules"].items() if not status["ok"]]
    if missing:
      print("optional modules not available: " + ", ".join(missing))
  cli_ok = report.get("cli", {"ok": True})["ok"]
  return 0 if report["base_import"]["ok"] and report["distribution"]["version"] and cli_ok else 1


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
