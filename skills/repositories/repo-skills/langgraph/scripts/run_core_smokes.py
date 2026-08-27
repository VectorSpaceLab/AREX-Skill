#!/usr/bin/env python3
"""Run small LangGraph environment smoke checks without needing the source repo."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def check_imports() -> dict[str, Any]:
    modules = [
        "langgraph",
        "langgraph.graph",
        "langgraph.prebuilt",
        "langgraph.checkpoint",
        "langgraph_sdk",
        "langgraph_cli",
    ]
    results: dict[str, Any] = {}
    for name in modules:
        try:
            importlib.import_module(name)
            results[name] = {"ok": True}
        except Exception as exc:
            results[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return results


def check_graph() -> dict[str, Any]:
    try:
        from typing_extensions import TypedDict
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    class State(TypedDict):
        value: int

    def inc(state: State) -> State:
        return {"value": state["value"] + 1}

    try:
        builder = StateGraph(State)
        builder.add_node("inc", inc)
        builder.add_edge(START, "inc")
        builder.add_edge("inc", END)
        app = builder.compile()
        output = app.invoke({"value": 1})
        return {"ok": output["value"] == 2, "output": output}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_cli() -> dict[str, Any]:
    try:
        langgraph_command = Path(sys.executable).parent / "langgraph"
        command = str(langgraph_command) if langgraph_command.exists() else "langgraph"
        proc = subprocess.run(
            [command, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_head": proc.stdout[:300],
            "stderr_head": proc.stderr[:300],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="append",
        choices=["imports", "graph", "cli"],
        help="Check(s) to run. Defaults to all checks.",
    )
    args = parser.parse_args()
    checks = args.check or ["imports", "graph", "cli"]
    output: dict[str, Any] = {}
    if "imports" in checks:
        output["imports"] = check_imports()
    if "graph" in checks:
        output["graph"] = check_graph()
    if "cli" in checks:
        output["cli"] = check_cli()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if all(_ok(value) for value in output.values()) else 1


def _ok(value: Any) -> bool:
    if isinstance(value, dict) and "ok" in value:
        return bool(value["ok"])
    if isinstance(value, dict):
        return all(_ok(item) for item in value.values())
    return bool(value)


if __name__ == "__main__":
    raise SystemExit(main())
