---
name: cli-projects
description: "Guide Wren CLI project setup, MDL authoring, profiles, connection
  fields, schema validation, build lifecycle, dbt or OSI import, and SQL type
  normalization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren CLI Projects

Use this sub-skill when a task creates, repairs, migrates, or inspects a Wren
project; configures a profile; needs MDL YAML; imports dbt/OSI material; or
needs the exact fields for a datasource.

## Workflow

1. **Identify the project**. A Wren project has `wren_project.yml`. Commands
   discover it from an explicit path, `WREN_PROJECT_HOME`, the current directory
   and its parents, then a configured default project.
2. **Inspect before editing**:
   ```bash
   wren context show
   wren profile list
   wren docs connection-info <datasource>
   ```
3. **Create or import deliberately**:
   ```bash
   wren context init --path my-project
   wren context init --from-mdl previous-mdl.json --path my-project
   wren context init --from-osi semantic_model.yaml --data-source postgres --path my-project
   ```
   For dbt, route through the documented `wren profile import dbt` and
   `wren context import dbt` commands after dbt artifacts are present.
4. **Edit source, then validate and build**:
   ```bash
   wren context validate --path my-project
   wren context build --path my-project
   ```
5. **Bind a connection without embedding a secret**. Create a profile with
   placeholders, then bind it to the project:
   ```bash
   wren profile add analytics --from-file connection.yml
   wren context set-profile analytics --path my-project
   ```
6. **Normalize external SQL types** before writing model columns:
   ```bash
   wren utils parse-type --type "character varying(255)" --dialect postgres
   ```

## Choose the Correct Artifact

| Need | Use |
| --- | --- |
| Project metadata and semantic namespace | `wren_project.yml` |
| Physical or SQL-defined semantic object | `models/<name>/metadata.yml` |
| Reusable logical query | `views/<name>/metadata.yml` |
| Named aggregation API | `cubes/<name>/metadata.yml` |
| Inter-model joins | `relationships.yml` |
| Durable business rules and confirmed query examples | `knowledge/` |
| Derived engine input | `target/mdl.json` |
| Environment-specific connection | profile plus `.env` values |

Do not copy a physical database catalog/schema into the project-level
`catalog`/`schema`. Project values are Wren's namespace; a model's
`table_reference` identifies the physical source object.

## Route Elsewhere

- For SQL execution, dry-plan recovery, cube queries, or `WrenEngine`, read
  `../query-engine/SKILL.md`.
- For memory index/recall and business-rule enrichment, read
  `../memory-knowledge/SKILL.md`.
- For agent-served workflow guides, read `../agent-workflows/SKILL.md`.

## References and Helper

- Read `references/project-lifecycle.md` for the lifecycle order and migration
  decisions.
- Read `references/mdl-schema.md` before writing models, views, relationships,
  or cubes.
- Read `references/profiles-and-connections.md` before creating a profile or
  resolving `${ENV_VAR}` values.
- Read `references/troubleshooting.md` when validation, project discovery, or
  connection setup fails.
- Run `scripts/validate_wren_project.py --project <directory>` for a safe
  structural preflight. It does not build, query, or change the project.

## Guardrails

- Validate before build; build after source edits; re-index memory only after a
  successful build when memory is part of the workflow.
- Prefer `wren docs connection-info` to guessing profile field names.
- Use `.env` or process environment for secret values. Do not send credentials
  in chat or place them in committed project files.
- `wren context upgrade --dry-run` is the first step for a schema-version
  migration; upgrades are forward-only.
