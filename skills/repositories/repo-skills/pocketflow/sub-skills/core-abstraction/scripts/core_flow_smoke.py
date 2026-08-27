#!/usr/bin/env python3
"""Deterministic PocketFlow core behavior smoke tests.

Run after installing pocketflow in any Python environment:
    python core_flow_smoke.py
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from pocketflow import (
    AsyncFlow,
    AsyncNode,
    AsyncParallelBatchNode,
    BatchFlow,
    BatchNode,
    Flow,
    Node,
)


class Start(Node):
    def prep(self, shared: dict[str, Any]) -> None:
        shared["value"] = 1

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: Any) -> str:
        return "inc"


class Inc(Node):
    def prep(self, shared: dict[str, Any]) -> None:
        shared["value"] += 1


class Fallback(Node):
    def __init__(self):
        super().__init__(max_retries=3)
        self.count = 0

    def exec(self, prep_res: Any) -> str:
        self.count += 1
        raise ValueError("intentional smoke failure")

    def exec_fallback(self, prep_res: Any, exc: Exception) -> str:
        return "fallback-ok"

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: str) -> None:
        shared["fallback"] = exec_res
        shared["attempts"] = self.count


class Doubles(BatchNode):
    def prep(self, shared: dict[str, Any]):
        return shared["items"]

    def exec(self, item: int) -> int:
        return item * 2

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: list[int]) -> None:
        shared["doubles"] = exec_res


class ForKeys(BatchFlow):
    def prep(self, shared: dict[str, Any]):
        return [{"key": key} for key in shared["input_data"]]


class CopyByParam(Node):
    def prep(self, shared: dict[str, Any]) -> None:
        key = self.params["key"]
        shared.setdefault("seen", {})[key] = shared["input_data"][key]


class AsyncUpper(AsyncNode):
    async def prep_async(self, shared: dict[str, Any]) -> str:
        return shared["text"]

    async def exec_async(self, prep_res: str) -> str:
        await asyncio.sleep(0)
        return prep_res.upper()

    async def post_async(self, shared: dict[str, Any], prep_res: str, exec_res: str) -> str:
        shared["upper"] = exec_res
        return "done"


class AsyncDoubleMany(AsyncParallelBatchNode):
    async def prep_async(self, shared: dict[str, Any]):
        return shared["numbers"]

    async def exec_async(self, item: int) -> int:
        await asyncio.sleep(0)
        return item * 2

    async def post_async(self, shared: dict[str, Any], prep_res: Any, exec_res: list[int]) -> None:
        shared["parallel"] = exec_res


def smoke_flow() -> dict[str, Any]:
    start = Start()
    inc = Inc()
    fallback = Fallback()
    start - "inc" >> inc
    inc >> fallback
    shared: dict[str, Any] = {}
    Flow(start=start).run(shared)
    assert shared["value"] == 2, shared
    assert shared["fallback"] == "fallback-ok", shared
    assert shared["attempts"] == 3, shared
    return shared


def smoke_batch() -> dict[str, Any]:
    shared: dict[str, Any] = {"items": [1, 2, 3], "input_data": {"a": 1, "b": 2}}
    Doubles().run(shared)
    assert shared["doubles"] == [2, 4, 6], shared
    ForKeys(start=CopyByParam()).run(shared)
    assert shared["seen"] == {"a": 1, "b": 2}, shared
    return shared


async def smoke_async() -> dict[str, Any]:
    shared: dict[str, Any] = {"text": "ok", "numbers": [1, 2, 3]}
    await AsyncFlow(start=AsyncUpper()).run_async(shared)
    assert shared["upper"] == "OK", shared
    await AsyncFlow(start=AsyncDoubleMany()).run_async(shared)
    assert shared["parallel"] == [2, 4, 6], shared
    return shared


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PocketFlow core smoke checks.")
    parser.add_argument("--mode", choices=["all", "flow", "batch", "async"], default="all")
    args = parser.parse_args()

    if args.mode in ("all", "flow"):
        print("flow", smoke_flow())
    if args.mode in ("all", "batch"):
        print("batch", smoke_batch())
    if args.mode in ("all", "async"):
        print("async", asyncio.run(smoke_async()))
    print("core_flow_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
