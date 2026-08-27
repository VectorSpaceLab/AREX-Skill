#!/usr/bin/env python3
"""Service-free smoke check for AdalFlow FunctionTool and ToolManager.

Run after installing adalflow:
    python scripts/function_tool_smoke.py

This script performs no provider calls, network access, file mutation, or MCP access.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Iterator

from adalflow.core.func_tool import FunctionTool, FunctionType
from adalflow.core.tool_manager import ToolManager
from adalflow.core.types import (
    Function,
    FunctionDefinition,
    FunctionExpression,
    FunctionOutput,
    ToolOutput,
)


def safe_add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


async def async_upper(text: str) -> str:
    """Upper-case text asynchronously."""
    await asyncio.sleep(0)
    return text.upper()


def count_sync(limit: int) -> Iterator[int]:
    """Yield integers from zero to limit minus one."""
    for i in range(limit):
        yield i


async def count_async(limit: int) -> AsyncIterator[int]:
    """Async-yield integers from zero to limit minus one."""
    for i in range(limit):
        await asyncio.sleep(0)
        yield i


def rich_status(label: str, ok: bool = True) -> ToolOutput:
    """Return a ToolOutput with separate observation and display strings."""
    if not ok:
        return ToolOutput(
            output={"label": label, "ok": False},
            observation=f"{label} failed validation",
            display=f"{label}: failed",
            status="error",
        )
    return ToolOutput(
        output={"label": label, "ok": True},
        observation=f"{label} passed validation",
        display=f"{label}: ok",
    )


def raises_expected_error(value: int) -> int:
    """Raise a predictable validation error."""
    raise ValueError(f"expected failure for {value}")


async def main() -> None:
    add_tool = FunctionTool(safe_add)
    async_tool = FunctionTool(async_upper)
    sync_gen_tool = FunctionTool(count_sync)
    async_gen_tool = FunctionTool(count_async)
    rich_tool = FunctionTool(rich_status)
    error_tool = FunctionTool(raises_expected_error)

    assert add_tool.function_type is FunctionType.SYNC
    assert async_tool.function_type is FunctionType.ASYNC
    assert sync_gen_tool.function_type is FunctionType.SYNC_GENERATOR
    assert async_gen_tool.function_type is FunctionType.ASYNC_GENERATOR

    sync_result = add_tool.call(2, 5)
    assert isinstance(sync_result, FunctionOutput)
    assert sync_result.output == 7
    assert sync_result.error is None

    async_result = await async_tool.acall("adalflow")
    assert async_result.output == "ADALFLOW"

    sync_generated = list(sync_gen_tool.call(3).output)
    assert sync_generated == [0, 1, 2]

    async_generated = []
    async_gen_output = (await async_gen_tool.acall(2)).output
    async for item in async_gen_output:
        async_generated.append(item)
    assert async_generated == [0, 1]

    manual_definition = FunctionDefinition(
        func_name="safe_add_alias",
        func_desc="Add two integers using an explicit definition.",
        func_parameters={"a": "int", "b": "int"},
    )
    alias_tool = FunctionTool(safe_add, definition=manual_definition)
    assert alias_tool.definition.func_name == "safe_add_alias"
    assert alias_tool.call(1, 4).output == 5

    manager = ToolManager(tools=[add_tool, rich_tool, alias_tool])
    direct = manager.execute_func(Function(name="safe_add", args=[10], kwargs={"b": 1}))
    assert direct.output == 11

    parsed = manager.call(
        expr_or_fun=FunctionExpression(action="safe_add(a=3, b=4)"),
        step="parse",
    )
    assert isinstance(parsed, Function)
    assert parsed.name == "safe_add"

    executed = manager.call(expr_or_fun=parsed, step="execute")
    assert executed.output == 7

    rich = manager.execute_func(Function(name="rich_status", kwargs={"label": "tool-smoke"}))
    assert isinstance(rich.output, ToolOutput)
    assert rich.output.status == "success"
    assert rich.output.observation == "tool-smoke passed validation"

    failed_rich = rich_tool.call("tool-smoke", ok=False)
    assert isinstance(failed_rich.output, ToolOutput)
    assert failed_rich.output.status == "error"

    captured_error = error_tool.call(42)
    assert captured_error.output is None
    assert captured_error.error is not None
    assert "expected failure for 42" in captured_error.error

    print("FunctionTool/ToolManager smoke passed")


if __name__ == "__main__":
    asyncio.run(main())
