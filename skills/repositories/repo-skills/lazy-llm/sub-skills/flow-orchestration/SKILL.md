---
name: flow-orchestration
description: "Guides LazyLLM pipeline, parallel, branching, looping, binding,
  graph, and traceable flow orchestration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Flow Orchestration

Use this sub-skill when a task asks how to compose LazyLLM flows with `pipeline`, `parallel`, `diverter`, `switch`, `ifs`, `loop`, `warp`, `barrier`, `bind`, nested contexts, or traceable graph execution.

## Start here when

- The user wants to turn Python functions, model modules, RAG retrievers, or agents into a LazyLLM workflow.
- A flow returns an unexpected tuple/list/dict shape.
- The task mentions `_skip_items`, `_kept_items`, `_scatter`, `_concurrent`, `bind`, `pipeline()` context managers, nested subflows, or conditional/loop execution.
- You need to replace model/RAG/agent nodes with deterministic callables before debugging orchestration.

## Files to read

- [flow-recipes.md](references/flow-recipes.md) for concise recipes and common shape semantics.
- [troubleshooting.md](references/troubleshooting.md) for output-shape, binding, and backend debugging failures.
- [scripts/flow_smoke.py](scripts/flow_smoke.py) for a safe Python-callable flow smoke test.

## Safe flow-building sequence

1. **Sketch the data shape** at each node before adding LazyLLM primitives.
2. **Prototype with deterministic Python callables** rather than models/providers.
3. **Choose the primitive.**
   - `pipeline`: sequential composition.
   - `parallel`: same input through multiple stages; can return tuples and skip/keep items.
   - `diverter`: distribute positional/list/tuple/dict inputs to separate functions.
   - `switch`/`ifs`: conditional routing.
   - `loop`: repeated execution with count or stop condition.
   - `bind`: bind flow inputs or prior stage outputs into callable parameters.
4. **Run `scripts/flow_smoke.py`** to confirm the environment and expected semantics.
5. **Swap in heavy nodes last** and route their setup to model-deployment, RAG, agents-tools, or writer-review.

## Verified examples from tests

- `pipeline(add_one, add_one)(1) == 3`.
- Context manager pipelines can name stages and bind the original input or previous outputs into later stages.
- `parallel(add_one, add_one)(1) == (2, 2)`.
- `_skip_items` and `_kept_items` select by index or by named stage, but cannot be provided together.
- `switch` supports predicate-to-action maps, default cases, conversion functions, and full-input judging.
- `ifs` supports booleans and callable conditions and propagates real condition exceptions.
- `loop` supports fixed counts, stop conditions, and runtime limit expansion.

## Cross-sub-skill links

- Use [model-deployment](../model-deployment/SKILL.md) when a flow node calls `OnlineModule`, `TrainableModule`, or `ServerModule`.
- Use [rag-document-processing](../rag-document-processing/SKILL.md) when a flow node ingests documents, retrieves nodes, or reranks contexts.
- Use [agents-tools](../agents-tools/SKILL.md) when a flow node is a tool manager or agent.
- Use [writer-review](../writer-review/SKILL.md) when flow output is a writer artifact or review command plan.

## Handoff checklist

When you finish a flow task, provide:

- primitive choice and why,
- input/output shape for each stage,
- minimal deterministic smoke result,
- where model/RAG/agent/writer nodes are configured,
- any concurrency/multiprocessing or side-effect warnings.
