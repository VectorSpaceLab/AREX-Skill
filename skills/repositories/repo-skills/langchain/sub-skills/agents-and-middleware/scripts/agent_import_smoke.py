#!/usr/bin/env python3
"""Import-only smoke check for LangChain v1 agent and middleware APIs.

This script is intentionally safe: it imports public symbols and inspects a few
lightweight properties without instantiating provider clients, calling networks,
executing shell commands, or reading user files.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterable


MODULES: tuple[str, ...] = (
    "langchain.chat_models",
    "langchain.agents",
    "langchain.agents.structured_output",
    "langchain.agents.middleware",
    "langchain.tools",
    "langchain.embeddings",
)

REQUIRED_SYMBOLS: dict[str, tuple[str, ...]] = {
    "langchain.chat_models": ("init_chat_model", "BaseChatModel"),
    "langchain.agents": ("create_agent", "AgentState"),
    "langchain.agents.structured_output": (
        "ToolStrategy",
        "ProviderStrategy",
        "StructuredOutputValidationError",
        "MultipleStructuredOutputsError",
    ),
    "langchain.agents.middleware": (
        "AgentMiddleware",
        "ModelRequest",
        "ModelResponse",
        "ModelRetryMiddleware",
        "ModelFallbackMiddleware",
        "HumanInTheLoopMiddleware",
        "SummarizationMiddleware",
        "ModelCallLimitMiddleware",
        "ToolCallLimitMiddleware",
        "PIIMiddleware",
        "FilesystemFileSearchMiddleware",
        "ShellToolMiddleware",
        "TodoListMiddleware",
        "ProviderToolSearchMiddleware",
        "wrap_model_call",
        "wrap_tool_call",
    ),
    "langchain.tools": ("tool", "BaseTool", "ToolRuntime", "InjectedState", "InjectedStore"),
    "langchain.embeddings": ("Embeddings", "init_embeddings"),
}


def _missing_symbols(module_name: str, symbols: Iterable[str]) -> list[str]:
    module = importlib.import_module(module_name)
    return [symbol for symbol in symbols if not hasattr(module, symbol)]


def main() -> int:
    failures: list[str] = []

    for module_name in MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{module_name}: import failed: {exc!r}")
            continue

        missing = _missing_symbols(module_name, REQUIRED_SYMBOLS.get(module_name, ()))
        if missing:
            failures.append(f"{module_name}: missing symbols: {', '.join(missing)}")

    if failures:
        print("LangChain agent import smoke check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("LangChain agent import smoke check passed.")
    print("Checked imports only; no provider, network, shell, or file-search execution was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
