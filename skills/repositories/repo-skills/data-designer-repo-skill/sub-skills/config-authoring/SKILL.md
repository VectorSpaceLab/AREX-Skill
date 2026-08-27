---
name: config-authoring
description: "Design, inspect, validate, and serialize DataDesigner configs:
  builders, columns, samplers, seeds, person data, validators, processors,
  model/tool configs, custom columns, skip/drop rules, and Jinja references."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Config Authoring

Use this sub-skill when the user needs to create, edit, inspect, validate, or serialize `data_designer.config` objects or a Python script that returns a `DataDesignerConfigBuilder`.

## Route here for

- Builder API questions: `DataDesignerConfigBuilder`, shorthand `add_column(...)`, `from_config(...)`, `build()`, and `write_config(...)`.
- Column design: sampler, LLM text/code/structured/judge, expression, validation, embedding, image, seed dataset, and custom column configs.
- Sampler parameters, sampler constraints, conditional sampler params, person/person-from-faker fields, and managed persona schema inspection.
- Seed source configs and seed/person Jinja references.
- Config-only model/tool declarations: `ModelConfig`, inference params, `ModelProvider`, `ToolConfig`, and MCP provider config objects.
- Troubleshooting Pydantic validation, discriminators, missing fields, bad Jinja syntax/references, drop/skip propagation, and serialization errors.

## Do not handle here

- Running generation, `preview`, `create`, result artifacts, resume, or model readiness probes. Route to [`generation-runtime`](../generation-runtime/SKILL.md), especially for `preview`, `create`, and `check_models`.
- CLI state files, `data-designer` command syntax, `agent context/types/state`, or non-TTY behavior. Route to `cli-and-agent-tools`.
- Installing/discovering plugin packages or building package entry points. Route to `plugins-and-extensions`.
- Long recipe selection or adaptation narratives. Route to `recipes-and-integrations`.

For package topology and cross-cutting behavior, also use the root [package overview](../../references/package-overview.md). For install/import/global failures that are not config-specific, use root [troubleshooting](../../references/troubleshooting.md).

## Operating workflow

1. **Classify the request.** Decide whether the user is asking to author a new config, inspect an existing builder/YAML/JSON/script, fix a config error, add seed/person data, add validators/processors, or serialize a config.
2. **Load the right reference.**
   - Public API and field sets: [`references/api-reference.md`](references/api-reference.md).
   - Columns, samplers, validators, skip/drop/Jinja, and custom columns: [`references/columns-and-samplers.md`](references/columns-and-samplers.md).
   - Seed sources and person data: [`references/seed-and-person-data.md`](references/seed-and-person-data.md).
   - Symptom-based fixes: [`references/troubleshooting.md`](references/troubleshooting.md).
3. **Prefer public imports.** Use `import data_designer.config as dd` and public `dd.*` exports unless a reference explicitly names a lower-level public module for inspection.
4. **Author a builder, not an execution.** Return or update a `DataDesignerConfigBuilder`; do not call `preview`, `create`, or `check_models` from this sub-skill.
5. **Validate locally before handoff.** At minimum instantiate the config objects and call `builder.build()` to trigger Pydantic validation. If the DataDesigner interface and non-model resources are available, `DataDesigner().validate(builder)` performs compile-time validation without running generation; generation/runtime failures still route to `generation-runtime`.
6. **Be explicit about model aliases.** The installed-package evidence found no usable model aliases by default in the agent context. Config-only sampler/expression/seed workflows can still build and validate without model calls. Model-backed columns need explicit `ModelConfig` aliases before runtime checks.
7. **Serialize only serializable configs.** `builder.write_config("config.yaml")` or `.json` is valid for normal seed sources; `DataFrameSeedSource` intentionally cannot be serialized, so convert it to `LocalFileSeedSource` first.
8. **Use bundled inspectors when facts may be stale.** Run `python scripts/dump_config_type_catalog.py` to refresh live installed field sets and `python scripts/inspect_person_schema.py <locale>` to inspect managed person fields when assets are present.

## Output expectations

- For new scripts, expose `load_config_builder() -> dd.DataDesignerConfigBuilder` and keep dependencies explicit.
- For fixes, state the minimal field/key/discriminator change and the validation command or snippet used.
- For seed/person configs, name which columns remain in final output and which helper columns use `drop=True`.
- For validation handoff, distinguish config validation from runtime generation/model errors and link to `generation-runtime` when model calls or artifacts are involved.
