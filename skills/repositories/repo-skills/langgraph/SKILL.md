---
name: langgraph
description: "Build, run, persist, deploy, and operate LangGraph Python
  applications using the core runtime, prebuilt agents, checkpointing, CLI, and
  SDK clients."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangGraph

Use this skill when a task involves LangGraph, the low-level orchestration framework for building stateful agents and long-running workflows. It covers the Python monorepo packages `langgraph`, `langgraph-prebuilt`, `langgraph-checkpoint`, `langgraph-checkpoint-sqlite`, `langgraph-checkpoint-postgres`, `langgraph-cli`, and `langgraph-sdk`.

## Quick Start

Install the core package for most application work:

```bash
pip install -U langgraph
```

For focused packages or deployment tooling:

```bash
pip install -U langgraph-cli
pip install -U langgraph-sdk
pip install -U langgraph-checkpoint-sqlite
pip install -U langgraph-checkpoint-postgres "psycopg[binary]"
```

Minimal import and graph smoke check:

```python
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    value: int

def inc(state: State) -> State:
    return {"value": state["value"] + 1}

builder = StateGraph(State)
builder.add_node("inc", inc)
builder.add_edge(START, "inc")
builder.add_edge("inc", END)
app = builder.compile()
assert app.invoke({"value": 1})["value"] == 2
```

## Route by Task

- **Custom graphs and runtime behavior**: Use `sub-skills/graph-runtime/SKILL.md` for `StateGraph`, reducers, node signatures, conditional edges, `Command`, `Send`, interrupts, streaming, subgraphs, low-level `Pregel`, and runtime debugging.
- **Prebuilt agents and tools**: Use `sub-skills/prebuilt-agents/SKILL.md` for `create_react_agent`, `ToolNode`, `ValidationNode`, injected state/store/runtime, tool-call errors, structured responses, and human interrupt payloads.
- **Persistence and memory**: Use `sub-skills/persistence/SKILL.md` for checkpointers, `thread_id`, checkpoint resume, SQLite, Postgres, in-memory savers, `InMemoryStore`, semantic search, and serde hardening.
- **CLI and deployment**: Use `sub-skills/cli-deployment/SKILL.md` for `langgraph new`, `dev`, `up`, `build`, `dockerfile`, `validate`, `langgraph.json`, Docker/server configuration, and local deployment troubleshooting.
- **SDK clients and streaming**: Use `sub-skills/sdk-clients/SKILL.md` for Python async/sync SDK clients, assistants, threads, runs, cron, store APIs, v3 thread-centric streaming, auth headers, and JS SDK relocation status.

## Shared References and Scripts

- Read `references/repo-provenance.md` when deciding whether this skill matches a checkout or should be refreshed.
- Read `references/package-map.md` to map user requests to the monorepo packages, install commands, import modules, and common optional dependencies.
- Read `references/troubleshooting.md` for cross-cutting install, import, config, service, security, and version-mismatch failures before drilling into a sub-skill’s troubleshooting file.
- Run `scripts/run_core_smokes.py --help` or selected smoke checks when validating a LangGraph environment without relying on the original repository checkout.

## Common Decisions

- Choose `StateGraph` when a task needs custom state schemas, deterministic routing, reducers, subgraphs, or precise interrupt/resume control.
- Choose prebuilt agent APIs when the task is primarily a tool-calling chat agent and does not need a fully custom graph loop.
- Use an in-memory checkpointer only for tests, local demos, or debugging; use SQLite for lightweight local persistence and Postgres for durable multi-process or production persistence.
- Use `langgraph dev` for local hot-reload development, `langgraph up` for a local Docker API server, `langgraph build` for an image, and `langgraph dockerfile` when a user needs to review or customize the generated container recipe.
- Use the SDK only when there is a running LangGraph API server or deployment; local graph construction/invocation does not require `langgraph-sdk`.

## Verification Checklist

1. Confirm package imports with the relevant sub-skill smoke script.
2. Compile a minimal graph before adding persistence, tools, or deployment configuration.
3. If persistence is involved, invoke with `config={"configurable": {"thread_id": "..."}}` and verify resume/list behavior.
4. If serving with the CLI, validate `langgraph.json` before running `dev`, `up`, or `build`.
5. If using the SDK, verify URL/auth selection and streaming mode against the server being targeted.

## Safety and Scope

This skill is self-contained. Do not require the original LangGraph repository checkout for runtime use. The bundled references and scripts distill repo evidence into reusable guidance; original tests and examples remain verification evidence, not runtime dependencies.
