---
name: query-engine
description: "Guide Wren governed SQL and cube queries, dry-plan and dry-run
  diagnostics, connectors, SQL policy, and the WrenEngine Python API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren Query Engine

Use this route for a business-data query, a planning error, a cube query, a
connector decision, or Python code that embeds Wren's semantic engine.

## Safe Query Order

1. Confirm the project and compiled target:
   ```bash
   wren context show
   test -f target/mdl.json
   ```
2. Fetch schema/business context through the memory-knowledge route when
   available; write SQL against MDL model/view names, not raw tables.
3. For a complex query, inspect generated SQL before execution:
   ```bash
   wren dry-plan --sql 'SELECT ...'
   ```
4. Execute only after the plan and profile are correct:
   ```bash
   wren query --sql 'SELECT ...' --output table --limit 100
   ```
5. Use `wren dry-run` for a live database validation with no returned rows.
6. Store a successful, meaningful NL→SQL pair through the memory route only
   after it is accepted as correct.

## Choose the Interface

- `wren --sql` is the short form of `wren query`.
- `wren dry-plan` is a semantic/dialect plan and does not need a live query.
- `wren dry-run` checks the planned SQL against the live datasource.
- `wren cube query` is preferred for a covered measure/dimension/time query.
- `WrenEngine` returns a PyArrow table to Python callers.
- For a new or unfamiliar query shape, inspect the resulting plan before an
  execution path that could access a costly or production datasource.

## Fast Error Recovery

- **Model/column error in a dry plan**: read project context or memory first;
  correct one semantic name/relationship issue, then rerun the plan.
- **Plan succeeds but a query fails**: preserve the emitted dialect SQL and
  check the selected profile, connector extra, permissions, and database error.
- **Aggregation request**: ask whether a cube already covers it before writing
  raw `GROUP BY` SQL.
- **Local file/table issue**: confirm the model physical reference and the
  connector's file/catalog conventions; do not change semantic model names just
  to hide an attachment mismatch.

## Route Elsewhere

- Project/profile/MDL authoring: `../cli-projects/SKILL.md`.
- Memory/knowledge context: `../memory-knowledge/SKILL.md`.
- Framework agent tools: `../sdk-integrations/SKILL.md`.

## References and Helpers

- Read `references/query-workflows.md` for query and error-recovery order.
- Read `references/python-api.md` for verified Python signatures and low-level
  planning behavior.
- Read `references/connectors.md` before selecting optional datasource packages.
- Read `references/cubes.md` for structured aggregation syntax.
- Read `references/troubleshooting.md` when the plan or execution fails.
- Run `scripts/check_wren_environment.py` for package/CLI checks and
  `scripts/dry_plan_smoke.py --mdl <path> --datasource <name> --sql '...'` for
  a no-database planning smoke.

## Guardrails

- A successful dry-plan does not prove database permissions, connectivity, or
  query cost.
- A CPU import does not verify a remote connector or cloud credential.
- Respect configured `strict_mode` and `denied_functions`; do not bypass them
  by changing query text or using unmodeled tables.
