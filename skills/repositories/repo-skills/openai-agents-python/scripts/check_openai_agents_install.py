#!/usr/bin/env python3
"""Check an openai-agents installation without making API calls."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import os
import sys
from typing import Any

SURFACES = {
    "agents": ["Agent", "Runner", "RunConfig", "ModelSettings", "function_tool", "handoff"],
    "agents.run_state": ["RunState"],
    "agents.realtime": ["RealtimeAgent", "RealtimeRunner", "RealtimeSession"],
    "agents.mcp": ["MCPServerStdio", "MCPServerStreamableHttp"],
    "agents.sandbox": ["SandboxAgent", "Manifest"],
    "agents.tracing": ["trace", "add_trace_processor", "set_tracing_disabled"],
}

OPTIONAL_IMPORTS = {
    "voice": "agents.voice",
    "redis": "agents.extensions.memory.redis_session",
    "sqlalchemy": "agents.extensions.memory.sqlalchemy_session",
    "mongodb": "agents.extensions.memory.mongodb_session",
    "dapr": "agents.extensions.memory.dapr_session",
    "encrypt": "agents.extensions.memory.encrypt_session",
    "litellm": "agents.extensions.models.litellm_model",
    "any-llm": "agents.extensions.models.any_llm_model",
    "visualization": "agents.extensions.visualization",
}


def safe_distribution() -> dict[str, Any]:
    try:
        dist = metadata.distribution("openai-agents")
        return {
            "ok": True,
            "name": dist.metadata.get("Name"),
            "version": dist.version,
            "summary": dist.metadata.get("Summary"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def import_surface(module_name: str, names: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "present": [], "missing": []}
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["ok"] = True
    result["file"] = getattr(module, "__file__", None)
    for name in names:
        if hasattr(module, name):
            result["present"].append(name)
        else:
            result["missing"].append(name)
    return result


def optional_import(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {"ok": True, "module": module_name, "file": getattr(module, "__file__", None)}
    except Exception as exc:
        return {"ok": False, "module": module_name, "error": f"{type(exc).__name__}: {exc}"}


def inspect_signatures() -> dict[str, str]:
    signatures: dict[str, str] = {}
    try:
        from agents import Agent, RunConfig, Runner, function_tool, handoff
        from agents.run_state import RunState

        objects = {
            "Agent": Agent,
            "Runner.run": Runner.run,
            "Runner.run_sync": Runner.run_sync,
            "Runner.run_streamed": Runner.run_streamed,
            "RunConfig": RunConfig,
            "function_tool": function_tool,
            "handoff": handoff,
            "RunState": RunState,
        }
        for name, obj in objects.items():
            try:
                signatures[name] = str(inspect.signature(obj))
            except Exception as exc:
                signatures[name] = f"<signature unavailable: {type(exc).__name__}: {exc}>"
    except Exception as exc:
        signatures["error"] = f"{type(exc).__name__}: {exc}"
    return signatures


def build_report(check_optional: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable_basename": os.path.basename(sys.executable),
        "distribution": safe_distribution(),
        "surfaces": {},
        "signatures": inspect_signatures(),
    }
    for module_name, names in SURFACES.items():
        report["surfaces"][module_name] = import_surface(module_name, names)
    if check_optional:
        report["optional_imports"] = {
            name: optional_import(module_name) for name, module_name in OPTIONAL_IMPORTS.items()
        }
    report["ok"] = bool(report["distribution"].get("ok")) and all(
        surface.get("ok") and not surface.get("missing")
        for surface in report["surfaces"].values()
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human text.")
    parser.add_argument(
        "--check-optional",
        action="store_true",
        help="Probe optional extras and report missing dependencies without failing the base check.",
    )
    args = parser.parse_args()
    report = build_report(args.check_optional)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        dist = report["distribution"]
        print(f"openai-agents distribution: {dist}")
        print(f"base surfaces ok: {report['ok']}")
        for module_name, surface in report["surfaces"].items():
            print(f"{module_name}: ok={surface.get('ok')} missing={surface.get('missing')}")
        if args.check_optional:
            for name, result in report["optional_imports"].items():
                print(f"optional {name}: ok={result.get('ok')} {result.get('error', '')}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
