#!/usr/bin/env python3
"""Safe AutoGen core-runtime smoke checks.

This script performs no network or service calls. By default it inspects key
installed API signatures. With --run-local-example it also runs a tiny in-process
SingleThreadedAgentRuntime example.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import sys
from dataclasses import dataclass
from importlib import metadata
from typing import Any


def _version(package_name: str) -> str:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "not installed"


def inspect_signatures() -> int:
    try:
        from autogen_core import AgentId, DefaultTopicId, RoutedAgent, SingleThreadedAgentRuntime, message_handler, type_subscription
        from autogen_core.model_context import BufferedChatCompletionContext, TokenLimitedChatCompletionContext
        from autogen_core.models import AssistantMessage, UserMessage
        from autogen_core.tools import FunctionTool, StaticWorkbench
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as exc:
        print(f"AutoGen core is not importable in this Python environment: {exc}", file=sys.stderr)
        print("Install/use an environment with autogen-core before running this smoke check.", file=sys.stderr)
        return 2

    objects: list[tuple[str, Any]] = [
        ("SingleThreadedAgentRuntime", SingleThreadedAgentRuntime),
        ("RoutedAgent", RoutedAgent),
        ("message_handler", message_handler),
        ("type_subscription", type_subscription),
        ("DefaultTopicId", DefaultTopicId),
        ("AgentId", AgentId),
        ("FunctionTool", FunctionTool),
        ("StaticWorkbench", StaticWorkbench),
        ("UserMessage", UserMessage),
        ("AssistantMessage", AssistantMessage),
        ("BufferedChatCompletionContext", BufferedChatCompletionContext),
        ("TokenLimitedChatCompletionContext", TokenLimitedChatCompletionContext),
    ]

    print("Installed package versions:")
    for package_name in ["autogen-core", "autogen-agentchat", "autogen-ext", "pyautogen", "agbench"]:
        print(f"  {package_name}: {_version(package_name)}")

    print("\nCore signatures:")
    for name, obj in objects:
        print(f"  {name}{inspect.signature(obj)}")

    return 0


@dataclass
class Ping:
    text: str


@dataclass
class Pong:
    text: str


async def _run_local_example_async() -> str:
    from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler

    class EchoAgent(RoutedAgent):
        def __init__(self) -> None:
            super().__init__("Local echo agent for smoke testing")

        @message_handler
        async def handle_ping(self, message: Ping, ctx: MessageContext) -> Pong:
            return Pong(text=f"echo:{message.text}")

    runtime = SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)
    await EchoAgent.register(runtime, "echo", lambda: EchoAgent())
    runtime.start()
    try:
        response = await runtime.send_message(Ping("ok"), recipient=AgentId("echo", "default"))
        if not isinstance(response, Pong):
            raise TypeError(f"Expected Pong response, got {type(response)!r}")
        if response.text != "echo:ok":
            raise AssertionError(f"Unexpected response text: {response.text!r}")
        return response.text
    finally:
        await runtime.stop()


def run_local_example() -> int:
    try:
        response_text = asyncio.run(_run_local_example_async())
    except (ModuleNotFoundError, metadata.PackageNotFoundError) as exc:
        print(f"AutoGen core is not importable in this Python environment: {exc}", file=sys.stderr)
        print("Install/use an environment with autogen-core before running this smoke check.", file=sys.stderr)
        return 2
    print(f"Local runtime example response: {response_text}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect AutoGen core runtime APIs and optionally run a local runtime smoke example.")
    parser.add_argument("--inspect", action="store_true", help="Inspect key installed package versions and API signatures.")
    parser.add_argument("--run-local-example", action="store_true", help="Run a tiny in-process runtime send/response example.")
    args = parser.parse_args()

    if not args.inspect and not args.run_local_example:
        args.inspect = True

    exit_code = 0
    if args.inspect:
        exit_code = inspect_signatures() or exit_code
    if args.run_local_example:
        exit_code = run_local_example() or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
