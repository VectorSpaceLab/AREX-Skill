#!/usr/bin/env python3
"""Probe DeepXiv's optional local Agent dependencies without network access.

This helper uses only the Python standard library. It checks import specs and
imports local Python modules to distinguish an absent dependency from an import
that is present but broken. It never creates a Reader, OpenAI client, or network
request, and it never reads credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import sys
from typing import Dict, Iterable, Tuple


OPTIONAL_MODULES: Tuple[Tuple[str, str, str], ...] = (
    ("openai", "openai", "declared by deepxiv-sdk[agent]"),
    ("langgraph", "langgraph", "declared by deepxiv-sdk[agent]"),
    ("langchain_core", "langchain-core", "declared by deepxiv-sdk[agent]"),
    (
        "tiktoken",
        "tiktoken",
        "required by the Agent implementation but omitted from 1.0.0 extras",
    ),
)


def _probe_module(module_name: str) -> Dict[str, str]:
    """Return a stable, path-free status record for one module."""
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ModuleNotFoundError, AttributeError):
        spec = None

    if spec is None:
        return {"status": "missing"}

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # A broken optional install is actionable too.
        return {"status": "import-error", "error_type": type(exc).__name__}

    version = ""
    try:
        version = importlib.metadata.version(module_name.replace("_", "-"))
    except importlib.metadata.PackageNotFoundError:
        version = str(getattr(module, "__version__", ""))
    except Exception:
        version = ""

    result = {"status": "ok"}
    if version:
        result["version"] = version
    return result


def _probe_package() -> Dict[str, object]:
    """Check the base package and whether it exports Agent."""
    try:
        package = importlib.import_module("deepxiv_sdk")
    except Exception as exc:
        return {
            "status": "import-error",
            "error_type": type(exc).__name__,
            "agent_exported": False,
        }

    return {
        "status": "ok",
        "version": str(getattr(package, "__version__", "unknown")),
        "agent_exported": hasattr(package, "Agent"),
    }


def _probe_agent_module() -> Dict[str, str]:
    """Import the Agent module only after the individual checks."""
    try:
        importlib.import_module("deepxiv_sdk.agent.agent")
    except Exception as exc:
        return {"status": "import-error", "error_type": type(exc).__name__}
    return {"status": "ok"}


def _recommendations(
    modules: Dict[str, Dict[str, str]], package: Dict[str, object], agent: Dict[str, str]
) -> list[str]:
    recommendations: list[str] = []
    declared_missing = [
        dist
        for module, dist, _ in OPTIONAL_MODULES[:3]
        if modules[module]["status"] != "ok"
    ]
    if declared_missing:
        recommendations.append(
            'Install the declared optional set: python -m pip install "deepxiv-sdk[agent]"'
        )
    if modules["tiktoken"]["status"] != "ok":
        recommendations.append(
            "Install tiktoken separately: python -m pip install tiktoken "
            "(it is not declared by the 1.0.0 agent/all extras)."
        )
    if package.get("status") != "ok":
        recommendations.append(
            "Install deepxiv-sdk in this interpreter before using the local Agent."
        )
    elif not package.get("agent_exported"):
        recommendations.append(
            "The base package imported but did not export Agent; resolve the optional "
            "module/import errors above, then rerun this probe."
        )
    if agent["status"] != "ok":
        recommendations.append(
            "The Agent module did not import cleanly; use its error type and the "
            "module statuses above to repair the optional environment."
        )
    return recommendations


def probe() -> Dict[str, object]:
    """Run all local checks and return JSON-serializable data."""
    modules = {
        module: _probe_module(module)
        for module, _distribution, _note in OPTIONAL_MODULES
    }
    package = _probe_package()
    agent = _probe_agent_module() if package.get("status") == "ok" else {"status": "skipped"}
    result: Dict[str, object] = {
        "python": sys.version.split()[0],
        "network_checked": False,
        "credentials_read": False,
        "llm_called": False,
        "package": package,
        "modules": modules,
        "agent_module": agent,
    }
    result["recommendations"] = _recommendations(modules, package, agent)
    result["ready"] = (
        package.get("status") == "ok"
        and bool(package.get("agent_exported"))
        and agent.get("status") == "ok"
        and all(modules[name]["status"] == "ok" for name, _d, _n in OPTIONAL_MODULES)
    )
    return result


def _iter_lines(result: Dict[str, object]) -> Iterable[str]:
    yield "DeepXiv local Agent dependency probe"
    yield f"Python: {result['python']}"
    yield "Safety: no network, credentials, LLM, or Reader request"

    package = result["package"]
    if isinstance(package, dict):
        version = package.get("version", "unknown")
        exported = "yes" if package.get("agent_exported") else "no"
        yield f"deepxiv_sdk: {package.get('status')} (version {version}; Agent exported: {exported})"

    modules = result["modules"]
    if isinstance(modules, dict):
        notes = {module: note for module, _dist, note in OPTIONAL_MODULES}
        for module, status in modules.items():
            if isinstance(status, dict):
                suffix = f"; {status['error_type']}" if status.get("error_type") else ""
                yield f"{module}: {status.get('status')}{suffix} ({notes[module]})"

    agent = result["agent_module"]
    if isinstance(agent, dict):
        suffix = f"; {agent['error_type']}" if agent.get("error_type") else ""
        yield f"deepxiv_sdk.agent.agent: {agent.get('status')}{suffix}"

    recommendations = result.get("recommendations", [])
    if recommendations:
        yield "Actions:"
        for recommendation in recommendations:
            yield f"- {recommendation}"
    else:
        yield "Actions: all optional Agent checks passed."
    yield f"Ready for local Agent: {'yes' if result['ready'] else 'no'}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check DeepXiv local Agent imports without network or LLM access."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable JSON report instead of human-readable lines",
    )
    args = parser.parse_args(argv)
    result = probe()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("\n".join(_iter_lines(result)))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
