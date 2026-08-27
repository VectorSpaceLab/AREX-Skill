#!/usr/bin/env python3
"""Inspect installed ADK agent-construction APIs without model calls.

This script imports the public ADK package, prints key signatures, and
constructs a minimal in-memory Agent object. It performs no network calls,
reads no credentials, and writes no files.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import sys
from typing import Any


def _format_signature(obj: Any) -> str:
  try:
    return str(inspect.signature(obj))
  except (TypeError, ValueError) as exc:
    return f"<signature unavailable: {exc}>"


def _print_signature(label: str, obj: Any) -> None:
  print(f"{label}: {_format_signature(obj)}")


def _version() -> str:
  try:
    return importlib.metadata.version("google-adk")
  except importlib.metadata.PackageNotFoundError:
    return "unknown"


def inspect_api() -> int:
  try:
    import google.adk as adk
    from google.adk import Agent, Runner
    from google.adk.agents import RunConfig
  except Exception as exc:  # pragma: no cover - diagnostic path
    print(f"ERROR: failed to import google.adk: {exc}", file=sys.stderr)
    return 1

  print(f"google-adk version: {_version()}")
  print(f"google.adk module: {getattr(adk, '__name__', 'google.adk')}")

  _print_signature("google.adk.Agent", Agent)
  _print_signature("google.adk.Runner", Runner)
  _print_signature("Runner.run", Runner.run)
  _print_signature("RunConfig", RunConfig)

  try:
    from google.adk.tools.function_tool import FunctionTool
  except Exception as exc:  # pragma: no cover - optional diagnostic path
    print(f"FunctionTool: unavailable ({exc})")
  else:
    _print_signature("FunctionTool", FunctionTool)

  try:
    agent = Agent(
        name="inspection_agent",
        instruction="Constructed for local API inspection only.",
    )
  except Exception as exc:  # pragma: no cover - diagnostic path
    print(f"ERROR: failed to construct minimal Agent: {exc}", file=sys.stderr)
    return 1

  print("minimal_agent_constructed: yes")
  print(f"minimal_agent_name: {agent.name}")
  print(f"minimal_agent_mode: {getattr(agent, 'mode', None)!r}")
  print(f"minimal_agent_tools: {len(getattr(agent, 'tools', []))}")
  return 0


def main() -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Safely inspect installed ADK agent-construction signatures and "
          "construct a minimal Agent without model calls."
      )
  )
  parser.parse_args()
  return inspect_api()


if __name__ == "__main__":
  raise SystemExit(main())
