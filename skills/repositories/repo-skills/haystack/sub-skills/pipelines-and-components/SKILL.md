---
name: pipelines-and-components
description: "Build, connect, run, serialize, debug, and extend Haystack
  Pipeline, AsyncPipeline, SuperComponent, and custom @component workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pipelines and Components

Use this sub-skill when the task is about Haystack orchestration rather than a specific model, retriever, agent, or repository-maintenance command.

## Route Here

- Create or modify `Pipeline` and `AsyncPipeline` graphs with `add_component()`, `connect()`, `run()`, `run_async()`, and `run_async_generator()`.
- Write custom `@component` classes, define input and output sockets, validate socket names/types, or debug component contract errors.
- Configure loop safety with `max_runs_per_component`, inspect intermediate outputs with `include_outputs_from`, and diagnose blocked or over-running graphs.
- Serialize or load pipelines with `to_dict()`, `from_dict()`, `dumps()`, `loads()`, `dump()`, and `load()`.
- Use pipeline breakpoints, snapshots, drawing, or `SuperComponent` wrappers.

## Reroute

- Model/provider components, credentials, generation-specific parameters, and embedding/generator selection: `../generation-and-model-components/SKILL.md`.
- RAG retrieval strategy, document stores, rankers, and retriever wiring choices: `../retrieval-and-rag/SKILL.md`.
- Agent loops, tool invocation, and human-in-the-loop workflows: route to the `agents-tools-and-hitl` sibling when present.
- Hatch, tests, release notes, or maintainer commands for this repository: route to the `repo-development` sibling when present.

## Core References

- Start with `references/api-reference.md` for concrete constructor signatures, component contracts, connection rules, and serialization APIs.
- Use `references/workflows.md` for build/debug/async/loop/super-component recipes.
- Use `references/troubleshooting.md` when imports, optional integrations, sockets, serialization, snapshots, or runtime execution fail.
- Run `scripts/pipeline_smoke_check.py` in any environment with `haystack-ai` installed to verify the public APIs this sub-skill relies on.

## Fast Pattern

```python
from haystack import Pipeline, component

@component
class Uppercase:
    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": text.upper()}

pipe = Pipeline(max_runs_per_component=5)
pipe.add_component("upper", Uppercase())
result = pipe.run({"upper": {"text": "haystack"}})
assert result["upper"]["text"] == "HAYSTACK"
```
