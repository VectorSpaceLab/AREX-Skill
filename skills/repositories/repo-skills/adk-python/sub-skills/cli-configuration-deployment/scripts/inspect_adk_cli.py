#!/usr/bin/env python3
"""Safely inspect an installed ADK CLI and config schema metadata.

This helper runs only `adk --help`-style commands and package-resource
inspection. It does not import user agents, start servers, deploy, contact cloud
services, read credentials, or mutate files.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from dataclasses import dataclass
from typing import Any


DEFAULT_COMMANDS = [
    "run",
    "web",
    "api_server",
    "test",
    "eval",
    "eval_set",
    "deploy",
]


@dataclass
class HelpResult:
  command: str
  ok: bool
  returncode: int | None
  summary: str
  error: str | None = None


def _run_help(adk_executable: str, command: str | None, timeout: float) -> HelpResult:
  args = [adk_executable]
  label = "adk"
  if command:
    args.append(command)
    label = f"adk {command}"
  args.append("--help")
  try:
    completed = subprocess.run(
        args,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
  except FileNotFoundError:
    return HelpResult(label, False, None, "", f"Executable not found: {adk_executable}")
  except subprocess.TimeoutExpired:
    return HelpResult(label, False, None, "", f"Timed out after {timeout} seconds")

  output = completed.stdout.strip() or completed.stderr.strip()
  first_lines = "\n".join(output.splitlines()[:12])
  return HelpResult(
      label,
      completed.returncode == 0,
      completed.returncode,
      first_lines,
      None if completed.returncode == 0 else completed.stderr.strip()[:500],
  )


def _parse_top_level_commands(help_text: str) -> list[str]:
  commands: list[str] = []
  in_commands = False
  for line in help_text.splitlines():
    if line.strip() == "Commands:":
      in_commands = True
      continue
    if not in_commands:
      continue
    match = re.match(r"^\s{2}([A-Za-z0-9_-]+)\s+", line)
    if match:
      commands.append(match.group(1))
  return commands


def _schema_metadata() -> dict[str, Any]:
  result: dict[str, Any] = {"found": False}
  try:
    root = importlib.resources.files("google.adk.agents.config_schemas")
    schema = root.joinpath("AgentConfig.json")
    if schema.is_file():
      text = schema.read_text(encoding="utf-8")
      parsed = json.loads(text)
      result.update(
          {
              "found": True,
              "resource": "google.adk.agents.config_schemas/AgentConfig.json",
              "title": parsed.get("title"),
              "top_level_keys": sorted(parsed.keys()),
              "definition_count": len(parsed.get("$defs", {})),
              "property_names": sorted(parsed.get("properties", {}).keys()),
          }
      )
  except Exception as exc:  # pragma: no cover - diagnostic path
    result["error"] = f"{type(exc).__name__}: {exc}"
  return result


def _package_metadata() -> dict[str, Any]:
  try:
    version = importlib.metadata.version("google-adk")
  except importlib.metadata.PackageNotFoundError:
    version = None
  try:
    import google.adk as adk  # type: ignore

    import_version = getattr(adk, "__version__", None)
  except Exception as exc:  # pragma: no cover - diagnostic path
    import_version = None
    import_error = f"{type(exc).__name__}: {exc}"
  else:
    import_error = None
  return {
      "distribution": "google-adk",
      "distribution_version": version,
      "import_name": "google.adk",
      "import_version": import_version,
      "import_error": import_error,
  }


def _resolve_adk_executable(adk_executable: str) -> str:
  resolved = shutil.which(adk_executable)
  if resolved:
    return resolved
  sibling = Path(sys.executable).with_name(adk_executable)
  if sibling.exists():
    return str(sibling)
  return adk_executable


def inspect_cli(adk_executable: str, commands: list[str], timeout: float) -> dict[str, Any]:
  executable = _resolve_adk_executable(adk_executable)
  top = _run_help(executable, None, timeout)
  command_results = [_run_help(executable, command, timeout) for command in commands]
  discovered = _parse_top_level_commands(top.summary) if top.ok else []
  return {
      "adk_executable": executable,
      "package": _package_metadata(),
      "schema": _schema_metadata(),
      "top_level_help": asdict(top),
      "discovered_commands": discovered,
      "checked_commands": [asdict(item) for item in command_results],
  }


def main(argv: list[str]) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--adk", default="adk", help="ADK executable to inspect; default: adk")
  parser.add_argument(
      "--commands",
      nargs="*",
      default=DEFAULT_COMMANDS,
      help="Subcommands to inspect with --help; default: common safe commands",
  )
  parser.add_argument("--timeout", type=float, default=8.0, help="Timeout per help command")
  parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
  args = parser.parse_args(argv)

  report = inspect_cli(args.adk, args.commands, args.timeout)
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    package = report["package"]
    print(f"google-adk distribution: {package['distribution_version'] or 'not found'}")
    print(f"google.adk import version: {package['import_version'] or package['import_error'] or 'unknown'}")
    print(f"ADK executable: {report['adk_executable']}")
    print(f"Schema found: {report['schema'].get('found')}")
    if report["discovered_commands"]:
      print("Top-level commands: " + ", ".join(report["discovered_commands"]))
    for item in report["checked_commands"]:
      status = "ok" if item["ok"] else "failed"
      print(f"{item['command']}: {status}")
      if item.get("error"):
        print(f"  {item['error']}")
  failed = [item for item in report["checked_commands"] if not item["ok"]]
  return 1 if not report["top_level_help"]["ok"] or failed else 0


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
