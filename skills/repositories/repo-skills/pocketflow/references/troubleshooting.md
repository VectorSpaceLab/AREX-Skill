# PocketFlow troubleshooting

Use this page for cross-cutting install, import, and workflow-selection issues before diving into a sub-skill.

## Install and import

### `ModuleNotFoundError: pocketflow`
- Install the package with `pip install pocketflow` or use an editable install from a PocketFlow checkout during development.
- Confirm the active Python is the intended one before diagnosing framework errors.
- If import succeeds in one interpreter but not another, the problem is usually environment selection rather than PocketFlow itself.

### Editable install succeeds but behavior looks stale
- Re-run the import check and confirm the package version.
- If you are using a source checkout, remember that a later checkout change can make this skill stale; compare the current package behavior with the provenance file.

### Accidental use of a different framework
- PocketFlow is a tiny graph runtime, not a full agent SDK or provider wrapper.
- If a task expects built-in tools, tracing, memory, vector search, or web automation, implement those as user utilities and read the relevant sub-skill.

## Core workflow selection mistakes

### The task is about node/flow semantics
Read `sub-skills/core-abstraction/SKILL.md` when you need to understand:
- `prep -> exec -> post`
- `>>` and `- "action" >>`
- retries and fallback
- `BatchNode` vs `BatchFlow`
- async and parallel async orchestration

### The task is about app design or recipes
Read `sub-skills/design-patterns/SKILL.md` when you need:
- workflow decomposition
- agents, RAG, map-reduce, structured output
- multi-agent queues
- service/background job patterns
- PocketFlow cookbook-style app scaffolding

### The task is about utilities or integrations
Read `sub-skills/utilities/SKILL.md` when you need:
- LLM/search/embedding/vector/TTS wrappers
- visualization/debugging/tracing
- env var handling for provider credentials
- safe local smoke helpers for utilities

## Provenance and staleness

### The skill appears out of date
- Compare the runtime package version and public API to `references/repo-provenance.md`.
- If class names, constructor defaults, or async/batch semantics have changed, refresh the skill instead of extending it blindly.

### A cookbook example requires credentials or a service
- Treat it as design evidence unless the user explicitly asked to run the service.
- Do not invent provider keys or local endpoints.
- Keep those dependencies in the design-pattern or utilities sub-skill troubleshooting pages.

## Flow debugging quick checks

1. Confirm the node is actually in the flow and returns the action you expect.
2. Confirm the transition is wired with the same action string.
3. Confirm the node is not being executed with `node.run()` when you expected `flow.run()`.
4. Confirm `BatchFlow` params are set on the flow, not the shared store.
5. Confirm async code is called with `run_async()` and not the sync API.
6. Confirm retry/fallback logic is idempotent and that `exec()` does not mutate `shared` directly.

## When to stop and re-scope

- If a requested workflow needs unavailable hardware, external credentials, or a service that the user has not approved, keep that limitation explicit.
- If the task is not PocketFlow-specific, use another repo skill or a general maintenance workflow instead of forcing this one.
