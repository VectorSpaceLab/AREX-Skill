#!/usr/bin/env python3
"""Print safe LlamaIndex agent/tool skeletons.

This helper is intentionally offline by default: it does not create provider LLMs,
read environment variables, call a network API, or execute an agent run. Use it to
start local code for FunctionTool, QueryEngineTool, FunctionAgent, ReActAgent,
streaming events, and multi-agent handoff.
"""

from __future__ import annotations

import argparse
import inspect
import textwrap
from typing import Annotated



SKELETON = r'''
from typing import Annotated

from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent, ReActAgent
from llama_index.core.agent.workflow import AgentStream, ToolCall, ToolCallResult
from llama_index.core.memory import ChatMemoryBuffer, Memory
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core.workflow import Context


# 1) Deterministic function tool.
def lookup_status(
    item_id: Annotated[str, "Stable id for exactly one item, such as TICKET-123"],
) -> str:
    """Look up status for one approved item id."""
    return f"status for {item_id}: pending"


status_tool = FunctionTool.from_defaults(
    fn=lookup_status,
    name="lookup_item_status",
    description=(
        "Use to check the status of one item by id. "
        "Do not use for policy questions or broad search."
    ),
    return_direct=False,
)


# 2) Optional context-aware tool for AgentWorkflow state.
async def record_note(ctx: Context, note: str) -> str:
    """Record a short note in workflow state for later specialist agents."""
    state = await ctx.store.get("state", default={})
    state.setdefault("notes", []).append(note)
    await ctx.store.set("state", state)
    return "note recorded"


# 3) Optional RAG tool: build query_engine elsewhere with the indexing sub-skill.
# knowledge_tool = QueryEngineTool.from_defaults(
#     query_engine=query_engine,
#     name="domain_knowledge_base",
#     description="Answer domain questions. Input must be a complete natural-language question.",
#     return_direct=False,
# )


# 4) FunctionAgent for function-calling LLMs. Supply a compatible llm object.
function_agent = FunctionAgent(
    name="operations",
    description="Uses deterministic tools to answer operational questions.",
    system_prompt="Use tools for status lookups. Say what is missing instead of guessing.",
    tools=[status_tool, record_note],
    llm=llm,
    streaming=False,
    allow_parallel_tool_calls=False,
)


# 5) ReActAgent for models without native function calling.
react_agent = ReActAgent(
    name="react_operations",
    description="Uses ReAct text reasoning to call operational tools.",
    system_prompt="Use Thought, Action, Action Input, or Answer exactly.",
    tools=[status_tool],
    llm=llm,
    streaming=False,
)


# 6) Multi-agent handoff. Names in can_handoff_to must match agent names exactly.
triage_agent = FunctionAgent(
    name="triage",
    description="Routes status questions to operations and answers general requests.",
    system_prompt="Hand off status lookups to operations.",
    can_handoff_to=["operations"],
    llm=llm,
    streaming=False,
)
workflow = AgentWorkflow(
    agents=[triage_agent, function_agent],
    root_agent="triage",
    initial_state={"notes": []},
    timeout=120,
    early_stopping_method="generate",
)


# 7) Safe run pattern with event inspection.
async def run_with_events() -> str:
    memory = ChatMemoryBuffer.from_defaults(token_limit=8000)
    handler = workflow.run(
        user_msg="Check TICKET-123 and record what happened.",
        memory=memory,
        max_iterations=8,
    )
    async for event in handler.stream_events():
        if isinstance(event, AgentStream):
            print(event.delta, end="")
        elif isinstance(event, ToolCall):
            print(f"Calling {event.tool_name}: {event.tool_kwargs}")
        elif isinstance(event, ToolCallResult):
            print(f"{event.tool_name} error={event.tool_output.is_error}")
    result = await handler
    return str(result.response)
'''


def demo_tool(item_id: Annotated[str, "Example item id such as TICKET-123"]) -> str:
    """Look up status for one example item without network access."""
    return f"status for {item_id}: pending"


def build_demo_tool():
    """Create a local FunctionTool for schema inspection only."""
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError as exc:
        raise SystemExit(
            "llama_index.core is required for --print-schema. Install/activate a "
            "LlamaIndex environment, or use --print-code for an offline template."
        ) from exc

    return FunctionTool.from_defaults(
        fn=demo_tool,
        name="lookup_demo_status",
        description="Use to inspect a safe local demo tool schema for one item id.",
        return_direct=False,
    )


def print_schema() -> None:
    """Print the schema that a tool-calling LLM would see."""
    tool = build_demo_tool()
    print("Tool name:", tool.metadata.name)
    print("Tool description:", tool.metadata.description)
    print("Tool parameters:")
    print(tool.metadata.get_parameters_dict())


def print_code() -> None:
    """Print the full skeleton code."""
    print(textwrap.dedent(SKELETON).strip())


def print_summary() -> None:
    """Print a short summary and local demo function signature."""
    signature = inspect.signature(demo_tool)
    print("Safe LlamaIndex agent/tool skeleton helper")
    print("No LLM, network, or agent execution occurs by default.")
    print(f"Demo tool signature: demo_tool{signature}")
    print("Use --print-schema to inspect FunctionTool metadata.")
    print("Use --print-code to print a copyable agent/workflow template.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe LlamaIndex FunctionAgent, ReActAgent, QueryEngineTool, and AgentWorkflow skeletons.",
    )
    parser.add_argument(
        "--print-code",
        action="store_true",
        help="Print a complete copyable skeleton without executing any agent or LLM call.",
    )
    parser.add_argument(
        "--print-schema",
        action="store_true",
        help="Print a safe local FunctionTool schema for inspection.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.print_code:
        print_code()
    elif args.print_schema:
        print_schema()
    else:
        print_summary()


if __name__ == "__main__":
    main()
