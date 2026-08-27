# Framework SDK Troubleshooting

## `from_project()` rejects the project

Confirm that the supplied directory contains `wren_project.yml` and a compiled
`target/mdl.json`. Run the CLI lifecycle first:

```bash
wren context validate --path analytics-project
wren context build --path analytics-project
```

## Query tool is missing memory capabilities

Memory is auto-detected. Check whether project memory state is present and
whether the needed memory extra was installed. Keep `knowledge/sql/` durable;
do not create a fake memory directory just to expose tools.

## Agent prompt mentions a missing tool

Build tools/toolset first, then pass that exact collection to `system_prompt()`
or `instructions()`. This is especially important when
`include_memory_write=False`.

## Profile seems to choose the same database

Inspect placeholder names in profiles and the project `.env`. If all profiles
reference the same variables, they resolve to the same values. Use separate
variables or a project-bound profile with unambiguous configuration.

## Query is too large or error retry loops

Use a smaller limit or aggregate in SQL. Treat retryable semantic errors as
input for dry-plan/model repair; surface connection and infrastructure errors to
the host application rather than asking the LLM to retry indefinitely.
