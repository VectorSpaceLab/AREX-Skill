#!/usr/bin/env python3
"""Safe Mem0 SDK smoke-plan helper.

Default mode prints credential-free smoke snippets for Python and TypeScript.
Optional `--mode validate-python-import` imports the Python package only.
Optional `--mode live-platform-python` performs a small hosted Platform add/search
only when explicitly requested and MEM0_API_KEY is present.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import textwrap
from typing import Any

PYTHON_PLATFORM_SNIPPET = r'''
from mem0 import MemoryClient

client = MemoryClient()  # reads MEM0_API_KEY
client.add(
    "Smoke-test memory: user likes green tea.",
    user_id="skill-smoke-user",
    metadata={"source": "mem0-sdk-smoke"},
)
results = client.search("What drink does the smoke-test user like?", filters={"user_id": "skill-smoke-user"})
print(results)
'''

PYTHON_OSS_SNIPPET = r'''
from mem0 import Memory

memory = Memory()
memory.add("Smoke-test memory: user likes green tea.", user_id="skill-smoke-user", infer=False)
results = memory.search("green tea", filters={"user_id": "skill-smoke-user"}, top_k=3)
print(results)
'''

TYPESCRIPT_PLATFORM_SNIPPET = r'''
import { MemoryClient } from "mem0ai";

const client = new MemoryClient({ apiKey: process.env.MEM0_API_KEY! });
await client.add(
  [{ role: "user", content: "Smoke-test memory: user likes green tea." }],
  { userId: "skill-smoke-user", metadata: { source: "mem0-sdk-smoke" } },
);
const results = await client.search("What drink does the smoke-test user like?", {
  filters: { user_id: "skill-smoke-user" },
});
console.log(results);
'''

TYPESCRIPT_OSS_SNIPPET = r'''
import { Memory } from "mem0ai/oss";

const memory = new Memory();
await memory.add("Smoke-test memory: user likes green tea.", {
  userId: "skill-smoke-user",
  infer: false,
});
const results = await memory.search("green tea", {
  filters: { user_id: "skill-smoke-user" },
  topK: 3,
});
console.log(results);
'''


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n```\n{textwrap.dedent(body).strip()}\n```\n"


def build_plan(language: str) -> str:
    sections: list[str] = []
    if language in {"python", "both"}:
        sections.append(_section("Python Platform smoke", PYTHON_PLATFORM_SNIPPET))
        sections.append(_section("Python OSS smoke", PYTHON_OSS_SNIPPET))
    if language in {"typescript", "both"}:
        sections.append(_section("TypeScript Platform smoke", TYPESCRIPT_PLATFORM_SNIPPET))
        sections.append(_section("TypeScript OSS smoke", TYPESCRIPT_OSS_SNIPPET))
    return "\n".join(sections)


def validate_python_import() -> dict[str, Any]:
    report: dict[str, Any] = {"ok": False, "version": None, "exports": [], "errors": []}
    try:
        mem0 = importlib.import_module("mem0")
    except Exception as exc:  # pragma: no cover - depends on user environment
        report["errors"].append(str(exc))
        return report

    report["ok"] = True
    report["version"] = getattr(mem0, "__version__", None)
    for name in ("Memory", "AsyncMemory", "MemoryClient", "AsyncMemoryClient"):
        if hasattr(mem0, name):
            report["exports"].append(name)
    return report


def live_platform_python(user_id: str, query: str, content: str) -> dict[str, Any]:
    api_key_present = bool(os.environ.get("MEM0_API_KEY"))
    if not api_key_present:
        return {
            "ok": False,
            "error": "MEM0_API_KEY is not set. Refusing live hosted call without explicit credentials.",
        }

    from mem0 import MemoryClient

    client = MemoryClient()
    add_response = client.add(
        content,
        user_id=user_id,
        metadata={"source": "mem0-sdk-smoke"},
    )
    search_response = client.search(query, filters={"user_id": user_id}, top_k=3)
    return {
        "ok": True,
        "add_response_keys": sorted(add_response.keys()) if isinstance(add_response, dict) else type(add_response).__name__,
        "search_result_count": len(search_response.get("results", [])) if isinstance(search_response, dict) else None,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe Mem0 SDK smoke snippets or run explicit read/live checks."
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "validate-python-import", "live-platform-python"),
        default="plan",
        help="Default 'plan' prints snippets only and performs no network/provider calls.",
    )
    parser.add_argument(
        "--language",
        choices=("python", "typescript", "both"),
        default="both",
        help="Language snippets to include in plan mode.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON for validation/live modes.")
    parser.add_argument("--user-id", default="skill-smoke-user", help="User scope for explicit live Platform smoke.")
    parser.add_argument(
        "--query",
        default="What drink does the smoke-test user like?",
        help="Search query for explicit live Platform smoke.",
    )
    parser.add_argument(
        "--content",
        default="Smoke-test memory: user likes green tea.",
        help="Memory content for explicit live Platform smoke.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.mode == "plan":
        print(build_plan(args.language))
        return 0

    if args.mode == "validate-python-import":
        report = validate_python_import()
    else:
        report = live_platform_python(args.user_id, args.query, args.content)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if report.get("ok"):
            print("Mem0 SDK smoke check: ok")
            for key, value in report.items():
                if key != "ok":
                    print(f"- {key}: {value}")
        else:
            print("Mem0 SDK smoke check: failed")
            for error in report.get("errors", []) or [report.get("error", "unknown error")]:
                print(f"- {error}")

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
