#!/usr/bin/env python3
"""Inspect Langchain-Chatchat SDK and adapter signatures without HTTP calls.

Example:
  python sdk_surface_probe.py --json
"""
from __future__ import annotations

import argparse
import inspect
import json
from importlib.metadata import PackageNotFoundError, version


def safe_version(name: str):
    try:
        return version(name)
    except PackageNotFoundError:
        return None
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


def safe_signature(obj):
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


def method_signatures(cls):
    methods = {}
    for name, member in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_") and name != "__init__":
            continue
        methods[name] = safe_signature(member)
    return methods


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe open_chatcaht SDK and langchain_chatchat adapter surfaces.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = {
        "ok": True,
        "distributions": {
            "langchain-chatchat": safe_version("langchain-chatchat"),
            "open_chatcaht": safe_version("open_chatcaht"),
            "open-langchain-chatchat": safe_version("open-langchain-chatchat"),
        },
        "imports": {},
        "sdk_classes": {},
        "adapters": {},
        "notes": [
            "This probe imports classes and inspects signatures only; it does not call a Chatchat API server.",
            "The SDK import package is spelled open_chatcaht in the inspected repository."
        ],
    }

    try:
        import open_chatcaht  # noqa: F401
        from open_chatcaht.api.chat.chat_client import ChatClient
        from open_chatcaht.api.knowledge_base.knowledge_base_client import KbClient
        from open_chatcaht.api.server.server_client import ServerClient
        from open_chatcaht.api.standard_openai.standard_openai_client import StandardOpenaiClient
        from open_chatcaht.api.tools.tool_client import ToolClient
        from open_chatcaht.api_client import ApiClient
        from open_chatcaht.chatchat_api import ChatChat

        for cls in [ApiClient, ChatChat, KbClient, ChatClient, ToolClient, ServerClient, StandardOpenaiClient]:
            report["sdk_classes"][cls.__name__] = method_signatures(cls)
        report["imports"]["open_chatcaht"] = "ok"
    except Exception as exc:
        report["ok"] = False
        report["imports"]["open_chatcaht"] = f"{type(exc).__name__}: {exc}"

    try:
        from langchain_chatchat import ChatPlatformAI, PlatformToolsRunnable

        for cls in [ChatPlatformAI, PlatformToolsRunnable]:
            report["adapters"][cls.__name__] = {
                "signature": safe_signature(cls),
                "doc_first_lines": (inspect.getdoc(cls) or "").splitlines()[:12],
            }
        report["imports"]["langchain_chatchat"] = "ok"
    except Exception as exc:
        report["ok"] = False
        report["imports"]["langchain_chatchat"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"SDK/adapters probe: {'OK' if report['ok'] else 'FAILED'}")
        for name, status in report["imports"].items():
            print(f"{name}: {status}")
        for name, methods in report["sdk_classes"].items():
            print(f"{name}: {len(methods)} public/constructor methods")
        for name in report["adapters"]:
            print(f"{name}: {report['adapters'][name]['signature']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
