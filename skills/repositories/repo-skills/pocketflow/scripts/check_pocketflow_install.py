#!/usr/bin/env python3
"""Quick PocketFlow installation and behavior smoke checks.

This helper uses only the installed package and stdlib. It checks that the
public graph runtime imports, runs a branching flow, exercises retry/fallback,
and confirms batch and async basics.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from pocketflow import AsyncNode, BatchNode, Flow, Node


class BranchStart(Node):
    def prep(self, shared: dict[str, Any]) -> None:
        shared["branch"] = "left"

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: Any) -> str:
        return "go"


class BranchEnd(Node):
    def prep(self, shared: dict[str, Any]) -> None:
        shared["done"] = True


class TotalNode(BatchNode):
    def prep(self, shared: dict[str, Any]):
        return [1, 2, 3]

    def exec(self, item: int) -> int:
        return item * 2

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: list[int]) -> str:
        shared["total"] = sum(exec_res)
        return "default"


class RetryNode(Node):
    def __init__(self):
        super().__init__(max_retries=2)
        self.attempts = 0

    def exec(self, prep_res: Any) -> str:
        self.attempts += 1
        raise RuntimeError("intentional failure")

    def exec_fallback(self, prep_res: Any, exc: Exception) -> str:
        return "fallback"

    def post(self, shared: dict[str, Any], prep_res: Any, exec_res: str) -> None:
        shared["fallback"] = exec_res


class AsyncEchoNode(AsyncNode):
    async def prep_async(self, shared: dict[str, Any]) -> str:
        return shared["message"]

    async def exec_async(self, prep_res: str) -> str:
        return prep_res.upper()

    async def post_async(self, shared: dict[str, Any], prep_res: str, exec_res: str) -> str:
        shared["echo"] = exec_res
        return "done"


async def async_smoke() -> dict[str, Any]:
    shared: dict[str, Any] = {"message": "ok"}
    node = AsyncEchoNode()
    await node.run_async(shared)
    return shared


def run_all() -> None:
    shared: dict[str, Any] = {}
    start = BranchStart()
    end = BranchEnd()
    start - "go" >> end
    Flow(start=start).run(shared)
    assert shared == {"branch": "left", "done": True}, shared

    shared = {}
    TotalNode().run(shared)
    assert shared["total"] == 12, shared

    shared = {}
    retry = RetryNode()
    retry.run(shared)
    assert shared["fallback"] == "fallback", shared
    assert retry.attempts == 2, retry.attempts

    shared = asyncio.run(async_smoke())
    assert shared["echo"] == "OK", shared

    print("PocketFlow install smoke ok")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=["all"], default="all")
    args = parser.parse_args()
    if args.check == "all":
        run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
