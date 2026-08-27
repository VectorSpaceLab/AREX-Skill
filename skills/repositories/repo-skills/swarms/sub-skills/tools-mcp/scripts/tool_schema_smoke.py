#!/usr/bin/env python3
"""Offline tool-schema smoke check for Swarms."""

from __future__ import annotations

import json
from pydantic import BaseModel

from swarms.tools.base_tool import BaseTool
from swarms.tools.pydantic_to_json import base_model_to_openai_function


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


class DemoModel(BaseModel):
    name: str
    count: int


def main() -> None:
    tool = BaseTool(function_map={"add": add}, tools=[add], verbose=False)
    schema = tool.func_to_dict(add)
    print(schema["function"]["name"])

    model_schema = base_model_to_openai_function(DemoModel)
    print(model_schema["functions"][0]["name"])

    result = tool.execute_tool_by_name(
        "add",
        json.dumps({"name": "add", "parameters": {"a": 1, "b": 2}}),
    )
    print(result)
    print("tool schema smoke ok")


if __name__ == "__main__":
    main()
