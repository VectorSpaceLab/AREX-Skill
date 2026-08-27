---
name: strands-agents
description: "Route Strands Agents monorepo work across the Python SDK,
  TypeScript SDK, docs site, MCP server, cross-SDK parity, testing,
  troubleshooting, and contribution workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Strands Agents

Use this repo skill for tasks about the Strands Agents monorepo, the
`strands-agents` Python package, the `@strands-agents/sdk` TypeScript package,
the Astro/Starlight documentation site, or the `strands-agents-mcp-server`
package.

## Read first

1. Read [repo-overview.md](references/repo-overview.md) to confirm repository layout, selected scope, and excluded infrastructure.
2. Read [cross-sdk-parity-and-contribution.md](references/cross-sdk-parity-and-contribution.md) before changing public APIs, hook events, docs, tests, or contribution-facing behavior.
3. Read [troubleshooting.md](references/troubleshooting.md) when install, dependency, credential, browser, network, AWS-infra, or staleness problems appear.
4. Check [repo-provenance.md](references/repo-provenance.md) when deciding whether this skill should be refreshed against a newer checkout.
5. Use [repo-routing-metadata.json](references/repo-routing-metadata.json) only as structured router metadata for managed repo-skill import flows.

## Public install clues

- Python users normally install `strands-agents` with any task-required optional extras and may also install `strands-agents-tools` for community tools.
- TypeScript users install `@strands-agents/sdk` with Node.js 20+.
- MCP server users can launch `strands-agents-mcp-server` through a Python package install or `uvx`.
- In a checkout, use the package-specific sub-skill before installing broad dev dependencies or all optional extras.

## Route by task

| Task signals | Go to |
| --- | --- |
| Python `Agent`, `@tool`, model providers, MCP client, memory, sessions, hooks, interventions, plugins, sandbox, telemetry, graph/swarm/A2A, Python tests | [python-sdk](sub-skills/python-sdk/SKILL.md) |
| TypeScript `Agent`, Zod/JSON tools, model providers, MCP tools/client, middleware, hooks, interventions, memory, sessions, storage, sandbox, telemetry, graph/swarm, examples, package exports | [typescript-sdk](sub-skills/typescript-sdk/SKILL.md) |
| Astro/Starlight docs pages, MDX, snippets, `<Syntax>`, tabs, `sourceLinks`, navigation, generated API docs, docs review/audit/planning | [docs-site](sub-skills/docs-site/SKILL.md) |
| `strands-agents-mcp-server`, `search_docs`, `fetch_doc`, docs catalog indexing, cache hydration, section extraction, URL restrictions, MCP server tests | [mcp-server](sub-skills/mcp-server/SKILL.md) |
| Cross-SDK naming, literal parity, hook event parity, public/internal API, comments, logging, feature lifecycle, PR readiness | [cross-sdk-parity-and-contribution.md](references/cross-sdk-parity-and-contribution.md) plus the relevant SDK sub-skill |

## Fast checks

- Use [python-import-smoke.sh](scripts/python-import-smoke.sh) when Python packages are installed and you need import/signature sanity for both Python packages.
- Use [ts-check.sh](scripts/ts-check.sh) for root TypeScript workspace checks when npm dependencies are installed.
- Use [site-check.sh](scripts/site-check.sh) for docs-site checks when site npm dependencies are installed.
- Sub-skills provide narrower helpers for Python SDK, TypeScript SDK, docs-site, and MCP server checks.

## Operating rules

- Work in the smallest relevant package and test slice first; do not run broad provider, browser, network, or AWS-infrastructure checks unless the task selects them.
- Keep Python and TypeScript concepts in parity by meaning, not identical code. Identifiers match after language recasing; string literal casing follows the cross-SDK rules.
- Public exports require deliberate API review. Python public surfaces use `__all__`; TypeScript public surfaces use package/barrel exports.
- Do not call SDK tools "skills" in SDK-facing docs. Reserve "skills" for agent skill files.
- When source files move, update docs `sourceLinks` in the same change.
- Treat `test-infra/` as opt-in real AWS infrastructure. Do not deploy it or set internal flags unless the task explicitly targets that stack.
- Record any skipped credential, network, browser, Docker, AWS, or live-provider checks in the final handoff instead of implying they passed.

## Scope boundaries

This skill is intentionally a reusable monorepo operating guide, not a release or CI automation manual. It covers package development, docs authoring, source-backed troubleshooting, and safe verification selection. Release automation, GitHub workflow internals, account-specific infrastructure, generated build output, caches, and one-off migration scripts are out of default scope unless a future task explicitly selects them.
