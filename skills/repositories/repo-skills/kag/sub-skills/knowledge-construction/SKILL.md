---
name: knowledge-construction
description: "Routes KAG project setup, schema commit, builder-chain, and
  index-selection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Knowledge Construction

Use this sub-skill when the user wants to prepare or inspect a KAG project before query-time use.

## Triggers

Common requests include:

- create or restore a project from `kag_config.yaml`
- commit a schema to the project server
- choose builder chains, readers, splitters, extractors, vectorizers, or writers
- inspect or compare index managers
- validate that a project layout is safe before building
- debug checkpointed builder runs or layout mismatches

## Start here

1. Read `references/workflows.md` for the command sequence and builder lifecycle.
2. Run `scripts/validate_project_layout.py` before any live build or schema mutation.
3. Read `references/data-and-configuration.md` for builder config keys, index choices, and file-layout assumptions.
4. Read `references/troubleshooting.md` when a namespace, schema filename, config key, or writer mode looks wrong.

## What belongs here

This sub-skill owns the tasks that turn source data into a KAG project and knowledge graph:

- `knext project create|restore|update|list`
- `knext schema commit`
- `knext schema reg_concept_rule`
- builder chain selection and local preflight checks
- index-manager choice for chunk, summary, table, outline, atomic-query, or hybrid retrieval
- domain-knowledge injection and other build-time graph preparation

## What does not belong here

- Query-time answering or trace diagnosis goes to `question-answering`.
- MCP server launch, distributed job submission, or benchmark planning goes to `mcp-and-automation`.
- Generic install/import issues go to the root troubleshooting files.

## Working rule

Prefer a safe local check first. If the layout or config is obviously wrong, fix the local project structure or report the mismatch before touching any server-mutating command.

## Common decisions

- If the namespace and schema filename disagree, stop before `knext schema commit`.
- If a custom builder component is mentioned, make sure its module is imported before registry construction.
- If a writer is destructive, confirm intent before any build or injection run.
- If a build failure looks resumable, inspect the checkpoint before deleting anything.
- If index selection is unclear, compare cost and retrieval depth before choosing the hybrid route.

## What a good answer should include

- the project folder and schema file that will be touched
- the exact chain or index manager that fits the data shape
- the minimum safe preflight to run before a live command
- whether any checkpoints, deletions, or server writes are involved
- the next command to run only after the local layout is consistent

## Stop conditions

Stop and ask for confirmation when the task would:

- create or restore a project against the wrong server
- commit a schema that does not match the namespace
- use a destructive writer mode
- require an unavailable external service or a missing custom component

## Bundled helpers

- `scripts/validate_project_layout.py` — checks that the project layout, namespace, schema file, and builder folders line up before a build.
- `references/data-and-configuration.md` — use this when choosing a builder chain or index manager.
- `references/troubleshooting.md` — use this when project creation, schema commit, or checkpoint handling fails.
