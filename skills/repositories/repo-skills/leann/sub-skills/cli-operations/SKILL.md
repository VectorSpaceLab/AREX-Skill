---
name: cli-operations
description: "Operate LEANN safely through its CLI: build, search, ask, watch,
  rebuild, migrate, manage daemons and registries, route source indexers, and
  plan commands without execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN CLI Operations

Use this sub-skill when the task is expressed as a `leann` command or involves
CLI index resolution, idempotent builds, watch/rebuild recovery, passage-ID
migration, embedding daemons, local/global index discovery, removal, or one of
the seven personal-data indexers.

## Route by task

- Look up all 19 groups, exact flags, defaults, positional queries, prompt and
  metadata-filter syntax, and the deliberate absence of grep/hybrid flags in
  [CLI reference](references/cli-reference.md).
- Plan build/update/rebuild, back up before mutation, migrate IDs, resolve
  duplicate names, or remove an index with
  [index lifecycle operations](references/index-lifecycle-operations.md).
- Manage daemon TTL/ports, recover stale processes, understand watch scope and
  project registration, or preflight source indexers with
  [daemon, watch, registry, and indexers](references/daemon-watch-and-registry.md).
- Diagnose parser errors, bad filter JSON, missing sources/indexes, ambiguity,
  unsafe mutation assumptions, stale daemons, watch surprises, and platform
  prerequisites with [troubleshooting](references/troubleshooting.md).
- Construct a shell-quoted command without running LEANN using the bundled
  [command planner](scripts/build_leann_command.py).

## Operating rules

1. Run from the project that owns the index. CLI indexes live under that
   project's `.leann/indexes/`; the same name can exist in registered projects.
2. Use `leann list` before mutation. Stop the index daemon and copy the complete
   index directory before `migrate-ids`, risky rebuild work, or irreplaceable
   removal.
3. Prefer idempotent `build`/`rebuild`. Use `--force` only for an intentional
   full replacement; do not use deletion as recovery.
4. Start migration with `--dry-run`. Content-hash collisions deduplicate
   identical passage text, and the operation has no built-in backup.
5. In automation use unique names and `search --non-interactive`; duplicate
   resolution differs across search, ask, react, watch, and mutation commands.
6. Treat the query as positional for `search` and `react`; it is optional and
   positional for `ask`. Quote queries, prompt templates, and JSON filters.
7. Use only parser-backed flags. The CLI has metadata filtering but no
   grep/hybrid switches; route those retrieval modes to the Python API.
8. Keep one watch loop per index. Dry-run watch does not advance the checkpoint;
   a successful rebuild does.
9. Never place credentials in generated command text. A remote embedding key
   resolved during `build` can be persisted in index metadata; treat those
   artifacts as sensitive and follow the provider sub-skill's guidance.

## Boundaries

- For Python builders/searchers, metadata schemas, BM25, hybrid, and grep, use
  [API and indexing](../api-and-indexing/SKILL.md).
- For backend choice, compact/recompute storage, and tuning, use
  [backends and storage](../backends-and-storage/SKILL.md).
- For embedding/LLM providers, model behavior, credentials, and chat semantics,
  use [embeddings and chat](../embeddings-and-chat/SKILL.md).
- For reader internals, chunking, and extraction workflows, use
  [RAG applications](../rag-applications/SKILL.md).
- For HTTP endpoints, MCP, and service deployment, use
  [MCP and services](../mcp-and-services/SKILL.md).
