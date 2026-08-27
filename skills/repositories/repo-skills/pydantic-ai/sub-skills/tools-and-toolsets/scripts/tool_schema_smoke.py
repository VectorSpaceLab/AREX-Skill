#!/usr/bin/env python3
"""Smoke-check Pydantic AI tool schema generation and toolset composition.

Usage:
    python tool_schema_smoke.py

The script performs no network calls, reads no credentials, and writes no files.
It verifies local imports, `FunctionToolset` schema extraction, prefix/filter/prepare
wrappers, `include_return_schemas()`, and `TestModel` request parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pydantic_ai import Agent, CombinedToolset, FunctionToolset, RunContext, ToolDefinition
from pydantic_ai.models.test import TestModel


@dataclass
class Access:
    role: str = 'user'
    include_admin: bool = False


def keep_allowed_tools(ctx: RunContext[Access], tool_def: ToolDefinition) -> bool:
    return ctx.deps.include_admin or not tool_def.name.startswith('admin_')


def annotate_descriptions(ctx: RunContext[Access], tool_defs: list[ToolDefinition]) -> list[ToolDefinition]:
    return [replace(tool_def, description=f'{tool_def.description} (role: {ctx.deps.role})') for tool_def in tool_defs]


math_tools = FunctionToolset[Access](
    instructions=lambda ctx: f'Use arithmetic tools for {ctx.deps.role} requests.',
    require_parameter_descriptions=True,
)


@math_tools.tool_plain
def add(x: int, y: int) -> int:
    """Add two integers.

    Args:
        x: First integer.
        y: Second integer.
    """
    return x + y


admin_tools = FunctionToolset[Access]()


@admin_tools.tool
def audit(ctx: RunContext[Access], topic: str) -> str:
    """Create an audit note for the current role.

    Args:
        topic: Subject to record in the audit note.
    """
    return f'{ctx.deps.role}: {topic}'


toolset = (
    CombinedToolset([math_tools.prefixed('math'), admin_tools.prefixed('admin')])
    .filtered(keep_allowed_tools)
    .prepared(annotate_descriptions)
    .include_return_schemas()
)


def exposed_tool_defs(deps: Access) -> list[ToolDefinition]:
    model = TestModel(call_tools=[], custom_output_text='ok')
    agent = Agent(model, deps_type=Access, toolsets=[toolset])
    result = agent.run_sync('Inspect available tools.', deps=deps)
    assert result.output == 'ok'
    assert model.last_model_request_parameters is not None
    return model.last_model_request_parameters.function_tools


def main() -> None:
    user_defs = exposed_tool_defs(Access(role='user'))
    user_names = [tool_def.name for tool_def in user_defs]
    assert user_names == ['math_add'], user_names
    math_add = user_defs[0]
    assert math_add.parameters_json_schema['properties']['x']['description'] == 'First integer.'
    assert math_add.include_return_schema is True
    assert math_add.description is not None
    assert math_add.description.startswith('Add two integers. (role: user)')
    assert 'Return schema:' in math_add.description

    admin_defs = exposed_tool_defs(Access(role='admin', include_admin=True))
    admin_names = [tool_def.name for tool_def in admin_defs]
    assert admin_names == ['math_add', 'admin_audit'], admin_names
    descriptions = {tool_def.name: tool_def.description for tool_def in admin_defs}
    assert descriptions['admin_audit'] is not None
    assert descriptions['admin_audit'].startswith('Create an audit note for the current role. (role: admin)')

    print('tool schema smoke passed')


if __name__ == '__main__':
    main()
