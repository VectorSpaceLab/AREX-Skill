# Graph Workflows

Use `pydantic_graph` when a workflow is naturally a typed state machine or parallel graph. Prefer simpler Pydantic AI agents, tools, or plain Python functions unless explicit graph structure, visualization, step-by-step execution, or parallel fan-out/fan-in is valuable.

## Builder-First API

For new code, start with `GraphBuilder`:

- `GraphBuilder(name=..., state_type=..., deps_type=..., input_type=..., output_type=...)` declares graph-level types.
- `@g.step` wraps async step functions that receive `StepContext[StateT, DepsT, InputT]` and return the next value.
- `g.edge_from(source).to(destination)` wires steps, start/end nodes, joins, decisions, and `BaseNode` interop.
- `g.build()` validates and returns a builder-based `Graph`.
- `await graph.run(state=..., deps=..., inputs=...)` returns the final output value.
- `graph.render()` or `print(graph)` emits a Mermaid state diagram.

The legacy `BaseNode`-based `Graph` runner is deprecated when imported from `pydantic_graph`. `BaseNode`, `End`, and `GraphRunContext` still matter for builder interop and existing node classes, but do not start new designs by importing `Graph` from the top-level package.

## Minimal Step Graph

```python
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class CounterState:
    value: int = 0


g = GraphBuilder(state_type=CounterState, input_type=int, output_type=int)


@g.step
async def add_input(ctx: StepContext[CounterState, None, int]) -> int:
    ctx.state.value += ctx.inputs
    return ctx.state.value


@g.step
async def double(ctx: StepContext[CounterState, None, int]) -> int:
    return ctx.inputs * 2


g.add(
    g.edge_from(g.start_node).to(add_input),
    g.edge_from(add_input).to(double),
    g.edge_from(double).to(g.end_node),
)

graph = g.build()
# result = await graph.run(state=CounterState(), inputs=3)  # -> 6
```

Keep `StepContext` generic parameters aligned with the builder: first state, then deps, then the current step input. If no state/deps/input is used, annotate with `None` for that slot.

## State and Dependencies

Use state for mutable run progress, counters, caches, accumulated artifacts, or user/session data. Use deps for immutable services or handles passed into every step. Avoid hidden module globals when `state` or `deps` should make dependencies explicit.

```python
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class State:
    seen: list[str]


@dataclass(frozen=True)
class Deps:
    prefix: str


g = GraphBuilder(state_type=State, deps_type=Deps, input_type=str, output_type=str)


@g.step
async def remember(ctx: StepContext[State, Deps, str]) -> str:
    value = f'{ctx.deps.prefix}{ctx.inputs}'
    ctx.state.seen.append(value)
    return value
```

Pass `state=State(...)`, `deps=Deps(...)`, and `inputs=...` to `graph.run()`. Missing or mismatched annotations usually surface as build-time validation errors, wrong diagram edges, or type-checking failures.

## BaseNode Interop

Use `BaseNode` for existing node-style workflows or when a node's class and fields are the best representation. Register node classes with `g.node(NodeType)` so the builder can infer outgoing edges from `run()` return hints.

```python
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphBuilder, GraphRunContext, StepContext


@dataclass
class DivisibleByFive(BaseNode[None, None, int]):
    value: int

    async def run(self, ctx: GraphRunContext[None, None]) -> Increment | End[int]:
        if self.value % 5 == 0:
            return End(self.value)
        return Increment(self.value)


@dataclass
class Increment(BaseNode[None, None, int]):
    value: int

    async def run(self, ctx: GraphRunContext[None, None]) -> DivisibleByFive:
        return DivisibleByFive(self.value + 1)


g = GraphBuilder(input_type=int, output_type=int)


@g.step
async def start(ctx: StepContext[None, None, int]) -> DivisibleByFive:
    return DivisibleByFive(ctx.inputs)


g.add(
    g.edge_from(g.start_node).to(start),
    g.node(DivisibleByFive),
    g.node(Increment),
)

graph = g.build()
```

When a `BaseNode` can end the graph, include the output type as the third generic parameter and return `End[OutputT]`. Because generics are positional, include `None` for deps if you specify a run-end type without deps.

## Decisions

Use `g.decision()` plus `g.match(...)` for conditional routing. Simple types can be passed directly. Use `TypeExpression[...]` for `Literal`, unions, and other type forms that are not runtime classes.

```python
from typing import Literal

from pydantic_graph import GraphBuilder, StepContext, TypeExpression

g = GraphBuilder(output_type=str)


@g.step
async def choose(ctx: StepContext[None, None, None]) -> Literal['retry', 'done']:
    return 'done'


@g.step
async def retry(ctx: StepContext[None, None, object]) -> str:
    return 'retrying'


@g.step
async def done(ctx: StepContext[None, None, object]) -> str:
    return 'finished'


g.add(
    g.edge_from(g.start_node).to(choose),
    g.edge_from(choose).to(
        g.decision(note='route status')
        .branch(g.match(TypeExpression[Literal['retry']]).to(retry))
        .branch(g.match(TypeExpression[Literal['done']]).to(done))
    ),
    g.edge_from(retry, done).to(g.end_node),
)
```

Branches are checked in order; provide a catch-all branch such as `g.match(object)` only when a default route is intentional. If no branch matches at runtime, the graph fails.

## Parallel Maps, Broadcasts, and Joins

Use `.map()` to spread iterable or async-iterable outputs across parallel paths. Use broadcasting by routing one source to multiple destinations. Use a join to aggregate forked results before continuing.

```python
from pydantic_graph import GraphBuilder, StepContext, reduce_list_append

g = GraphBuilder(input_type=list[int], output_type=list[int])


@g.step
async def square(ctx: StepContext[None, None, int]) -> int:
    return ctx.inputs * ctx.inputs


collect = g.join(reduce_list_append, initial_factory=list[int])

g.add(
    g.edge_from(g.start_node).map().to(square),
    g.edge_from(square).to(collect),
    g.edge_from(collect).to(g.end_node),
)
```

For an input list that may be empty, pass `downstream_join_id=collect.id` to `.map(...)` or use `g.add_mapping_edge(..., downstream_join_id=collect.id)` so the join still produces its initial value.

Common reducers:

- `reduce_list_append`: collect each input as one list item.
- `reduce_list_extend`: extend a list with iterable inputs.
- `reduce_dict_update`: merge dictionaries.
- `reduce_sum`: sum numeric/additive values.
- `reduce_null`: discard outputs when only side effects matter.
- `ReduceFirstValue()`: keep the first value and cancel sibling tasks.

Use `initial_factory=list[int]` or `initial_factory=dict[str, int]` for mutable accumulators; avoid sharing one mutable `initial` object across runs.

## Transforms, Labels, and Diagrams

`g.edge_from(source)` returns a path builder. Add `.transform(sync_function)` for synchronous value shaping, `.label('...')` for diagram labels, `.map()` for spreading, and `.to(...)` for destinations.

```python

def normalize(ctx: StepContext[None, None, str]) -> str:
    return ctx.inputs.strip().casefold()


g.add(
    g.edge_from(g.start_node).label('raw input').transform(normalize).to(next_step),
)
```

Use `graph.render(title='Workflow')` for Mermaid source. If the diagram does not match your expected edges, check return annotations, edge sources, decision branches, and whether `g.add(...)` included every edge path.

## Step-by-Step Execution

Use `await graph.run(...)` for normal execution. Use `graph.iter(...)` when you need to inspect execution events, recover from node errors, or drive a graph step-by-step. The iterator can yield markers such as end or error events depending on the execution path; use this for advanced control rather than ordinary application code.

## Design Checklist

- Verify a graph is warranted; simple sequential logic should stay plain Python.
- Name state/deps dataclasses and step functions clearly because they appear in diagrams.
- Keep builder type parameters and step annotations consistent.
- Add all edges in one visible construction block when possible.
- Prefer builder steps for new work and `BaseNode` interop only when class-based nodes are useful or inherited.
- Sort joined results in assertions if parallel ordering is not semantically important.
- Render the diagram during development and compare it against the intended state machine.
