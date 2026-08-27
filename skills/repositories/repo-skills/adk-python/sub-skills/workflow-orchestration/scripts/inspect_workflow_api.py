#!/usr/bin/env python3
"""Inspect ADK workflow APIs without network, credentials, or LLM calls.

This helper imports the installed google.adk workflow package, prints selected
signatures, and constructs a tiny function-node Workflow object to verify the
local API surface. It does not execute a Runner or write files.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import sys
from collections.abc import Callable
from typing import Any


def _signature_or_error(obj: Any) -> str:
  """Returns a readable signature string or a compact error description."""
  try:
    return str(inspect.signature(obj))
  except (TypeError, ValueError) as exc:
    return f"<signature unavailable: {exc}>"


def _print_signature(label: str, obj: Any) -> None:
  """Prints one labeled signature line."""
  print(f"{label}: {_signature_or_error(obj)}")


def _load_distribution_version() -> str:
  """Returns the installed google-adk distribution version if available."""
  try:
    return importlib.metadata.version("google-adk")
  except importlib.metadata.PackageNotFoundError:
    return "<distribution not found>"


def _build_tiny_workflow() -> tuple[Any, Any]:
  """Constructs a no-LLM Workflow from a tiny FunctionNode chain."""
  from google.adk import START
  from google.adk.workflow import FunctionNode
  from google.adk.workflow import Workflow

  def normalize(node_input: str) -> str:
    return node_input.strip().lower()

  normalize_node = FunctionNode(func=normalize, name="normalize")
  workflow = Workflow(
      name="tiny_workflow",
      edges=[(START, normalize_node)],
  )
  return workflow, normalize_node


def inspect_workflow_api(*, show_private_modules: bool) -> int:
  """Prints workflow API details and returns a process exit code."""
  print(f"google-adk distribution: {_load_distribution_version()}")

  try:
    import google.adk.workflow as workflow_module
    from google.adk import START
    from google.adk.workflow import Edge
    from google.adk.workflow import FunctionNode
    from google.adk.workflow import JoinNode
    from google.adk.workflow import RetryConfig
    from google.adk.workflow import Workflow
    from google.adk.workflow import node
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(
        "Failed to import google.adk workflow APIs. Install google-adk in "
        "the active Python environment or run with an appropriate source "
        f"path. Original error: {exc}",
        file=sys.stderr,
    )
    return 1

  print(f"google.adk.workflow module: {workflow_module.__name__}")
  print(f"START node name: {getattr(START, 'name', START)!r}")
  print("\nSignatures:")
  _print_signature("Workflow", Workflow)
  _print_signature("node", node)
  _print_signature("FunctionNode", FunctionNode)
  _print_signature("JoinNode", JoinNode)
  _print_signature("RetryConfig", RetryConfig)
  _print_signature("Edge", Edge)

  if show_private_modules:
    print("\nPrivate module locations:")
    for obj in (Workflow, FunctionNode, JoinNode, RetryConfig):
      print(f"{obj.__name__}: {obj.__module__}")

  print("\nTiny workflow construction:")
  try:
    workflow, normalize_node = _build_tiny_workflow()
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(f"failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1

  graph = getattr(workflow, "graph", None)
  edge_count = len(getattr(graph, "edges", []) or [])
  node_names = [node_obj.name for node_obj in (getattr(graph, "nodes", []) or [])]
  terminal_names = sorted(getattr(graph, "_terminal_node_names", set()) or set())
  print(f"workflow.name: {workflow.name}")
  print(f"function_node.name: {normalize_node.name}")
  print(f"graph.edge_count: {edge_count}")
  print(f"graph.node_names: {node_names}")
  print(f"graph.terminal_nodes: {terminal_names}")
  print("status: ok")
  return 0


def _build_parser() -> argparse.ArgumentParser:
  """Builds the command-line parser."""
  parser = argparse.ArgumentParser(
      description=(
          "Inspect installed ADK workflow signatures and construct a tiny "
          "no-LLM Workflow object."
      )
  )
  parser.add_argument(
      "--show-private-modules",
      action="store_true",
      help="Also print module names for selected workflow classes.",
  )
  return parser


def main(argv: list[str] | None = None) -> int:
  """CLI entry point."""
  parser = _build_parser()
  args = parser.parse_args(argv)
  return inspect_workflow_api(show_private_modules=args.show_private_modules)


if __name__ == "__main__":
  raise SystemExit(main())
