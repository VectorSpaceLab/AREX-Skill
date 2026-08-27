---
name: typescript-sdk
description: "Guide work on the Strands TypeScript SDK (@strands-agents/sdk),
  including agents, tools, providers, MCP, hooks, middleware, interventions,
  plugins, memory, sessions, storage, sandboxing, telemetry, multi-agent
  orchestration, examples, packaging, and workspace commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TypeScript SDK

Use this sub-skill when the task touches the Strands TypeScript SDK or the
`@strands-agents/sdk` package in a Strands Agents checkout.

## Start here

1. Read [overview.md](references/overview.md) for scope, boundaries, package shape, and the Node/browser split.
2. Read [api-reference.md](references/api-reference.md) for public exports, classes, config interfaces, and naming differences from Python.
3. Read [workflows.md](references/workflows.md) for implementation playbooks and command selection.
4. Read [testing-and-maintenance.md](references/testing-and-maintenance.md) before validating, packaging, or refreshing dependencies.
5. Read [troubleshooting.md](references/troubleshooting.md) when a check, example, provider, or browser flow fails.
6. Use [ts-core-check.sh](scripts/ts-core-check.sh) for focused workspace checks and [workspace-cli.sh](scripts/workspace-cli.sh) for common `strandly`-style workflows.

## Use this sub-skill for

- `Agent`, `AgentConfig`, invoke/stream, snapshots, checkpoints, interrupts, and result handling.
- Zod and JSON-schema tools, tool executors, direct tool calls, and MCP tools.
- Model provider classes, config interfaces, streaming events, token counting, and provider error translation.
- Hooks, middleware, interventions, plugins, retry strategy, context management, memory, session, storage, sandbox, and telemetry.
- Multi-agent `Graph`, `Swarm`, nodes, edges, state, hooks, and snapshot/resume behavior.
- `strands-ts` examples, package exports, workspace scripts, browser bundle checks, and package tarball checks.

## Route elsewhere

- Python SDK implementation or Python-specific API parity: use [python-sdk](../python-sdk/SKILL.md).
- Docs-site MDX, snippets, `sourceLinks`, or generated API docs: use [docs-site](../docs-site/SKILL.md).
- The docs-search MCP server package: use [mcp-server](../mcp-server/SKILL.md).
- AWS-provisioned infrastructure checks are out of default scope unless the task explicitly selects them.

## Operating rules

- Preserve cross-SDK parity: identifiers match with language idiom, single-word literals match exactly, multi-word literals use TS camelCase and Python snake_case through explicit maps.
- Use named exports only; public surface changes must update the correct barrel and `package.json` export entry when needed.
- Keep internal exports out of the root barrel and mark intentionally internal symbols with `@internal` when they cross files.
- Class and interface signatures require explicit return types, object shapes prefer `interface`, and source/test filenames use kebab-case.
- Treat Node-only and browser-safe code as separate surfaces; run browser bundle checks before claiming browser safety.
- Keep provider credentials, Playwright/browser setup, Docker telemetry, and live integrations as explicit optional checks.

## Fast path

1. Identify whether the task is runtime API, provider/model, tools/MCP, multi-agent, browser, example, package/dependency, or test-only.
2. Read the closest reference and check the public export surface before editing.
3. Use the smallest relevant test slice first; escalate to package, browser, or integration checks only when the task requires it.
4. If a behavior has a Python counterpart, compare the sibling route and the root cross-SDK guidance before changing names or hook events.
5. Record any skipped Node, browser, provider, or Docker checks in the final handoff rather than implying they passed.
