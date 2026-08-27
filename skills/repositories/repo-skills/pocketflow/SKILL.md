---
name: pocketflow
description: "Use PocketFlow, a tiny Python graph framework for LLM
  applications, agents, workflows, RAG, batch processing, async orchestration,
  and supporting utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# PocketFlow Repo Skill

Use this skill when a task asks to build, debug, review, or explain a PocketFlow application or to translate an LLM-system design into PocketFlow nodes and flows. PocketFlow is intentionally minimal: the installed package exposes a compact graph runtime with no built-in LLM provider, vector database, search, UI, audio, or tracing integration. Those integrations live in user utilities that PocketFlow nodes call.

## Fast recognition

Read this skill when the user mentions any of these signals:

- `pocketflow`, `Pocket Flow`, or a 100-line LLM framework.
- `Node`, `Flow`, `BatchNode`, `BatchFlow`, `AsyncNode`, `AsyncFlow`, `AsyncParallelBatchNode`, or `AsyncParallelBatchFlow` in a graph-orchestration context.
- A Python LLM app with `prep -> exec -> post`, a shared dictionary, action strings, graph transitions, or `node - "action" >> other_node` syntax.
- Building lightweight agents, RAG, map-reduce, structured-output, streaming, FastAPI background jobs, voice/chat workflows, or coding-agent loops without a large framework.

## Minimal install and import check

```bash
pip install pocketflow
python - <<'PY'
from pocketflow import Node, Flow
class Start(Node):
    def prep(self, shared):
        shared["seen"] = True
start = Start()
Flow(start=start).run({})
print("pocketflow import ok")
PY
```

For development from source, an editable install is also valid. The public package version captured for this skill is `0.0.3`; see [repo provenance](references/repo-provenance.md) for the source snapshot.

## Route by task

| If the task is about... | Read |
| --- | --- |
| Public runtime classes, `prep/exec/post`, transitions, retries, fallback, nested flows, sync/async, batch/parallel behavior, or unit-test-like API debugging | [core-abstraction](sub-skills/core-abstraction/SKILL.md) |
| Designing an LLM app architecture, deciding between workflow/agent/RAG/map-reduce/structured-output/multi-agent patterns, or using cookbook-style recipes | [design-patterns](sub-skills/design-patterns/SKILL.md) |
| Implementing provider wrappers, search/embedding/vector/TTS/database utilities, graph visualization, logging/tracing, chunking, streaming, or external dependency safety | [utilities](sub-skills/utilities/SKILL.md) |
| Cross-cutting install/import/provider/config mistakes before choosing a sub-skill | [troubleshooting](references/troubleshooting.md) |
| Router placement, source snapshot, or staleness checks | [repo provenance](references/repo-provenance.md) and [routing metadata](references/repo-routing-metadata.json) |

## PocketFlow mental model

1. **A node has three optional phases.** `prep(shared)` reads and prepares data, `exec(prep_res)` performs compute and is the only phase retried, and `post(shared, prep_res, exec_res)` writes results and returns the next action.
2. **A flow follows action strings.** `a >> b` is the default transition. `a - "search" >> b` is a named transition. If `post()` returns `None`, PocketFlow looks for the default successor.
3. **The shared store is the durable data contract.** Most task state should be in a user-designed dictionary or persistence layer. Nodes communicate by reading/writing it.
4. **Params are per-run identifiers.** `BatchFlow.prep()` returns parameter dictionaries; child nodes read them from `self.params`. Do not use params as mutable shared state.
5. **PocketFlow is not an integration framework.** LLM calls, embeddings, vector search, DB queries, speech, UI, and observability are ordinary utility functions invoked by nodes.
6. **Start simple.** For a new LLM system, write a short design document first, then implement utilities, shared-store schema, nodes, and flows.

## Common safe checks

- Run [scripts/check_pocketflow_install.py](scripts/check_pocketflow_install.py) to confirm import, flow branching, fallback, batch, and async basics in the current Python environment.
- Run [sub-skills/core-abstraction/scripts/core_flow_smoke.py](sub-skills/core-abstraction/scripts/core_flow_smoke.py) when debugging runtime semantics.
- Use [sub-skills/design-patterns/scripts/design_pattern_templates.py](sub-skills/design-patterns/scripts/design_pattern_templates.py) to print safe skeletons for common application patterns.
- Use [sub-skills/utilities/scripts/pocketflow_utilities.py](sub-skills/utilities/scripts/pocketflow_utilities.py) for local chunking, Mermaid demo output, or environment-variable validation.

## Boundaries and caveats

- Do not claim PocketFlow automatically manages prompts, memory, tools, provider retries, callbacks, vector indexes, web servers, tracing, or credentials. Implement those explicitly as utilities and shared-store fields.
- Avoid writing giant `exec()` methods that read/write global state; put input selection in `prep()` and result persistence in `post()`.
- Do not run credentialed cookbook-style examples unless the user has provided required keys and approved network or service side effects.
- `AsyncParallelBatchNode` and `AsyncParallelBatchFlow` overlap independent async work; they are not CPU-parallel execution engines.
- If a task is primarily about maintaining this repository source code rather than using PocketFlow as a package, also apply normal Python repository maintenance practices.
