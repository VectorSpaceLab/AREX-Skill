#!/usr/bin/env python3
"""Offline smoke check for the Atomic Agents MCP integration surface."""

from __future__ import annotations

from atomic_agents.connectors.mcp import MCPTransportType, SchemaTransformer


def main() -> int:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "A name"},
            "count": {"type": "integer", "description": "A count"},
        },
        "required": ["name"],
    }
    model = SchemaTransformer.create_model_from_schema(schema, "SmokeModel", "smoke_tool")
    instance = model(tool_name="smoke_tool", name="demo")

    print("mcp transports:", ", ".join(t.value for t in MCPTransportType))
    print("model fields:", ", ".join(model.model_fields))
    print("instance:", instance.model_dump_json())
    print("mcp smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
