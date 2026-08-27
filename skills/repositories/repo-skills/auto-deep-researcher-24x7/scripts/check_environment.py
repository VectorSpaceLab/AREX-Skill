#!/usr/bin/env python3
"""Read-only application environment and config probe.

Usage:
  python scripts/check_environment.py --repo-root /path/to/checkout

The probe imports the selected application modules from an explicit checkout,
checks YAML and provider metadata, optionally probes CUDA, and never launches a
training process, contacts an API, writes project state, or reads credentials.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def _load_config(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return {}, None
    try:
        import yaml
    except ImportError as exc:
        return None, f"PyYAML unavailable: {exc}"
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"config parse failed: {exc}"
    if value is None:
        return {}, None
    if not isinstance(value, dict):
        return None, "config root must be a mapping"
    return value, None


def _provider_metadata(config: dict[str, Any]) -> dict[str, Any]:
    agent = config.get("agent") if isinstance(config.get("agent"), dict) else {}
    provider = str(agent.get("provider", "anthropic"))
    result: dict[str, Any] = {
        "provider_label": provider,
        "model": str(agent.get("model", "claude-sonnet-4-6")),
        "base_url_configured": bool(str(agent.get("base_url", "")).strip()),
        "api_key_env_name_configured": bool(str(agent.get("api_key_env", "")).strip()),
        "auth_token_env_name_configured": bool(str(agent.get("auth_token_env", "")).strip()),
        "secret_values_read": False,
    }
    try:
        from core.agents import AgentDispatcher
        preset = AgentDispatcher.PROVIDER_PRESETS.get(provider)
        result["normalized_provider"] = "openai" if preset else provider
        result["preset"] = bool(preset)
        result["provider_supported"] = provider in AgentDispatcher.SUPPORTED_PROVIDERS or bool(preset)
    except Exception as exc:
        result["provider_supported"] = False
        result["error"] = str(exc)
    return result


def _cuda_probe() -> dict[str, Any]:
    try:
        import torch
    except ImportError as exc:
        return {"available": False, "status": "torch unavailable", "error": str(exc)}
    result: dict[str, Any] = {
        "torch": getattr(torch, "__version__", "unknown"),
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
    }
    if result["available"]:
        result["device_name"] = torch.cuda.get_device_name(0)
        result["capability"] = list(torch.cuda.get_device_capability(0))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Deep Researcher environment probe")
    parser.add_argument("--repo-root", required=True, help="Application checkout to inspect")
    parser.add_argument("--config", default="config.yaml", help="Config filename relative to repo root")
    parser.add_argument("--cuda", action="store_true", help="Include a read-only torch CUDA probe")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"ok": False, "error": "repo root is not a directory"}, indent=2))
        return 2
    sys.path.insert(0, str(root))
    modules = [
        "core.loop", "core.execution", "core.tools", "core.monitor", "core.memory",
        "core.ledger", "core.journal", "core.safety", "core.obsidian", "gpu.detect",
        "gpu.keeper",
    ]
    imported: list[str] = []
    import_errors: dict[str, str] = {}
    for name in modules:
        try:
            importlib.import_module(name)
            imported.append(name)
        except Exception as exc:
            import_errors[name] = f"{type(exc).__name__}: {exc}"
    config, config_error = _load_config(root / args.config)
    output: dict[str, Any] = {
        "ok": not import_errors and config_error is None,
        "imported": imported,
        "import_errors": import_errors,
        "config_error": config_error,
        "provider": _provider_metadata(config or {}),
        "secret_values_read": False,
        "network_access": False,
        "training_started": False,
    }
    if args.cuda:
        output["cuda"] = _cuda_probe()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
