#!/usr/bin/env python3
"""Run a deterministic no-network smolagents CodeAgent inspection demo."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def make_deterministic_code_model(answer: str):
    try:
        from smolagents import Model
        from smolagents.models import ChatMessage, ChatMessageStreamDelta, MessageRole
        from smolagents.monitoring import TokenUsage
    except ModuleNotFoundError as error:
        raise SystemExit(f"Cannot run demo: smolagents or one of its dependencies is unavailable ({error}).") from error

    class DeterministicCodeModel(Model):
        """Tiny model that emits one valid CodeAgent action without network calls."""

        model_id = "deterministic-code-model"

        def __init__(self, answer: str) -> None:
            self.answer = answer
            self.calls = 0

        def generate(
            self, messages: list[ChatMessage], stop_sequences: list[str] | None = None, **kwargs: Any
        ) -> ChatMessage:
            self.calls += 1
            content = f"Thought: I can answer directly.\n<code>\nfinal_answer({self.answer!r})\n</code>"
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=content,
                token_usage=TokenUsage(input_tokens=10, output_tokens=8),
            )

        def generate_stream(self, messages: list[ChatMessage], stop_sequences: list[str] | None = None, **kwargs: Any):
            message = self.generate(messages, stop_sequences=stop_sequences, **kwargs)
            content = str(message.content or "")
            for chunk in [content[: len(content) // 2], content[len(content) // 2 :]]:
                yield ChatMessageStreamDelta(content=chunk)

        def to_dict(self) -> dict[str, Any]:
            return {"answer": self.answer}

        @classmethod
        def from_dict(cls, model_dictionary: dict[str, Any]) -> "DeterministicCodeModel":
            return cls(answer=model_dictionary.get("answer", "demo answer"))

    return DeterministicCodeModel(answer)


def summarize_steps(agent: Any) -> list[dict[str, Any]]:
    summary = []
    for step in agent.memory.steps:
        summary.append(
            {
                "type": type(step).__name__,
                "step_number": getattr(step, "step_number", None),
                "is_final_answer": getattr(step, "is_final_answer", None),
                "error": str(getattr(step, "error", "") or "") or None,
                "code_action": getattr(step, "code_action", None),
                "observations": getattr(step, "observations", None),
            }
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a deterministic smolagents CodeAgent run without network or credentials."
    )
    parser.add_argument("--task", default="Return a tiny deterministic answer.", help="Task text passed to agent.run().")
    parser.add_argument("--answer", default="demo answer", help="Final answer emitted by the fake model.")
    parser.add_argument("--stream", action="store_true", help="Consume agent.run(..., stream=True) and print event types.")
    parser.add_argument(
        "--full-result",
        action="store_true",
        help="Return and print RunResult fields instead of only the final answer.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary suitable for automated smoke checks.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        from smolagents import CodeAgent
    except ModuleNotFoundError as error:
        print(f"Cannot run demo: smolagents or one of its dependencies is unavailable ({error}).", file=sys.stderr)
        return 2

    agent = CodeAgent(
        tools=[],
        model=make_deterministic_code_model(args.answer),
        max_steps=2,
        return_full_result=args.full_result,
        stream_outputs=args.stream,
    )

    stream_events: list[str] = []
    if args.stream:
        final_output = None
        for event in agent.run(args.task, stream=True):
            event_type = type(event).__name__
            stream_events.append(event_type)
            if not args.json:
                print(f"event: {event_type}")
            if event_type == "FinalAnswerStep":
                final_output = event.output
        result_payload: Any = final_output
    else:
        result_payload = agent.run(args.task)

    if args.full_result and not args.stream:
        output = result_payload.output
        state = result_payload.state
        token_usage = result_payload.token_usage.dict() if result_payload.token_usage else None
    else:
        output = result_payload
        state = None
        token_usage = None

    payload = {
        "output": output,
        "state": state,
        "token_usage": token_usage,
        "stream_events": stream_events,
        "steps": summarize_steps(agent),
        "full_code": agent.memory.return_full_code(),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"output: {payload['output']}")
        if state is not None:
            print(f"state: {state}")
            print(f"token_usage: {token_usage}")
        print("steps:")
        for step in payload["steps"]:
            print(f"- {step['type']} step={step['step_number']} final={step['is_final_answer']} error={step['error']}")
        print("full_code:")
        print(payload["full_code"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
