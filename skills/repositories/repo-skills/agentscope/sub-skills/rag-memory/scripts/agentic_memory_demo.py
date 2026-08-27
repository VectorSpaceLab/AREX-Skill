#!/usr/bin/env python3
"""Filesystem-backed long-term memory demo using AgenticMemoryMiddleware.

Prerequisites:
    - AgentScope installed with the memory-related extras used by the script.
    - `DASHSCOPE_API_KEY` set for the chat model.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

from pydantic import SecretStr

from agentscope.agent import Agent
from agentscope.credential import DashScopeCredential
from agentscope.event import (
    TextBlockDeltaEvent,
    ToolCallDeltaEvent,
    ToolCallStartEvent,
    ToolResultEndEvent,
    ToolResultTextDeltaEvent,
)
from agentscope.message import UserMsg
from agentscope.middleware import AgenticMemoryMiddleware
from agentscope.model import DashScopeChatModel
from agentscope.permission import AdditionalWorkingDirectory, PermissionMode
from agentscope.tool import Read, Toolkit, Write


DEMO_ROOT = Path(__file__).with_name("demo_workspace")
FIRST_USER_MESSAGE = """
Please remember these durable facts for future conversations in this workspace:

- My name is Alice Chen.
- I live in Hangzhou.
- I prefer concise Chinese answers.
- When evaluating examples, I like seeing a fresh Agent instance prove that
  long-term memory was persisted outside the current conversation state.

Use the filesystem memory instructions in your system prompt: create or update
a topic Markdown memory file with frontmatter, and update MEMORY.md with a
short pointer to that file. Read MEMORY.md first if you need to update it.
""".strip()
SECOND_USER_MESSAGE = """
What do you remember about my name, location, answer style, and how I like
examples to demonstrate long-term memory? Read the relevant memory files if
you need details before answering.
""".strip()



def _configure_permissions(agent: Agent, workspace_root: Path) -> None:
    agent.state.permission_context.mode = PermissionMode.ACCEPT_EDITS
    agent.state.permission_context.working_directories[str(workspace_root)] = (
        AdditionalWorkingDirectory(
            path=str(workspace_root),
            source="filesystem-memory-demo",
        )
    )



def _build_agent(model: DashScopeChatModel, workspace_root: Path) -> Agent:
    memory = AgenticMemoryMiddleware(workdir=str(workspace_root))
    agent = Agent(
        name="memory_assistant",
        system_prompt=(
            "You are a concise assistant. When the user asks you to remember "
            "durable preferences or profile facts, persist them using the "
            "filesystem memory instructions. Use the Read and Write tools for "
            "memory files."
        ),
        model=model,
        toolkit=Toolkit(tools=[Read(), Write()]),
        middlewares=[memory],
    )
    _configure_permissions(agent, workspace_root)
    return agent


async def _run_turn(agent: Agent, text: str) -> str:
    reply_parts: list[str] = []
    tool_names: dict[str, str] = {}
    tool_args: dict[str, str] = {}
    tool_results: dict[str, str] = {}

    async for event in agent.reply_stream(UserMsg("alice", text)):
        if isinstance(event, ToolCallStartEvent):
            tool_names[event.tool_call_id] = event.tool_call_name
            tool_args[event.tool_call_id] = ""
            tool_results[event.tool_call_id] = ""
        elif isinstance(event, ToolCallDeltaEvent):
            tool_args[event.tool_call_id] += event.delta
        elif isinstance(event, ToolResultTextDeltaEvent):
            tool_results[event.tool_call_id] += event.delta
        elif isinstance(event, ToolResultEndEvent):
            tool_id = event.tool_call_id
            print(f"[tool] {tool_names.pop(tool_id, '<unknown>')} -> {event.state}")
            arguments = tool_args.pop(tool_id, "")
            result = tool_results.pop(tool_id, "")
            if arguments:
                print(f"  args: {arguments}")
            for line in result.splitlines():
                print(f"  {line}")
        elif isinstance(event, TextBlockDeltaEvent):
            reply_parts.append(event.delta)

    return "".join(reply_parts)



def _print_memory_files(workspace_root: Path) -> None:
    memory_root = workspace_root / "Memory"
    print(f"\n[Markdown memory files] {memory_root}")
    if not memory_root.exists():
        print("  The Memory directory has not been created yet.")
        return
    for path in sorted(memory_root.rglob("*.md")):
        print(f"\n--- {path.relative_to(workspace_root)} ---")
        print(path.read_text(encoding="utf-8").strip())



def _print_soft_verification(workspace_root: Path) -> None:
    memory_root = workspace_root / "Memory"
    combined = (
        "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in sorted(memory_root.rglob("*.md"))
        )
        if memory_root.exists()
        else ""
    )
    checks = {
        "MEMORY.md exists": (memory_root / "MEMORY.md").exists(),
        "mentions Alice Chen": "Alice Chen" in combined,
        "mentions Hangzhou": "Hangzhou" in combined,
        "mentions concise Chinese answers": (
            "concise Chinese" in combined or "Chinese answers" in combined
        ),
    }

    print("\n[Soft verification]")
    for label, ok in checks.items():
        print(f"  {'PASS' if ok else 'WARN'} - {label}")


async def main() -> None:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("Set DASHSCOPE_API_KEY before running this demo.")

    print(f"=== resetting demo workspace: {DEMO_ROOT} ===")
    shutil.rmtree(DEMO_ROOT, ignore_errors=True)
    DEMO_ROOT.mkdir(parents=True, exist_ok=True)

    model = DashScopeChatModel(
        credential=DashScopeCredential(api_key=SecretStr(api_key)),
        model="qwen3.7-max",
        stream=False,
    )

    print("\n=== Turn 1: ask the Agent to persist user memory ===")
    agent = _build_agent(model, DEMO_ROOT)
    print(f"[user]\n{FIRST_USER_MESSAGE}\n")
    first_reply = await _run_turn(agent, FIRST_USER_MESSAGE)
    print(f"\n[assistant]\n{first_reply}")

    _print_memory_files(DEMO_ROOT)
    _print_soft_verification(DEMO_ROOT)

    print("\n=== Turn 2: ask the same Agent to recall memory ===")
    print(f"[user]\n{SECOND_USER_MESSAGE}\n")
    second_reply = await _run_turn(agent, SECOND_USER_MESSAGE)
    print(f"\n[assistant]\n{second_reply}")


if __name__ == "__main__":
    asyncio.run(main())
