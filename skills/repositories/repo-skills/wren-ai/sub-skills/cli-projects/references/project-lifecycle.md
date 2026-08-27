# Project Lifecycle

## When to read

Read this for a new project, an imported manifest, a migration, or a validation
failure. It defines the order of operations that keeps project source and the
compiled MDL consistent.

## Minimal lifecycle

```bash
mkdir analytics-project && cd analytics-project
wren context init
# Add or import models, views, relationships, cubes, and knowledge
wren context validate
wren context build
```

A build compiles project YAML into `target/mdl.json`. Query, MCP, SDK, and
GenBI paths that need an MDL use that derived file. Rebuild after source changes.

## Common lifecycle variants

### Initialize an empty project

```bash
wren context init --empty --path analytics-project
```

Use this when an agent or a user will create model YAML from schema discovery.
The generated structure includes models, views, relationships, knowledge, and
an agent guidance file.

### Import a legacy compiled MDL

```bash
wren context init --from-mdl old-mdl.json --path analytics-project
wren context validate --path analytics-project
wren context build --path analytics-project
```

The imported JSON uses camelCase, while YAML source uses snake_case. Treat the
new YAML as the editable source of truth after import.

### Import an OSI semantic model

```bash
wren context init --from-osi semantic_model.yaml --data-source postgres --path analytics-project
wren context validate --path analytics-project
wren context build --path analytics-project
```

Choose the target datasource explicitly because type and dialect interpretation
must be known during conversion.

### Import dbt artifacts

Before importing, generate the dbt manifest/catalog artifacts with dbt. Then:

```bash
wren profile import dbt --project-dir path-to-dbt-project
wren context import dbt --project-dir path-to-dbt-project --path analytics-project
```

Use `--dry-run` before an import that would write a project. Review generated
models and relationships before trusting query output.

## Upgrade an existing project

```bash
wren context upgrade --dry-run
wren context upgrade
wren context validate
wren context build
```

The current project layout is schema version 5. It adds the first-class
`knowledge/` base; older `instructions.md` and `queries.yml` remain readable
for compatibility but should be migrated intentionally.

## Verify without a database

`wren context validate` checks source structure and project consistency.
`wren context build` creates the compiled manifest. Neither needs a successful
remote database query for basic project construction. Use a separate query or
dry-plan only after the project workflow requires it.
