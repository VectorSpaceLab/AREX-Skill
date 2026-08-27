# Maintainer Workflows

This reference is for agents changing the `openai-agents` source repository rather than building applications with the SDK.

## Repository Orientation

| Area | Role | Development notes |
| --- | --- | --- |
| `src/agents/` | Library source for the `agents` import package. | Runtime changes here trigger the full repo verification policy. Keep public API compatibility in mind before editing exported dataclasses or constructors. |
| `src/agents/run.py` | Public runtime entrypoint for `Runner` / `AgentRunner`. | Keep this file focused on orchestration and public flow control. Move new internal runtime logic to `run_internal/` modules. |
| `src/agents/run_internal/` | Internal run loop, turn resolution, tool execution/planning, item normalization, session persistence, and helpers. | Keep streaming and non-streaming paths behaviorally aligned. Coordinate new item/tool/output types across all affected modules. |
| `src/agents/run_state.py` | Durable pause/resume serialization boundary. | Serialized shape changes require schema version and summary updates plus round-trip and legacy-read tests. |
| `tests/` | Unit, integration-style, snapshot, compatibility, sandbox, model, realtime, MCP, and memory tests. | Prefer focused tests near the changed behavior, then run broader gates before handoff. |
| `docs/` | MkDocs source and API reference pages. | English source docs are edited directly; generated translations are not normal edit targets. |
| `docs/scripts/` | Documentation automation. | `generate_ref_files.py` is safe reference-generation tooling. Translation automation is maintainer/service-oriented and not bundled as a runtime helper. |
| `Makefile` | Canonical local commands. | Use `uv run` through make targets to stay in the repository environment. |
| `pyproject.toml` | Package metadata, dependencies, optional extras, Ruff, mypy, pytest, coverage, and inline snapshot settings. | Changes here affect build/test behavior and trigger full verification. |

The package distribution is `openai-agents` and imports as `agents`. It exposes no console-script entry points, so repository maintenance workflows should use `make`, `uv run`, and Python module imports rather than expecting an installed CLI.

## Policy Skills Required by Repo Rules

Repository policy names three mandatory meta steps. Treat these as required workflow gates when the task matches the trigger:

| Gate | Trigger | Expected outcome |
| --- | --- | --- |
| `$implementation-strategy` | Before runtime code, exported APIs, external config, persisted schemas, wire protocols, or user-facing behavior changes. | Decide compatibility boundary against the latest release tag, identify durable state/API risk, and pick a direct replacement, compatibility shim, or migration strategy. |
| `$code-change-verification` | Before marking runtime code, tests, examples, build/test config, or behavior-impacting docs changes complete. | Run or account for `make format`, `make lint`, `make typecheck`, and `make tests` in order. |
| `$pr-draft-summary` | Before final handoff for eligible code/test/example/build-config or behavior-impacting docs changes. | Produce summary, test plan, branch suggestion, title, and draft PR description without committing or opening a PR. |

For docs-only or repo-meta changes, the full verification stack can be skipped unless docs affect SDK behavior or the user asks for full verification.

## Planning and ExecPlans

Use an ExecPlan for multi-step or multi-file work, new features, refactors, or work likely to take more than about an hour. The plan must be self-contained, outcome-focused, and maintained as a living document with progress, discoveries, decisions, and retrospective notes.

Compatibility risk belongs in the plan only when the change affects behavior shipped in the latest release tag or a released / explicitly supported durable external state boundary. Do not assume branch-local unreleased churn needs compatibility shims.

## Runtime Code Ownership

`run.py` should stay a thin public orchestration layer. When new runtime logic grows beyond wiring, place it under `run_internal/` and import it into the public entrypoint.

When changing run-loop behavior, inspect both streaming and non-streaming paths:

- `run_single_turn` and `run_single_turn_streamed` should preserve equivalent semantics unless the difference is deliberate and tested.
- `get_new_response` and `start_streaming` should be checked together when model-call payloads, retries, tracing, or streaming events change.
- New streaming item types require updates to stream event definitions as well as item conversion and persistence code.

When adding a new tool, output, approval, or run item type, coordinate at least these surfaces:

| Surface | Why it matters |
| --- | --- |
| `items.py` | Public and internal run item types and conversions. |
| `run_internal/run_steps.py` | Processed response and tool-run structs. |
| `run_internal/turn_resolution.py` | Model output processing and run item extraction. |
| `run_internal/tool_execution.py` and `tool_planning.py` | Execution, approval, and planning behavior. |
| `run_internal/items.py` | Normalization, dedupe, and approval filtering. |
| `stream_events.py` | Stream event names and semantic event surface. |
| `run_state.py` | Serialization and deserialization of paused/resumed state. |
| `run_internal/session_persistence.py` | Session save and rewind behavior. |

## RunState Schema Workflow

`RunState` is a durable pause/resume boundary. Its schema policy is:

1. Released schema versions remain readable.
2. Unreleased schema versions may be renumbered or squashed before release when intermediate snapshots are intentionally unsupported.
3. `to_json()` emits the current schema version.
4. Forward compatibility is fail-fast; older SDKs reject newer or unsupported versions.

When serialized shape changes:

- Update `CURRENT_SCHEMA_VERSION`.
- Add a concise chronological entry to `SCHEMA_VERSION_SUMMARIES`.
- Keep every supported summary non-empty.
- Add focused tests that prove new snapshots round-trip through `RunState.from_json`.
- Add or update legacy-read tests when older supported payloads need defaulting or migration.
- Check nested run state, sandbox resume state, approval items, tool outputs, context serialization metadata, and server-managed conversation identifiers when relevant.

## Public API Compatibility Workflow

Public constructors and dataclass field order are compatibility-sensitive. Examples include `RunConfig`, `FunctionTool`, `AgentHookContext`, result/context classes, and sandbox option models.

Safe pattern for adding optional public fields:

1. Prefer keyword-only usage at call sites, but do not rely on call sites to justify breaking positional callers.
2. Append new optional fields after existing public fields whenever possible.
3. If insertion is unavoidable, add a compatibility layer that preserves old positional meanings.
4. Add regression tests exercising the old positional call pattern.
5. Re-run focused compatibility tests before the full verification stack.

The repository has dedicated positional-compatibility tests. Use them as patterns when adding fields or preserving old constructor call shapes.

## Docs Workflow

Docs are published to the live site, so align docs with SDK behavior and release timing.

- Edit source English docs and API reference stubs, not generated translated docs.
- Treat runnable docs snippets as API compatibility checks; verify signatures and argument names against source before documenting them.
- For OpenAI platform or SDK-specific docs changes, repository policy requires authoritative OpenAI docs consultation via the configured platform-docs mechanism, plus local source inspection.
- `make build-docs` runs reference generation and MkDocs build.
- `make build-full-docs` runs translation automation and MkDocs build; this is maintainer/service-oriented and usually broader than needed for normal docs edits.

## Source Script Inventory Decisions

The generated sub-skill bundles only a safe local helper that suggests validation commands. Source scripts are intentionally handled as evidence rather than runtime dependencies:

| Source script | Runtime skill decision | Reason |
| --- | --- | --- |
| `docs/scripts/generate_ref_files.py` | Reference-only. | Safe and useful for understanding `make build-docs`, but future agents should use the repo's Makefile rather than a copied stale script. |
| `docs/scripts/translate_docs.py` | Excluded from bundled helpers. | Translation automation depends on service credentials and generated language content; it is maintainer/service-oriented. |
| `.github/scripts/run-asyncio-teardown-stability.sh` | Reference-only. | Useful for CI context and optional stability checks, but not a general local helper. |
| `.github/scripts/detect-changes.sh` and release scripts | Excluded from bundled helpers. | CI/release automation is maintainer-only and may have repository/service assumptions. |

## PR Handoff Expectations

The PR template asks for:

- A short summary of the change and problem solved.
- A test plan.
- An issue number when applicable.
- Checklist status for tests, docs, lint/format, and passing tests.

For eligible changes, repository policy requires a PR draft summary before the final response. This is a local handoff artifact: do not create a branch, commit, push, or open a PR unless the user explicitly asks.
