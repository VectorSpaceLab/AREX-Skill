#!/usr/bin/env python3
"""Run a deterministic no-network smoke check for pydantic-evals and pydantic-graph.

Usage:
    python path/to/evals_graph_smoke.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext, EqualsExpected, IsInstance
from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class ContainsKeyword(Evaluator[str, str, dict[str, str]]):
    """Assert that the task output contains a metadata-provided keyword."""

    def evaluate(self, ctx: EvaluatorContext[str, str, dict[str, str]]) -> EvaluationReason:
        keyword = (ctx.metadata or {}).get('keyword', '')
        matched = keyword.casefold() in ctx.output.casefold()
        return EvaluationReason(value=matched, reason=None if matched else f'missing keyword {keyword!r}')


def normalize(text: str) -> str:
    return ' '.join(text.casefold().split())


async def run_eval_smoke() -> None:
    dataset = Dataset[str, str, dict[str, str]](
        name='evals_graph_smoke',
        cases=[
            Case(
                name='spacing',
                inputs='  Hello   WORLD ',
                expected_output='hello world',
                metadata={'keyword': 'world'},
            ),
            Case(
                name='unicode',
                inputs='CAFÉ   AU   LAIT',
                expected_output='café au lait',
                metadata={'keyword': 'café'},
            ),
        ],
        evaluators=[IsInstance(type_name='str'), EqualsExpected(), ContainsKeyword()],
    )
    report = await dataset.evaluate(normalize, progress=False, max_concurrency=1)
    averages = report.averages()
    if averages is None or averages.assertions != 1.0:
        raise AssertionError(f'eval smoke failed: {averages!r}')


@dataclass
class GraphState:
    processed: int = 0


async def run_graph_smoke() -> None:
    builder = GraphBuilder(state_type=GraphState, input_type=list[int], output_type=list[int])

    @builder.step
    async def square(ctx: StepContext[GraphState, None, int]) -> int:
        ctx.state.processed += 1
        return ctx.inputs * ctx.inputs

    collect = builder.join(reduce_list_append, initial_factory=list[int])
    builder.add(
        builder.edge_from(builder.start_node).map().to(square),
        builder.edge_from(square).to(collect),
        builder.edge_from(collect).to(builder.end_node),
    )
    graph = builder.build()
    state = GraphState()
    result = await graph.run(state=state, inputs=[1, 2, 3])
    if sorted(result) != [1, 4, 9] or state.processed != 3:
        raise AssertionError(f'graph smoke failed: result={result!r}, state={state!r}')
    rendered = graph.render(title='Smoke Graph')
    required_fragments: tuple[str, ...] = ('Smoke Graph', 'square', '[*]')
    missing = [fragment for fragment in required_fragments if fragment not in rendered]
    if missing:
        raise AssertionError(f'graph render missing fragments: {missing!r}')


async def main() -> None:
    await run_eval_smoke()
    await run_graph_smoke()
    print('evals_graph_smoke: ok')


if __name__ == '__main__':
    asyncio.run(main())
