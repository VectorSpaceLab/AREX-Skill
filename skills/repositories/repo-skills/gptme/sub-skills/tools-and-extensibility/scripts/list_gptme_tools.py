#!/usr/bin/env python3
"""List gptme tools from the installed package without executing tools.

The default scope uses an empty in-process gptme config so user/project plugin
paths and MCP servers are not loaded. Use --scope configured only when importing
configured plugins is acceptable, and --include-mcp only when connecting to
configured MCP servers is acceptable.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


DANGEROUS_SCOPE_NOTE = (
    "configured scope may import configured plugin packages; --include-mcp may "
    "connect to configured MCP servers."
)


def _redacted_env_state(name: str) -> dict[str, str | bool]:
    value = os.environ.get(name)
    if not value:
        return {"set": False}
    if name.endswith("URL"):
        # Keep URL shape useful without exposing full query strings or credentials.
        safe = value.split("?", 1)[0]
        if "@" in safe:
            safe = safe.split("@", 1)[-1]
        return {"set": True, "value_hint": safe}
    if name.endswith("ENGINE"):
        if value in {"chromium", "firefox"}:
            return {"set": True, "value_hint": value}
        return {"set": True, "value_hint": "custom executable or path"}
    return {"set": True}


def check_browser_environment() -> dict[str, Any]:
    """Return safe browser-backend facts without launching a browser."""
    playwright_spec = importlib.util.find_spec("playwright")
    playwright_version = None
    if playwright_spec is not None:
        try:
            playwright_version = importlib.metadata.version("playwright")
        except importlib.metadata.PackageNotFoundError:
            playwright_version = "unknown"

    engine_state = _redacted_env_state("GPTME_BROWSER_ENGINE")
    cdp_state = _redacted_env_state("GPTME_BROWSER_CDP_URL")
    storage_state = _redacted_env_state("GPTME_BROWSER_STORAGE_STATE")

    notes: list[str] = []
    if playwright_spec is None and shutil.which("lynx") is None:
        notes.append("No Playwright package or lynx executable detected.")
    if playwright_spec is not None:
        notes.append(
            "Playwright Python package is installed; browser binaries are not launched or verified by this script."
        )
    if cdp_state.get("set"):
        notes.append("CDP URL is set; gptme browser CDP mode ignores GPTME_BROWSER_ENGINE.")
    elif engine_state.get("set") and engine_state.get("value_hint") not in {
        "chromium",
        "firefox",
    }:
        notes.append("Custom browser engine is configured; ensure the executable is present on PATH or by path.")

    return {
        "playwright_importable": playwright_spec is not None,
        "playwright_version": playwright_version,
        "lynx_on_path": shutil.which("lynx") is not None,
        "env": {
            "GPTME_BROWSER_ENGINE": engine_state,
            "GPTME_BROWSER_CDP_URL": cdp_state,
            "GPTME_BROWSER_STORAGE_STATE": storage_state,
        },
        "notes": notes,
    }


def _safe_tool_available(tool: Any) -> tuple[bool | None, str | None]:
    try:
        return bool(tool.is_available), None
    except Exception as exc:  # pragma: no cover - depends on optional tools
        return None, f"availability check raised {type(exc).__name__}: {exc}"


def _tool_function_record(function: Any) -> dict[str, Any]:
    fn = getattr(function, "fn", None)
    signature = None
    if fn is not None:
        try:
            import inspect

            signature = str(inspect.signature(fn))
        except Exception:
            signature = None
    return {
        "name": getattr(function, "name", None) or getattr(fn, "__name__", "<unknown>"),
        "description": getattr(function, "description", "") or "",
        "signature": signature,
        "hints": sorted(getattr(function, "hints", frozenset()) or []),
    }


def _parameter_record(parameter: Any) -> dict[str, Any]:
    return {
        "name": getattr(parameter, "name", ""),
        "type": getattr(parameter, "type", ""),
        "required": bool(getattr(parameter, "required", False)),
        "description": getattr(parameter, "description", None),
        "enum": getattr(parameter, "enum", None),
    }


def collect_tools(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from gptme.config import Config, UserConfig, set_config, set_config_from_workspace
        from gptme.plugins.registry import discover_all_plugins
        from gptme.tools import clear_tools, get_available_tools
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Could not import gptme tool APIs: {type(exc).__name__}: {exc}",
            "hint": "Run this script with the Python environment where gptme is installed.",
        }

    clear_tools()

    if args.scope == "builtins":
        set_config(Config(user=UserConfig()))
        plugin_paths: list[Path] = []
        enabled_plugins = None
    else:
        if args.workspace:
            set_config_from_workspace(Path(args.workspace).resolve())
        # Import after config has been set.
        from gptme.config import get_config

        config = get_config()
        plugin_paths, enabled_plugins = config.get_plugin_config()
        discover_all_plugins(plugin_paths, enabled_plugins=enabled_plugins)

    try:
        tools = get_available_tools(include_mcp=args.include_mcp)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Tool discovery failed: {type(exc).__name__}: {exc}",
            "scope": args.scope,
            "include_mcp": args.include_mcp,
        }

    records: list[dict[str, Any]] = []
    for tool in tools:
        available, availability_error = _safe_tool_available(tool)
        if args.tool and tool.name not in set(args.tool):
            continue
        records.append(
            {
                "name": tool.name,
                "description": tool.desc,
                "available": available,
                "availability_error": availability_error,
                "available_hint": tool.available_hint,
                "disabled_by_default": bool(tool.disabled_by_default),
                "is_mcp": bool(tool.is_mcp),
                "runnable": bool(tool.execute),
                "block_types": list(tool.block_types or []),
                "hints": sorted(tool.hints or []),
                "parameters": [_parameter_record(p) for p in (tool.parameters or [])],
                "functions": [_tool_function_record(f) for f in (tool.functions or [])],
            }
        )

    records.sort(key=lambda item: item["name"])
    result: dict[str, Any] = {
        "ok": True,
        "scope": args.scope,
        "include_mcp": args.include_mcp,
        "tool_count": len(records),
        "tools": records,
    }
    if args.scope == "configured":
        result["plugin_paths_count"] = len(plugin_paths)
        result["enabled_plugins"] = enabled_plugins
        result["note"] = DANGEROUS_SCOPE_NOTE
    if args.check_browser:
        result["browser_environment"] = check_browser_environment()
    return result


def render_text(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        lines = [f"ERROR: {result.get('error', 'unknown error')}"]
        if hint := result.get("hint"):
            lines.append(f"Hint: {hint}")
        return "\n".join(lines)

    lines = [
        f"gptme tool inventory ({result['scope']}, include_mcp={result['include_mcp']})",
        f"tools: {result['tool_count']}",
    ]
    if note := result.get("note"):
        lines.append(f"note: {note}")
    lines.append("")

    for tool in result["tools"]:
        flags: list[str] = []
        if tool["available"] is True:
            flags.append("available")
        elif tool["available"] is False:
            flags.append("unavailable")
        else:
            flags.append("availability-error")
        if tool["disabled_by_default"]:
            flags.append("disabled-by-default")
        if tool["is_mcp"]:
            flags.append("mcp")
        if tool["runnable"]:
            flags.append("runnable")
        if tool["hints"]:
            flags.append("hints=" + ",".join(tool["hints"]))
        lines.append(f"- {tool['name']}: {tool['description']} [{'; '.join(flags)}]")
        if tool["block_types"]:
            lines.append(f"  block_types: {', '.join(tool['block_types'])}")
        if tool["functions"]:
            fn_names = ", ".join(f["name"] for f in tool["functions"])
            lines.append(f"  functions: {fn_names}")
        if tool["parameters"]:
            params = ", ".join(
                p["name"] + ("*" if p["required"] else "") for p in tool["parameters"]
            )
            lines.append(f"  parameters: {params}")
        if tool["available_hint"]:
            lines.append(f"  availability hint: {tool['available_hint']}")
        if tool["availability_error"]:
            lines.append(f"  availability error: {tool['availability_error']}")

    if browser := result.get("browser_environment"):
        lines.extend(["", "browser environment:"])
        lines.append(f"- playwright importable: {browser['playwright_importable']}")
        if browser.get("playwright_version"):
            lines.append(f"- playwright version: {browser['playwright_version']}")
        lines.append(f"- lynx on PATH: {browser['lynx_on_path']}")
        for name, state in browser["env"].items():
            if state.get("set"):
                hint = state.get("value_hint")
                lines.append(f"- {name}: set" + (f" ({hint})" if hint else ""))
            else:
                lines.append(f"- {name}: unset")
        for note in browser.get("notes", []):
            lines.append(f"  note: {note}")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely list gptme ToolSpec inventory and availability hints.",
    )
    parser.add_argument(
        "--scope",
        choices=["builtins", "configured"],
        default="builtins",
        help=(
            "builtins uses an empty config and avoids configured plugins/MCP; "
            "configured loads current user/project plugin configuration."
        ),
    )
    parser.add_argument(
        "--workspace",
        help="Workspace directory for project config when --scope configured is used.",
    )
    parser.add_argument(
        "--include-mcp",
        action="store_true",
        help="Include configured MCP tools. This may connect to or start configured MCP servers.",
    )
    parser.add_argument(
        "--check-browser",
        action="store_true",
        help="Also report safe browser-backend facts without launching a browser.",
    )
    parser.add_argument(
        "--tool",
        action="append",
        help="Only show a specific tool name. Can be repeated.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.include_mcp and args.scope != "configured":
        parser.error("--include-mcp requires --scope configured")

    result = collect_tools(args)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
