---
name: python-sdk
description: "Guide work on the Strands Python SDK: agent loop, tools, models,
  MCP, memory, sessions, hooks, interventions, plugins, sandbox, telemetry,
  multi-agent graphs, snapshots, checkpoints, and Python tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python SDK

Use this sub-skill for Strands Python SDK work in the `strands-agents` package
and its Python source tree.

## Start here

1. Read [overview.md](references/overview.md) to confirm scope, package identity, and exclusions.
2. Read [api-reference.md](references/api-reference.md) for verified signatures, exports, extras, and provider surfaces.
3. Read [workflows.md](references/workflows.md) for the smallest safe path for the task.
4. Read [testing-and-maintenance.md](references/testing-and-maintenance.md) before changing code or tests.
5. Read [troubleshooting.md](references/troubleshooting.md) when the task is about recovery or diagnosis.
6. Run [python-core-check.sh](scripts/python-core-check.sh) for import and signature sanity; add `--pytest` only in a Strands Agents checkout with test dependencies installed.

## Use this sub-skill for

- `Agent`, invocation, event loop, concurrency, limits, structured output, checkpoints, snapshots, and direct tool calls.
- `@tool`, tool schemas, `ToolContext`, tool loading, tool providers, executors, and MCP client integration.
- Model providers, model config validation, streaming, token counting, context-window behavior, and provider error translation.
- Conversation managers, context manager strategies, memory manager, sessions, storage, hooks, interventions, plugins, sandbox, and telemetry.
- Multi-agent graph, swarm, A2A, shared result/state objects, and multi-agent hook/plugin behavior.
- Python unit tests, focused integration-test selection, package extras, and Python-specific coding conventions.

## Route elsewhere

- TypeScript SDK implementation or Node/browser package checks: use [typescript-sdk](../typescript-sdk/SKILL.md).
- Docs-site authoring, snippets, `sourceLinks`, generated API docs, or navigation: use [docs-site](../docs-site/SKILL.md).
- The docs-search MCP server package and its `search_docs` / `fetch_doc` tools: use [mcp-server](../mcp-server/SKILL.md).
- AWS test-infra or live provider credentials: treat as optional and credential-bound unless explicitly requested.

## Operating rules

- Prefer verified signatures and package metadata from the bundled references over memory.
- Public package surfaces should be declared through `__all__`; heavy optional providers should remain lazy-loaded.
- Use precise types, `X | None` optionals, coded `# type: ignore[code]`, Google-style docstrings, and specific exceptions.
- Provider boundaries translate vendor context-window and throttling errors to typed SDK exceptions and chain the original cause.
- Hook events use shared names and before/after ordering; compare sibling TypeScript behavior before changing cross-SDK event names.
- Keep provider credentials, network services, AWS resources, and optional backend extras explicit in the verification handoff.

## Fast path

1. Identify the owning subsystem and read the closest reference section.
2. Inspect the target file and smallest behavior test for line-level confirmation; do not widen to unrelated provider or integration surfaces.
3. Run the import/signature smoke helper first, then the smallest relevant pytest slice.
4. If a task changes public API, check docs and TypeScript parity before final handoff.
5. Record skipped provider, credential, network, or AWS-backed checks instead of implying broad integration coverage.
