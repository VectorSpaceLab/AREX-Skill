#!/usr/bin/env python3
"""Service-free AdalFlow Component/Sequential/Prompt smoke check.

This script checks core component registration, synchronous and asynchronous
call paths, Prompt rendering, Sequential chaining, and the common missing
super().__init__() failure mode. It makes no provider, network, dataset, or
model calls.
"""

from __future__ import annotations

import asyncio
import json

import adalflow as adal


class NormalizeText(adal.Component):
    def __init__(self):
        super().__init__()

    def call(self, text: str) -> str:
        return " ".join(text.strip().lower().split())


class JoinPair(adal.Component):
    def __init__(self):
        super().__init__()

    def call(self, left: str, right: str) -> str:
        return f"{left}:{right}"


class AddSuffix(adal.Component):
    def __init__(self, suffix: str):
        super().__init__()
        self.suffix = suffix

    def call(self, text: str) -> str:
        return f"{text}{self.suffix}"


class AsyncMirror(adal.Component):
    def __init__(self):
        super().__init__()

    async def acall(self, text: str) -> str:
        await asyncio.sleep(0)
        return f"async:{text}"


class PromptPipeline(adal.Component):
    def __init__(self):
        super().__init__()
        self.normalize = NormalizeText()
        self.prompt = adal.Prompt(
            template="Question: {{ question }}\nMode: {{ mode }}",
            prompt_kwargs={"mode": "smoke"},
        )

    def call(self, question: str) -> str:
        return self.prompt(question=self.normalize(question))


def assert_missing_super_failure() -> None:
    class BrokenComponent(adal.Component):
        def __init__(self):
            self.child = AddSuffix("!")

    try:
        BrokenComponent()
    except AttributeError as exc:
        assert "component.__init__" in str(exc).lower()
    else:  # pragma: no cover - defensive; assertion should fail loudly.
        raise AssertionError("assigning a child before super().__init__() unexpectedly succeeded")


def main() -> None:
    assert_missing_super_failure()

    seq = adal.Sequential(JoinPair(), NormalizeText(), AddSuffix("!"))
    assert seq(" Hello ", " WORLD ") == "hello : world!"
    assert len(seq) == 3
    assert isinstance(seq[0], JoinPair)
    assert isinstance(seq[-1], AddSuffix)

    pipeline = PromptPipeline()
    rendered = pipeline("  HELLO   AdalFlow  ")
    assert rendered == "Question: hello adalflow\nMode: smoke"

    names = [name for name, _component in pipeline.named_components()]
    assert names[0] == ""
    assert "normalize" in names
    assert "prompt" in names

    pipeline.train()
    assert pipeline.training is True
    assert pipeline.normalize.training is True
    assert pipeline.prompt.training is False  # DataComponent stays non-trainable.
    pipeline.eval()
    assert pipeline.training is False
    assert pipeline.normalize.training is False

    assert asyncio.run(AsyncMirror().acall("ping")) == "async:ping"

    serial = pipeline.prompt.to_dict()
    restored_prompt = adal.Prompt.from_dict(serial)
    assert restored_prompt(question="x", mode="restored") == "Question: x\nMode: restored"

    summary = {
        "status": "ok",
        "checks": [
            "missing super().__init__ guard",
            "Sequential multi-arg chaining",
            "Prompt rendering",
            "nested component registration",
            "train/eval propagation",
            "explicit acall",
            "Prompt to_dict/from_dict",
        ],
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
