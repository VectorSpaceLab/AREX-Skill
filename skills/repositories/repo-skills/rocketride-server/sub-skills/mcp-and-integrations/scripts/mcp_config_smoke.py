#!/usr/bin/env python3
"""
Safe RocketRide MCP configuration smoke check.

This script validates environment-variable and MCP-client JSON configuration for
rocketride-mcp. It intentionally does not start rocketride-mcp, does not start an
SSE server, and does not connect to a RocketRide engine.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Tuple

MCP_ENV_KEYS = ("ROCKETRIDE_URI", "ROCKETRIDE_AUTH", "ROCKETRIDE_APIKEY", "MCP_API_KEY")


@dataclass(frozen=True)
class LoadedSettings:
    apikey: str
    uri: str
    source: str


def redact(value: Optional[str]) -> str:
    """Redact a secret-like value while keeping enough shape for debugging."""
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-2:]}"


def redacted_env(env: Mapping[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key in MCP_ENV_KEYS:
        value = env.get(key, "")
        if key in {"ROCKETRIDE_AUTH", "ROCKETRIDE_APIKEY", "MCP_API_KEY"}:
            out[key] = redact(value)
        else:
            out[key] = value
    return out


def local_load_settings(env: Mapping[str, str]) -> LoadedSettings:
    """Mirror rocketride_mcp.config.load_settings without importing server code."""
    apikey = env.get("ROCKETRIDE_AUTH") or env.get("ROCKETRIDE_APIKEY") or ""
    uri = env.get("ROCKETRIDE_URI") or ""
    if not apikey:
        raise ValueError("Missing required environment variable: ROCKETRIDE_AUTH or ROCKETRIDE_APIKEY")
    if not uri:
        raise ValueError("Missing required environment variable: ROCKETRIDE_URI")
    source = "ROCKETRIDE_AUTH" if env.get("ROCKETRIDE_AUTH") else "ROCKETRIDE_APIKEY"
    return LoadedSettings(apikey=apikey, uri=uri, source=source)


@contextlib.contextmanager
def patched_env(values: Mapping[str, str]) -> Iterator[None]:
    """Temporarily patch only the MCP-related environment variables."""
    original: Dict[str, Optional[str]] = {key: os.environ.get(key) for key in MCP_ENV_KEYS}
    try:
        for key in MCP_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in values.items():
            if key in MCP_ENV_KEYS and value is not None:
                os.environ[key] = str(value)
        yield
    finally:
        for key in MCP_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in original.items():
            if value is not None:
                os.environ[key] = value


def installed_load_settings(env: Mapping[str, str]) -> Optional[LoadedSettings]:
    """Call installed rocketride_mcp.config.load_settings if available."""
    try:
        config_mod = importlib.import_module("rocketride_mcp.config")
    except Exception:
        return None
    with patched_env(env):
        settings = config_mod.load_settings()
    apikey = getattr(settings, "apikey")
    uri = getattr(settings, "uri")
    source = "ROCKETRIDE_AUTH" if env.get("ROCKETRIDE_AUTH") else "ROCKETRIDE_APIKEY"
    return LoadedSettings(apikey=apikey, uri=uri, source=source)


def uri_warnings(uri: str) -> List[str]:
    warnings: List[str] = []
    if not uri:
        return warnings
    lower = uri.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        warnings.append(
            "ROCKETRIDE_URI is an HTTP URL; rocketride-mcp expects the engine WebSocket URI such as ws://localhost:5565."
        )
    elif not (lower.startswith("ws://") or lower.startswith("wss://")):
        warnings.append("ROCKETRIDE_URI should normally start with ws:// or wss:// for MCP engine access.")
    if "localhost" in lower:
        warnings.append("If this runs in a container or remote client, localhost may refer to that process, not the host engine.")
    return warnings


def validate_env(label: str, env: Mapping[str, str], require_installed: bool = False) -> Dict[str, Any]:
    """Validate one environment map and compare installed loader behavior when present."""
    result: Dict[str, Any] = {"label": label, "env": redacted_env(env), "ok": False, "warnings": []}
    local = local_load_settings(env)
    result["loaded"] = {"uri": local.uri, "authSource": local.source, "auth": redact(local.apikey)}
    result["warnings"].extend(uri_warnings(local.uri))
    if env.get("ROCKETRIDE_AUTH") and env.get("ROCKETRIDE_APIKEY"):
        result["warnings"].append("Both ROCKETRIDE_AUTH and ROCKETRIDE_APIKEY are set; ROCKETRIDE_AUTH takes precedence.")

    installed = installed_load_settings(env)
    if installed is None:
        if require_installed:
            raise RuntimeError("rocketride_mcp.config is not importable but --require-installed was set")
        result["installedConfig"] = "not-importable"
    else:
        if installed.apikey != local.apikey or installed.uri != local.uri:
            raise AssertionError("Installed rocketride_mcp.config behavior differs from expected env precedence")
        result["installedConfig"] = "matches"
    result["ok"] = True
    return result


def expect_error(label: str, env: Mapping[str, str], message_part: str) -> Dict[str, Any]:
    """Assert that local and installed config loaders reject an invalid env."""
    result: Dict[str, Any] = {"label": label, "env": redacted_env(env), "ok": False}
    try:
        local_load_settings(env)
    except ValueError as exc:
        if message_part not in str(exc):
            raise AssertionError(f"Unexpected local error for {label}: {exc}") from exc
        result["localError"] = str(exc)
    else:
        raise AssertionError(f"Expected local settings failure for {label}")

    try:
        installed_available = importlib.util.find_spec("rocketride_mcp.config") is not None
    except Exception:
        installed_available = False
    if installed_available:
        try:
            installed_load_settings(env)
        except ValueError as exc:
            if message_part not in str(exc):
                raise AssertionError(f"Unexpected installed error for {label}: {exc}") from exc
            result["installedError"] = str(exc)
        else:
            raise AssertionError(f"Expected installed settings failure for {label}")
    else:
        result["installedConfig"] = "not-importable"
    result["ok"] = True
    return result


def default_smokes(require_installed: bool = False) -> List[Dict[str, Any]]:
    """Run no-network config behavior checks."""
    cases = [
        ("auth_only", {"ROCKETRIDE_URI": "ws://localhost:5565", "ROCKETRIDE_AUTH": "auth-value"}),
        ("apikey_fallback", {"ROCKETRIDE_URI": "wss://rocketride.example.invalid", "ROCKETRIDE_APIKEY": "apikey-value"}),
        (
            "auth_preferred_over_apikey",
            {
                "ROCKETRIDE_URI": "wss://rocketride.example.invalid",
                "ROCKETRIDE_AUTH": "auth-value",
                "ROCKETRIDE_APIKEY": "apikey-value",
            },
        ),
    ]
    results = [validate_env(label, env, require_installed=require_installed) for label, env in cases]
    results.append(expect_error("missing_auth", {"ROCKETRIDE_URI": "ws://localhost:5565"}, "ROCKETRIDE_AUTH"))
    results.append(expect_error("missing_uri", {"ROCKETRIDE_AUTH": "auth-value"}, "ROCKETRIDE_URI"))
    return results


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def select_mcp_server(data: Mapping[str, Any], server_name: str) -> Tuple[str, Mapping[str, Any]]:
    servers = data.get("mcpServers") if isinstance(data.get("mcpServers"), Mapping) else data
    if not isinstance(servers, Mapping):
        raise ValueError("MCP config must contain an object or an object-valued mcpServers field")
    if server_name in servers and isinstance(servers[server_name], Mapping):
        return server_name, servers[server_name]
    for name, server in servers.items():
        if isinstance(server, Mapping):
            command = str(server.get("command", ""))
            args = " ".join(str(x) for x in server.get("args", []) if isinstance(server.get("args", []), list))
            if "rocketride-mcp" in command or "rocketride_mcp" in args:
                return str(name), server
    raise ValueError(f"No MCP server named {server_name!r} and no rocketride-mcp command found")


def validate_client_config(path: Path, server_name: str, require_installed: bool = False) -> Dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, Mapping):
        raise ValueError("MCP config root must be a JSON object")
    selected_name, server = select_mcp_server(data, server_name)
    command = str(server.get("command", ""))
    args = server.get("args", [])
    env = server.get("env", {})
    if not isinstance(env, Mapping):
        raise ValueError("Selected MCP server env must be an object")
    env_map = {str(k): str(v) for k, v in env.items() if k in MCP_ENV_KEYS}
    result = validate_env(f"client_config:{selected_name}", env_map, require_installed=require_installed)
    result["serverName"] = selected_name
    result["command"] = command
    if not command:
        result["warnings"].append("Selected MCP server has no command field.")
    elif "rocketride-mcp" not in command and "python" not in command:
        result["warnings"].append("Command does not look like rocketride-mcp or python -m rocketride_mcp.")
    if args and not isinstance(args, list):
        result["warnings"].append("args field is present but is not a list.")
    return result


def current_env_map() -> Dict[str, str]:
    return {key: os.environ.get(key, "") for key in MCP_ENV_KEYS if os.environ.get(key, "")}


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="No-network smoke checks for rocketride-mcp config")
    parser.add_argument("--check-current-env", action="store_true", help="Validate current ROCKETRIDE_* environment")
    parser.add_argument("--client-config", type=Path, help="Validate a Claude/Cursor-style MCP JSON config")
    parser.add_argument("--server-name", default="rocketride", help="mcpServers entry name to check")
    parser.add_argument("--require-installed", action="store_true", help="Fail if rocketride_mcp.config is not importable")
    parser.add_argument("--json", action="store_true", help="Emit JSON only (default output is also JSON)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report: Dict[str, Any] = {"ok": False, "checks": []}
    try:
        if args.check_current_env:
            report["checks"].append(validate_env("current_env", current_env_map(), require_installed=args.require_installed))
        if args.client_config:
            report["checks"].append(
                validate_client_config(args.client_config, args.server_name, require_installed=args.require_installed)
            )
        if not args.check_current_env and not args.client_config:
            report["checks"].extend(default_smokes(require_installed=args.require_installed))
        report["ok"] = all(check.get("ok") for check in report["checks"])
    except Exception as exc:  # keep failures concise and path-safe
        report["ok"] = False
        report["error"] = str(exc)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
