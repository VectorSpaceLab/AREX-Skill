#!/usr/bin/env python3
"""Print safe PocketFlow design-pattern skeletons.

The script uses only the standard library. It does not call external APIs.
"""

from __future__ import annotations

import argparse
from textwrap import dedent

TEMPLATES = {
    "workflow": dedent(
        '''
        from pocketflow import Node, Flow

        class Step1(Node):
            def prep(self, shared):
                return shared["input"]
            def exec(self, prep_res):
                return prep_res
            def post(self, shared, prep_res, exec_res):
                shared["step1"] = exec_res

        class Step2(Node):
            def prep(self, shared):
                return shared["step1"]
            def exec(self, prep_res):
                return prep_res
            def post(self, shared, prep_res, exec_res):
                shared["step2"] = exec_res

        step1 = Step1()
        step2 = Step2()
        step1 >> step2
        flow = Flow(start=step1)
        '''
    ).strip(),
    "agent-loop": dedent(
        '''
        from pocketflow import Node, Flow

        class Decide(Node):
            def post(self, shared, prep_res, exec_res):
                return "search"

        class Search(Node):
            def post(self, shared, prep_res, exec_res):
                shared.setdefault("history", []).append("searched")
                return "decide"

        class Answer(Node):
            def post(self, shared, prep_res, exec_res):
                shared["answer"] = "done"

        decide = Decide()
        search = Search()
        answer = Answer()
        decide - "search" >> search
        decide - "answer" >> answer
        search - "decide" >> decide
        flow = Flow(start=decide)
        '''
    ).strip(),
    "rag-skeleton": dedent(
        '''
        from pocketflow import Node, BatchNode, Flow

        class Chunk(Node):
            def prep(self, shared):
                return shared["docs"]
            def exec(self, docs):
                return docs
            def post(self, shared, prep_res, exec_res):
                shared["chunks"] = exec_res

        class Embed(BatchNode):
            def prep(self, shared):
                return shared["chunks"]
            def exec(self, chunk):
                return chunk
            def post(self, shared, prep_res, exec_res):
                shared["embeddings"] = exec_res

        class Answer(Node):
            def prep(self, shared):
                return shared["question"], shared["chunks"]
            def exec(self, prep_res):
                return "answer"
            def post(self, shared, prep_res, exec_res):
                shared["answer"] = exec_res

        chunk = Chunk()
        embed = Embed()
        answer = Answer()
        chunk >> embed >> answer
        flow = Flow(start=chunk)
        '''
    ).strip(),
    "map-reduce": dedent(
        '''
        from pocketflow import BatchNode, Node, Flow

        class MapStep(BatchNode):
            def prep(self, shared):
                return shared["items"]
            def exec(self, item):
                return item
            def post(self, shared, prep_res, exec_res):
                shared["mapped"] = exec_res

        class ReduceStep(Node):
            def prep(self, shared):
                return shared["mapped"]
            def exec(self, items):
                return items
            def post(self, shared, prep_res, exec_res):
                shared["reduced"] = exec_res

        node = MapStep()
        reduce_step = ReduceStep()
        node >> reduce_step
        flow = Flow(start=node)
        '''
    ).strip(),
    "async-service-skeleton": dedent(
        '''
        import asyncio
        from pocketflow import AsyncNode, AsyncFlow

        class Receive(AsyncNode):
            async def prep_async(self, shared):
                return shared["request"]
            async def exec_async(self, prep_res):
                return prep_res
            async def post_async(self, shared, prep_res, exec_res):
                shared["received"] = exec_res
                return "next"

        start = Receive()
        flow = AsyncFlow(start=start)
        asyncio.run(flow.run_async({"request": "hello"}))
        '''
    ).strip(),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe PocketFlow design-pattern templates.")
    parser.add_argument("template", choices=sorted(TEMPLATES), help="Template to print")
    args = parser.parse_args()
    print(TEMPLATES[args.template])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
