#!/usr/bin/env python3
"""Safe, deterministic ROSA custom-tool template.

This helper adapts the repository's sample ``@tool`` function that accepts a
blacklist. It only validates and echoes caller-provided values: no ROS, LLM,
network, credential, or filesystem operation is performed. Run it with no
arguments for the schema/result self-check, or use ``--help`` for options.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

from langchain.agents import tool


@tool
def safe_custom_tool(
    value: str, blacklist: Optional[list[str]] = None
) -> dict[str, object]:
    """Return a normalized note and the blacklist supplied to this tool.

    The blacklist parameter demonstrates the shape ROSA can inject for a
    blacklist-aware tool. This example does not access or act on any robot.
    """
    normalized = value.strip()
    return {
        "value": normalized,
        "length": len(normalized),
        "blacklist_seen": list(blacklist or []),
        "side_effects": False,
    }


def _schema_as_dict(tool_object: object) -> dict:
    """Support the Pydantic schema method used by installed LangChain builds."""
    schema_type = getattr(tool_object, "args_schema", None)
    if schema_type is None:
        return {}
    if hasattr(schema_type, "model_json_schema"):
        return schema_type.model_json_schema()
    if hasattr(schema_type, "schema"):
        return schema_type.schema()
    return {"repr": repr(schema_type)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and safely self-check a deterministic ROSA tool."
    )
    parser.add_argument(
        "--value", default="safe inspection", help="Value passed to the tool."
    )
    parser.add_argument(
        "--blacklist",
        action="append",
        default=[],
        help="Caller blacklist entry; may be repeated.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Run the default deterministic invocation (the default path also does this).",
    )
    args = parser.parse_args()

    # Keep output JSON-like and reproducible so this is useful as a preflight
    # fixture without creating a ROSA agent or touching the host.
    schema = _schema_as_dict(safe_custom_tool)
    result = safe_custom_tool.invoke(
        {"value": args.value, "blacklist": args.blacklist}
    )
    print("TOOL_SCHEMA=" + json.dumps(schema, sort_keys=True, indent=2))
    print("TOOL_NAME=" + safe_custom_tool.name)
    print("TOOL_RESULT=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
