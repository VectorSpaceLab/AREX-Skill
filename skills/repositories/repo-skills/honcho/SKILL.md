---
name: honcho
description: "Router for Honcho self-hosting, integrations, CLI usage, and
  maintenance workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Honcho

Honcho is a peer/session/message memory system with a FastAPI API, a background
worker for memory formation and consolidation, Python and TypeScript SDKs, and
a terminal CLI.

Use this repo skill when a user asks about Honcho configuration, startup,
client integration, memory-model behavior, CLI inspection, repository testing,
or release maintenance.

## Start here

- Use `sub-skills/self-hosting/` when the task is about running the API,
deriver worker, database, Redis, embeddings, keys, or startup validation.
- Use `sub-skills/integrations/` when the task is about the Python SDK,
TypeScript SDK, REST routes, memory reads/writes, session context, chat, or
webhooks.
- Use `sub-skills/cli-operations/` when the task is about the `honcho` CLI,
`honcho init`, `honcho doctor`, config files, or command output.
- Use `sub-skills/maintenance/` when the task is about tests, type checks,
versioning, release hygiene, or repo scripts.

If you need a quick surface summary, run `scripts/surface_report.py` from a
Honcho checkout.

## Core mental model

Honcho centers on four public concepts:

- **Workspace**: the top-level tenancy boundary.
- **Peer**: any participant, human or AI.
- **Session**: a conversation thread shared by one or more peers.
- **Message / conclusion**: the raw turns and the derived observations that
  feed peer representations.

The API server handles requests and queues work; the deriver and dreamer run in
the background. Reads such as `session.context()` and `peer.representation()`
are cheap. Live reasoning through `peer.chat()` is slower and should be used
when a plain read is not enough.

## Reference map

Read these files when you need the fuller details:

- `references/core-model.md` — workspace/peer/session/message/conclusion model
  and the server/worker split.
- `references/configuration-and-environment.md` — config precedence, env vars,
  database and vector-store settings, and runtime defaults.
- `references/api-route-map.md` — grouped `/v3` route families and what each
  one is for.
- `references/cli-reference.md` — `honcho` command groups, config file
  behavior, scope flags, JSON output, and exit-code expectations.
- `references/development-and-testing.md` — tests, type checks, SDK checks,
  and release-adjacent maintenance commands.
- `references/troubleshooting.md` — common startup, auth, config, scope, and
  backend failures.
- `references/repo-provenance.md` — source revision and evidence trail.
- `references/repo-routing-metadata.json` — managed router metadata for
  downstream import.

## Routing guide

| If the user asks about… | Go to |
| --- | --- |
| Local API startup, DB/Redis, embeddings, keys, or queue health | `sub-skills/self-hosting/` |
| Python SDK, TypeScript SDK, REST routes, memory reads/writes, or webhooks | `sub-skills/integrations/` |
| `honcho` CLI commands, `init`, `doctor`, config, or JSON output | `sub-skills/cli-operations/` |
| Tests, scripts, type checking, versioning, or release maintenance | `sub-skills/maintenance/` |

## Good defaults

- Prefer the narrowest sub-skill that owns the workflow.
- Use the references before guessing at command flags or route names.
- Keep examples and command snippets inside this skill tree.
- Treat live reasoning, external providers, and remote vector stores as
  optional runtime surfaces unless the request explicitly needs them.

## Common signals

- `honcho doctor` is the fastest CLI health check.
- `honcho peer inspect` and `honcho session context` are the quickest memory
  inspection commands.
- `uv run pytest tests/` is the broad Python test command, but maintenance
  tasks should usually start with a smaller targeted subset.
- `uv run pytest tests/ -k typescript` is the supported TypeScript SDK test
  path from the monorepo root.
- `cd sdks/typescript && bun run tsc --noEmit` is the direct TypeScript SDK
  type-check command.

## Troubleshooting shortcuts

- If startup fails, check DB connectivity, embedding dimensions, and vector
  store configuration first.
- If CLI output looks human-readable when you expected JSON, add `--json` or
  pipe the command.
- If SDK or REST calls fail with scope errors, confirm the workspace, peer,
  and session IDs match the request.
- If tests fail in a live provider suite, confirm credentials and model env
  vars before changing code.

## Self-containment

This skill is intended to stand on its own. Runtime links stay inside this
skill tree, and bundled references/scripts capture the practical details a
future agent needs without reopening the source repository.
