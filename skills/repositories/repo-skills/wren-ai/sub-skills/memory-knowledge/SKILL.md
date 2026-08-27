---
name: memory-knowledge
description: "Guide Wren project knowledge, business rules, NL-to-SQL memory,
  schema retrieval, recall, memory index maintenance, and the enrich-context
  workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren Memory and Knowledge

Use this sub-skill when a task concerns business meaning that the schema alone
does not capture: rules, glossary knowledge, accepted queries, memory fetch or
recall, a stale index, or context enrichment.

## Operating Model

- `knowledge/` is durable project source.
- `knowledge/rules/` holds business rules for agents.
- `knowledge/sql/` holds confirmed NL→SQL pairs and is the source of truth for
  query memory.
- `.wren/memory/` is derived runtime state. It may be rebuilt and should not be
  committed as the sole copy of business knowledge.

## Everyday Workflow

1. Build the MDL after semantic source edits:
   ```bash
   wren context validate
   wren context build
   ```
2. Read business rules once at the start of a data-question session:
   ```bash
   wren context instructions
   ```
3. Retrieve schema context or prior examples before writing SQL:
   ```bash
   wren memory fetch -q "monthly customer revenue"
   wren memory recall -q "monthly customer revenue" --limit 3
   ```
4. Store an accepted non-exploratory result:
   ```bash
   wren memory store --nl "monthly customer revenue" --sql "SELECT ..."
   ```
5. Rebuild or audit derived memory only when source changes or drift require it:
   ```bash
   wren memory index
   wren memory check
   ```

## Backend Decision

Without the `memory` extra, Wren's lightweight grep behavior can still store and
recall pairs from `knowledge/sql/`. Semantic schema retrieval and the LanceDB
index need:

```bash
pip install "wrenai[memory]"
```

Do not install the large semantic-memory stack just to store a markdown query
pair.

## Context Enrichment

Use enrichment only after selecting a project and a mode. Preserve these rules:

- Add new knowledge; do not silently rewrite existing definitions.
- Validate every MDL edit immediately; revert that single change if validation
  fails.
- In auto-pilot mode, stop for conflicts and high-blast-radius additions such as
  cubes, views, relationships, or calculated metrics.
- Treat raw documents as evidence and clearly label agent inference.

## References and Helper

- Read `references/knowledge-layout.md` for the v5 project knowledge layout.
- Read `references/memory-workflows.md` for command behavior and fallback rules.
- Read `references/enrich-context.md` before adding business context.
- Read `references/troubleshooting.md` for stale indexes, missing extras, and
  concurrent operations.
- Run `scripts/inspect_memory_state.py --project <directory>` for a safe
  filesystem-only state summary.

## Route Elsewhere

- Project/profile creation: `../cli-projects/SKILL.md`.
- SQL planning/execution: `../query-engine/SKILL.md`.
- CLI-served agent guide retrieval: `../agent-workflows/SKILL.md`.
