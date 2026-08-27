#!/usr/bin/env python3
"""Inspect OpenAI Agents model/provider configuration without making API calls."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

SECRET_ENV_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_WEBSOCKET_BASE_URL",
    "OPENAI_DEFAULT_MODEL",
    "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "AZURE_API_KEY",
    "AZURE_OPENAI_API_KEY",
)

OPTIONAL_IMPORTS = {
    "websockets": "websockets",
    "litellm": "litellm",
    "any_llm": "any_llm",
}

AGENTS_IMPORTS = {
    "Agent": "agents",
    "ModelSettings": "agents",
    "RunConfig": "agents",
    "OpenAIProvider": "agents",
    "OpenAIResponsesModel": "agents",
    "OpenAIResponsesWSModel": "agents",
    "OpenAIChatCompletionsModel": "agents",
    "MultiProvider": "agents",
    "responses_websocket_session": "agents",
    "ModelRetrySettings": "agents",
    "retry_policies": "agents",
}


def _mask_env_value(name: str, value: str | None) -> dict[str, Any]:
    if value is None:
        return {"set": False}
    payload: dict[str, Any] = {"set": True, "length": len(value)}
    if name.endswith("BASE_URL") or name == "OPENAI_DEFAULT_MODEL":
        payload["value"] = value
    else:
        payload["preview"] = f"{value[:3]}...{value[-2:]}" if len(value) > 6 else "***"
    return payload


def _import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        return {"available": False, "error": f"{exc.__class__.__name__}: {exc}"}

    version = getattr(module, "__version__", None)
    return {"available": True, "version": str(version) if version is not None else None}


def _agents_object_status(name: str, module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        return {"available": False, "error": f"{exc.__class__.__name__}: {exc}"}
    return {"available": True, "module": getattr(obj, "__module__", module_name)}


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def inspect_configuration() -> dict[str, Any]:
    try:
        import agents
        from agents.models.default_models import get_default_model, get_default_model_settings
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        return {
            "ok": False,
            "agents_import_error": f"{exc.__class__.__name__}: {exc}",
            "python": sys.version.split()[0],
        }

    default_model = get_default_model()
    default_settings = get_default_model_settings(default_model)

    report: dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "agents_version": getattr(agents, "__version__", None),
        "default_model": default_model,
        "default_model_settings": json.loads(json.dumps(default_settings, default=_json_default)),
        "environment": {name: _mask_env_value(name, os.getenv(name)) for name in SECRET_ENV_NAMES},
        "agents_imports": {
            name: _agents_object_status(name, module_name)
            for name, module_name in AGENTS_IMPORTS.items()
        },
        "optional_imports": {
            label: _import_status(module_name)
            for label, module_name in OPTIONAL_IMPORTS.items()
        },
    }

    try:
        from agents import MultiProvider, OpenAIProvider

        provider = OpenAIProvider()
        multi = MultiProvider()
        report["provider_defaults"] = {
            "openai_use_responses": getattr(provider, "_use_responses", None),
            "openai_use_responses_websocket": getattr(provider, "_use_responses_websocket", None),
            "multi_provider_openai_prefix_mode": getattr(multi, "_openai_prefix_mode", None),
            "multi_provider_unknown_prefix_mode": getattr(multi, "_unknown_prefix_mode", None),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        report["provider_defaults_error"] = f"{exc.__class__.__name__}: {exc}"

    return report


def print_text(report: dict[str, Any]) -> None:
    if not report.get("ok"):
        print("agents import: failed")
        print(report.get("agents_import_error", "unknown error"))
        return

    print(f"agents version: {report.get('agents_version')}")
    print(f"python: {report.get('python')}")
    print(f"default model: {report.get('default_model')}")
    print("default model settings:")
    print(json.dumps(report.get("default_model_settings"), indent=2, sort_keys=True))

    print("\nenvironment:")
    for name, status in report["environment"].items():
        if status["set"]:
            suffix = status.get("value") or status.get("preview") or "set"
            print(f"  {name}: set ({suffix})")
        else:
            print(f"  {name}: not set")

    print("\nagents imports:")
    for name, status in report["agents_imports"].items():
        if status["available"]:
            print(f"  {name}: ok ({status['module']})")
        else:
            print(f"  {name}: unavailable ({status['error']})")

    print("\noptional imports:")
    for name, status in report["optional_imports"].items():
        if status["available"]:
            version = status.get("version") or "version unknown"
            print(f"  {name}: ok ({version})")
        else:
            print(f"  {name}: unavailable ({status['error']})")

    if "provider_defaults" in report:
        print("\nprovider defaults:")
        for key, value in report["provider_defaults"].items():
            print(f"  {key}: {value}")
    elif "provider_defaults_error" in report:
        print(f"\nprovider defaults: unavailable ({report['provider_defaults_error']})")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect OpenAI Agents model/provider configuration without API calls."
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    args = parser.parse_args()

    report = inspect_configuration()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
