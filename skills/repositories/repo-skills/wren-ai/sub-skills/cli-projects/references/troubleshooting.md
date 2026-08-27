# CLI Project Troubleshooting

## Project found but `target/mdl.json` is missing

Run the source checks first:

```bash
wren context validate
wren context build
```

Do not create a JSON target by hand. If validation fails, correct the named YAML
or relationship/cube reference and rerun validation.

## `catalog` or `schema` points at the wrong place

Project-level `catalog`/`schema` define Wren's semantic namespace. Physical
source location belongs in each model's `table_reference`. If tables are not
found later, inspect the model reference and connector-specific catalog behavior
before changing the project namespace.

## Profile resolves the wrong connection

A bound `profile:` in `wren_project.yml` takes precedence over the globally
active profile. Use `wren profile debug <name>` and check the bound project
configuration before switching global state.

## Missing secret error

Keep the profile placeholder intact; define the referenced uppercase variable
in the intended environment file or shell. Do not replace a placeholder with a
plaintext secret in version-controlled YAML.

## Type conversion or validation error

Run type normalization rather than guessing a SQL type:

```bash
wren utils parse-type --type "raw database type" --dialect postgres
```

For relationships and cube expressions, validate structural YAML first, then
use the relevant query/cube dry-plan route to validate semantics.

## Upgrade uncertainty

Always start with `wren context upgrade --dry-run`. Upgrades are forward-only;
review the planned changes before applying them to a project under version
control.
