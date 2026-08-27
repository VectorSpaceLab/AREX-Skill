# Enriching Business Context

## When to read

Read this when MDL has schema shape but agents still misunderstand enums, units,
NULL semantics, soft deletes, canonical tables, business names, metrics, or
query conventions.

## Choose a mode before reading/writing

- **Grill mode**: ask one scoped question at a time, propose a concrete draft,
  and wait for acceptance/edit/skip.
- **Auto-pilot**: apply low-blast-radius additions from evidence, but stop for
  conflicts, ambiguous destinations, and new cubes/views/relationships or other
  high-impact semantic objects.

Do not switch modes mid-session. Select the project explicitly; do not assume the
current directory is the intended data context.

## Evidence and sinks

Read project context and provided raw material before proposing changes. Route
new information deliberately:

| Finding | Sink |
| --- | --- |
| Model/column description or schema structure | MDL YAML |
| Named aggregation metric | Cube YAML after duplicate check |
| Default filter, synonym, external ID, currency, canonical-table convention | `knowledge/rules/` |
| Confirmed question/SQL example | `wren memory store` -> `knowledge/sql/` |

Examples of column-local facts include enum meanings, units, NULL meaning,
magic sentinel values, and time conventions. Record them as explicit description
text rather than relying on an agent's inference.

## Non-negotiable safety

1. Add rather than silently overwrite existing semantic text.
2. Validate every MDL edit immediately:
   ```bash
   wren context validate
   ```
3. For a new cube, also validate generated SQL:
   ```bash
   wren cube query --cube <name> --measures <measure> --sql-only
   ```
4. Revert the single proposed edit when validation fails.
5. Never put private secrets or sensitive raw material into public rules by
   default.

## Cube duplication guard

Before proposing a cube, inspect existing definitions:

```bash
wren cube list
wren cube describe <name>
```

If the same measure expression already exists on the same base object, store or
reference a query example instead of creating a competing metric. If a legacy
metric already represents the logic, surface it for an explicit migration
choice rather than duplicating it.
