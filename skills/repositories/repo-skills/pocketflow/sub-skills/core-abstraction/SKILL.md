---
name: core-abstraction
description: "Use PocketFlow's core graph runtime: Node, Flow, BatchNode,
  BatchFlow, async variants, action transitions, retries, fallback, and
  shared-store semantics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PocketFlow Core Abstraction

Use this sub-skill when the user asks about PocketFlow's public runtime semantics, a failing flow, or how to express a graph in terms of nodes, actions, shared state, params, batch behavior, or async orchestration.

## What this sub-skill covers

- `BaseNode`, `Node`, `BatchNode`, `Flow`, `BatchFlow`.
- `AsyncNode`, `AsyncBatchNode`, `AsyncParallelBatchNode`, `AsyncFlow`, `AsyncBatchFlow`, `AsyncParallelBatchFlow`.
- The `prep -> exec -> post` lifecycle.
- `>>` default transitions and `- "action" >>` named transitions.
- Retry/fallback behavior and `cur_retry`.
- Flow composition, nested flows, and flow-as-node routing.
- Shared store vs params.
- Batch and parallel semantics, including nested batches.

## What to read first

- [API reference](references/api-reference.md) for signatures and behavior.
- [Workflows](references/workflows.md) for linear, branching, nested, batch, async, and parallel recipes.
- [Troubleshooting](references/troubleshooting.md) for error messages, missing transitions, retry/fallback issues, and async misuse.
- [Core smoke helper](scripts/core_flow_smoke.py) for a deterministic local sanity check.

## Typical user requests

- "Why is my flow ending early?"
- "How do I branch on an action string?"
- "Why does BatchFlow not see my data?"
- "Why is my async node not running?"
- "How do I make a flow inside another flow?"
- "How do retries and fallbacks work?"

## Route map

| Need | Read |
| --- | --- |
| Method signatures, defaults, and runtime rules | `references/api-reference.md` |
| Linear, branching, nested, batch, async, or parallel recipes | `references/workflows.md` |
| Warning messages, failure modes, and repair steps | `references/troubleshooting.md` |
| Fast local runtime check | `scripts/core_flow_smoke.py` |

## Core mental model

### Node
A node is a tiny unit of work with optional `prep`, `exec`, and `post` methods.

- `prep(shared)` reads from the shared store and prepares input.
- `exec(prep_res)` performs the computation and may be retried.
- `post(shared, prep_res, exec_res)` writes results and returns the next action string.

### Flow
A flow orchestrates node transitions.

- Use `node_a >> node_b` for default transitions.
- Use `node_a - "search" >> node_b` for named transitions.
- The return value from `post()` determines which successor runs next.

### Batch
BatchFlow repeats a flow with parameter dictionaries.

- `BatchFlow.prep(shared)` returns a list of dicts.
- Each dict becomes `self.params` for the child flow.
- Child nodes read params from `self.params`, not from the shared store.

### Async and parallel
- `AsyncNode` and async flow types use `run_async()` / `prep_async()` / `exec_async()` / `post_async()`.
- `AsyncParallelBatchNode` and `AsyncParallelBatchFlow` are for independent I/O-bound work.
- Do not treat them as CPU-parallel primitives.

## Common success signals

- A branch flow runs the expected successor and stores the expected shared value.
- A retry node uses fallback after the final attempt and keeps the flow alive.
- A BatchNode returns a list of results in `post()` and the reduce node consumes that list.
- An async node completes under `AsyncFlow.run_async()` and mixed sync/async nodes can coexist in one async flow.

## Boundaries

- Do not use this sub-skill to design provider wrappers, LLM prompts, search, vector databases, or UI/service integrations. Those belong to `utilities` or `design-patterns`.
- Do not rely on original repository paths or cookbook files at runtime.
