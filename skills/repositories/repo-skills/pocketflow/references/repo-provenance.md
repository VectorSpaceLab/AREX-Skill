# PocketFlow repo provenance

This file records the public source snapshot used to construct this self-contained repo skill. It is for staleness detection and does not require access to the original checkout at runtime.

## Source snapshot

| Field | Value |
| --- | --- |
| Schema | `disco.repo-provenance.v1` |
| Repository | PocketFlow |
| Public remote | `https://github.com/The-Pocket/PocketFlow.git` |
| Commit | `f74d023f93607b8c3268133339a5e532a949898c` |
| Branch | `main` |
| Exact tag | none found |
| Working tree state | source tree clean at snapshot time before generated skill artifacts were written |
| Distribution name | `pocketflow` |
| Package version | `0.0.3` |
| Runtime import module | `pocketflow` |
| Required backend for verified core scope | CPU / standard Python |

## Public runtime surface inspected

The installed package exposed these public names:

- `BaseNode`
- `Node`
- `BatchNode`
- `Flow`
- `BatchFlow`
- `AsyncNode`
- `AsyncBatchNode`
- `AsyncParallelBatchNode`
- `AsyncFlow`
- `AsyncBatchFlow`
- `AsyncParallelBatchFlow`

Constructor signatures verified from the installed package:

- `Node(max_retries=1, wait=0)`
- `BatchNode(max_retries=1, wait=0)`
- `Flow(start=None)`
- `BatchFlow(start=None)`
- `AsyncNode(max_retries=1, wait=0)`
- `AsyncBatchNode(max_retries=1, wait=0)`
- `AsyncParallelBatchNode(max_retries=1, wait=0)`
- `AsyncFlow(start=None)`
- `AsyncBatchFlow(start=None)`
- `AsyncParallelBatchFlow(start=None)`

## Evidence paths used

Relative source evidence paths considered during construction:

- `setup.py`
- `README.md`
- `cookbook/README.md`
- `pocketflow/__init__.py`
- `pocketflow/__init__.pyi`
- `docs/guide.md`
- `docs/core_abstraction/node.md`
- `docs/core_abstraction/flow.md`
- `docs/core_abstraction/communication.md`
- `docs/core_abstraction/batch.md`
- `docs/core_abstraction/async.md`
- `docs/core_abstraction/parallel.md`
- `docs/design_pattern/agent.md`
- `docs/design_pattern/workflow.md`
- `docs/design_pattern/rag.md`
- `docs/design_pattern/mapreduce.md`
- `docs/design_pattern/structure.md`
- `docs/design_pattern/multi_agent.md`
- `docs/utility_function/llm.md`
- `docs/utility_function/websearch.md`
- `docs/utility_function/chunking.md`
- `docs/utility_function/embedding.md`
- `docs/utility_function/vector.md`
- `docs/utility_function/text_to_speech.md`
- `docs/utility_function/viz.md`
- `tests/test_flow_basic.py`
- `tests/test_flow_composition.py`
- `tests/test_batch_node.py`
- `tests/test_batch_flow.py`
- `tests/test_async_flow.py`
- `tests/test_async_batch_node.py`
- `tests/test_async_batch_flow.py`
- `tests/test_async_parallel_batch_node.py`
- `tests/test_async_parallel_batch_flow.py`
- `tests/test_fall_back.py`
- Selected cookbook recipe directories for workflow intent and optional integration caveats.

## Refresh triggers

Refresh this skill if a newer PocketFlow release changes any of these:

- The class names, constructor defaults, method signatures, action-transition syntax, or async/batch semantics.
- The recommended project structure or agentic-coding process.
- The cookbook recipe set or optional dependency patterns.
- The package version or installation story.
- Native tests begin requiring non-CPU backends for selected core behavior.
