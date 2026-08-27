#!/usr/bin/env python3
"""Inspect OptiLLM plugin slugs/signatures without invoking plugin behavior."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json

PLUGIN_MODULES = {
    "memory": "optillm.plugins.memory_plugin",
    "readurls": "optillm.plugins.readurls_plugin",
    "privacy": "optillm.plugins.privacy_plugin",
    "genselect": "optillm.plugins.genselect_plugin",
    "majority_voting": "optillm.plugins.majority_voting_plugin",
    "web_search": "optillm.plugins.web_search_plugin",
    "deep_research": "optillm.plugins.deep_research_plugin",
    "deepthink": "optillm.plugins.deepthink_plugin",
    "longcepo": "optillm.plugins.longcepo_plugin",
    "spl": "optillm.plugins.spl_plugin",
    "proxy": "optillm.plugins.proxy_plugin",
    "mcp": "optillm.plugins.mcp_plugin",
    "compact": "optillm.plugins.compact_plugin",
    "coc": "optillm.plugins.coc_plugin",
    "executecode": "optillm.plugins.executecode_plugin",
    "json": "optillm.plugins.json_plugin",
    "router": "optillm.plugins.router_plugin",
}


def inspect_static(check_imports: bool) -> dict:
    result = {}
    for slug, module_name in PLUGIN_MODULES.items():
        item = {"module": module_name}
        if check_imports:
            try:
                module = importlib.import_module(module_name)
                item["imported"] = True
                item["declared_slug"] = getattr(module, "SLUG", None)
                run = getattr(module, "run", None)
                item["has_run"] = callable(run)
                item["signature"] = str(inspect.signature(run)) if callable(run) else None
            except Exception as exc:
                item["imported"] = False
                item["error"] = f"{type(exc).__name__}: {exc}"
        result[slug] = item
    return result


def inspect_loaded() -> dict:
    try:
        import optillm.server as server
        server.load_plugins()
        return {
            slug: str(inspect.signature(func))
            for slug, func in sorted(server.plugin_approaches.items())
        }
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect OptiLLM plugins without real plugin calls")
    parser.add_argument("--check-imports", action="store_true", help="Import each known plugin module and inspect SLUG/run")
    parser.add_argument("--loaded", action="store_true", help="Call optillm.server.load_plugins and show loaded registry")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    result = {"known_plugin_modules": inspect_static(args.check_imports)}
    if args.loaded:
        result["loaded_plugins"] = inspect_loaded()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for slug, item in result["known_plugin_modules"].items():
            if args.check_imports:
                status = "ok" if item.get("imported") and item.get("has_run") else "FAILED"
                extra = item.get("signature") or item.get("error")
                print(f"{slug}: {status} {extra}")
            else:
                print(f"{slug}: {item['module']}")
        if "loaded_plugins" in result:
            print("Loaded registry:")
            for slug, sig in result["loaded_plugins"].items():
                print(f"  {slug}: {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
