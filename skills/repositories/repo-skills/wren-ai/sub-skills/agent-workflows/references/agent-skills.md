# CLI-Served Agent Skills

## When to read

Read this when deciding whether an agent should use the Wren discovery stub,
fetch a guide, or inspect bundled references/scripts.

## Delivery model

The small discovery stub is installed once in a compatible AI-client skill
directory. The operational guide content travels with the installed `wrenai`
package and is retrieved on demand:

```bash
wren skills list
wren skills get onboarding
wren skills get usage --full
wren skills get dlt-connector --script introspect_dlt
```

This avoids a stale cached guide when the package CLI is upgraded.

## Installation choices

A client may use the published discovery-stub installer, a compatible skills
manager, or a client plugin mechanism. Installation can modify a user/global
agent directory, so explain the target and ask for approval before using a
command that writes an agent configuration.

The core package install is still required:

```bash
pip install wrenai
```

## Guide routing

- Use `onboarding` for a new Wren user/project/database connection.
- Use `generate-mdl` once a connection exists but semantic models do not.
- Use `usage` for question -> context -> plan -> execution -> store behavior.
- Use `dlt-connector` for SaaS API data that should land in local DuckDB first.
- Use `enrich-context` for business semantics absent from the source schema.
- Use `genbi` for browser-side dashboard application workflows.

## Expected retrieval errors

An unknown guide or script means the requested name is not in the installed
package version. Run `wren skills list`; do not fabricate a guide name or rely
on a separate checkout to supply it.
