#!/usr/bin/env python3
"""Offline smoke test for the Atomic Agents core API."""

from __future__ import annotations

from types import SimpleNamespace

from pydantic import Field

from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator


class InputSchema(BaseIOSchema):
    """Smoke-test input schema."""

    message: str = Field(..., description="Message to echo")


class OutputSchema(BaseIOSchema):
    """Smoke-test output schema."""

    reply: str = Field(..., description="Echoed reply")


class DummyClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create, create_partial=self.create_partial))

    def create(self, *, messages, model, response_model, **kwargs):
        assert messages, "expected at least one message"
        assert model
        return response_model(reply=f"echo: {messages[-1]['content']}")

    def create_partial(self, *, messages, model, response_model, **kwargs):
        yield response_model(reply="partial-1")
        yield response_model(reply="partial-2")


def main() -> int:
    client = DummyClient()
    config = AgentConfig.model_construct(
        client=client,
        model="gpt-5-mini",
        history=ChatHistory(),
        system_prompt_generator=SystemPromptGenerator(background=["You are a smoke-test agent."]),
    )
    agent = AtomicAgent[InputSchema, OutputSchema](config)

    result = agent.run(InputSchema(message="hello"))
    assert result.reply.startswith("echo:"), result
    assert agent.history.get_message_count() == 2

    agent.reset_history()
    assert agent.history.get_message_count() == 0

    print("atomic-core smoke ok")
    print(result.reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
