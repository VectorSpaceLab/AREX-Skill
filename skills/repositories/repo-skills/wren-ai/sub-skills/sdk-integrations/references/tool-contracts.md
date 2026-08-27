# Toolkit Contracts and Project State

## Shared constructor

Both framework packages expose:

```python
WrenToolkit.from_project(path, *, profile=None)
```

The constructor requires the project root, `wren_project.yml`, and
`target/mdl.json`. It loads a project `.env` without overriding values the host
already exported, then resolves the requested/bound/active profile.

## Direct API

Both toolkits provide synchronous direct methods:

```python
toolkit.query(sql, limit=None)     # PyArrow table
toolkit.dry_plan(sql)              # target-dialect SQL
toolkit.dry_run(sql)               # None or error
toolkit.memory.fetch(question)
toolkit.memory.recall(question)
toolkit.memory.store(nl=..., sql=..., tags=[...])
```

Direct queries have no LLM-tool row cap; callers own their own resource policy.

## Memory auto-detection

The framework tool surfaces are based on whether the project has usable memory
state. When memory is absent, only runtime query/planning/model tools are
registered. Enabling semantic memory is a project operation; it is not a
constructor override.

## Profile caveat

A named profile can appear to be a no-op when two profiles use the same
placeholder names and the project `.env` supplies those values. The selection
still matters when profiles use different placeholders, hardcoded values, or
separate datasources. Keep one explicit profile per project when possible.

## Prompt/tool synchronization

Always generate the framework prompt/instructions from the same configured tool
collection passed to the agent. If storage is disabled, a stale default prompt
can tell an agent to invoke an unavailable memory-write tool.
