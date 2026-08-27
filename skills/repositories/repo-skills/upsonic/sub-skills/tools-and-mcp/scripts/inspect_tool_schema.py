#!/usr/bin/env python3
from __future__ import annotations

import inspect


def main() -> int:
    from upsonic.tools import FunctionTool, ToolConfig, prepare_command, tool

    @tool(requires_confirmation=True)
    def sample_tool(a: int, b: int) -> int:
        """Add two integers.

        Args:
            a: First integer.
            b: Second integer.
        """
        return a + b

    def adder(a: int, b: int) -> int:
        """Add two integers.

        Args:
            a: First integer.
            b: Second integer.
        """
        return a + b

    wrapped = FunctionTool.from_callable(adder)
    print(f'ToolConfig: {ToolConfig.model_fields.keys()}')
    print(f'function_tool: {wrapped.__class__.__name__}')
    print(f'wrapped_name: {getattr(wrapped, "name", "unknown")}')
    print(f'sample_tool_is_tool: {getattr(sample_tool, "_upsonic_is_tool", False)}')
    print(f'prepare_command: {prepare_command("python -V")}')
    print(f'FunctionTool.from_callable: {inspect.signature(FunctionTool.from_callable)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
