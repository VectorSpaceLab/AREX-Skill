---
name: contexts-and-configuration
description: "Choose and configure Great Expectations Data Contexts, metadata
  stores, credentials, Data Docs, analytics, and import sanity checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Contexts and Configuration

Use this sub-skill when a task needs a Great Expectations (GX Core) Data Context, project configuration, safe credential substitution, metadata-store/Data Docs settings, analytics toggles, or a quick import/context sanity check.

## Start Here

1. Choose the context deliberately: `gx.get_context(mode="ephemeral")` for temporary in-memory work, `gx.get_context(mode="file", project_root_dir=...)` or `context_root_dir=...` for persisted projects, and avoid Cloud mode in this GX Core line because Cloud construction raises a shutdown error.
2. Keep context setup separate from downstream work: route data connections to `../datasources-and-assets/SKILL.md`, expectation suites to `../expectations-and-suites/SKILL.md`, validation runs to `../validations-and-results/SKILL.md`, and checkpoint/Data Docs action orchestration to `../checkpoints-actions-and-data-docs/SKILL.md`.
3. For file-backed projects, edit `context.variables.config`, call `context.variables.save()`, and re-initialize the context so stores, Data Docs sites, analytics, and substitutions take effect.
4. Never hardcode credentials in skill outputs or committed project config; use environment variables, `config_variables.yml`, `runtime_environment`, or supported secret-manager references.

## Reference Map

- [Context types and stores](references/context-types-and-stores.md): read when choosing `gx.get_context` arguments, diagnosing file-vs-ephemeral persistence, or understanding context managers and stores.
- [Configuration and credentials](references/configuration-and-credentials.md): read when configuring `DataContextConfig`, config variables, environment substitutions, store paths, Data Docs sites, or analytics toggles.
- [Troubleshooting](references/troubleshooting.md): read when imports fail, the wrong context type appears, config variables do not substitute, Cloud mode is triggered, or store/Data Docs paths behave unexpectedly.
- [Inspect context script](scripts/inspect_context.py): run for a safe local smoke check of GX import/version, `gx.get_context`, context mode/type, managers, store names, and optional file-context scaffolding.

## Safe Inspection

From this sub-skill directory, run the bundled helper with no arguments for an ephemeral context sanity check:

```bash
python scripts/inspect_context.py
```

From the root `great-expectations/` skill directory, use the full sub-skill path:

```bash
python sub-skills/contexts-and-configuration/scripts/inspect_context.py
```

Run it against a disposable or intended file project root when you need to prove file-mode scaffolding/loading works:

```bash
python sub-skills/contexts-and-configuration/scripts/inspect_context.py --mode file --project-root-dir ./gx-project
```

The helper prints a compact JSON summary and does not print absolute project paths or credentials.
