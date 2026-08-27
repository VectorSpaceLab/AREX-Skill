---
name: validations-and-results
description: "Create and run GX ValidationDefinitions, pass batch and suite
  parameters, choose result formats, interpret validation results, and retrieve
  unexpected rows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Validations and Results

Use this sub-skill when a task needs to execute Great Expectations validations and interpret their outputs. It assumes the agent already has a GX context, a data asset or batch definition, and an expectation suite.

## Route by task

- Read [Validation definition workflows](references/validation-definition-workflows.md) to create, save, retrieve, and run `gx.ValidationDefinition` objects, pass `batch_parameters` and `expectation_parameters`, or use the `batch.validate()` shortcut.
- Read [Result formats and outputs](references/result-formats-and-outputs.md) before selecting `ResultFormat.BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, `COMPLETE`, or a result-format dict, and when interpreting `success`, `statistics`, `results`, `meta`, and `exception_info`.
- Read [Unexpected rows](references/unexpected-rows.md) when a task asks for all failing rows, `unexpected_rows`, `unexpected_index_query`, caps, or backend-specific limitations.
- Read [Troubleshooting](references/troubleshooting.md) to diagnose stale validation definitions, missing batch parameter keys, unresolved suite parameters, overlarge results, hidden exceptions, or result-format confusion.
- Run [scripts/run_validation_smoke.py](scripts/run_validation_smoke.py) to verify the installed GX Python API with a tiny local dataframe validation that prints success and statistics.

## Prerequisite routes

- For contexts, stores, Cloud/file/ephemeral mode, and project configuration, read `../contexts-and-configuration/SKILL.md`.
- For datasource, data asset, batch definition, and batch-parameter setup, read `../datasources-and-assets/SKILL.md`.
- For expectation and suite authoring details, row conditions, custom expectations, and `$PARAMETER` usage inside expectations, read `../expectations-and-suites/SKILL.md`.
- For checkpoint orchestration, actions, notifications, and Data Docs updates, read `../checkpoints-actions-and-data-docs/SKILL.md`.

## Core public APIs

- Import GX as `import great_expectations as gx`.
- Construct validations with `gx.ValidationDefinition(name=..., data=batch_definition, suite=expectation_suite)`.
- Persist and retrieve validations through `context.validation_definitions.add(...)`, `add_or_update(...)`, `get(name)`, `all()`, and `delete(name)`.
- Execute validations with `validation_definition.run(batch_parameters=..., expectation_parameters=..., result_format=..., run_id=...)`.
- Validate one expectation directly against an already materialized batch with `batch.validate(expectation, result_format=..., expectation_parameters=...)`.
- Use `gx.ResultFormat` enum values or equivalent strings/dicts for result verbosity.

## Guardrails

- Do not use checkpoints for simple validation execution unless the task needs actions, notifications, or Data Docs.
- Do not assume every backend supports every diagnostic output; unexpected row retrieval and index-query output vary across Pandas, SQL, and other execution engines.
- Avoid `COMPLETE` and `include_unexpected_rows` on large batches unless the user explicitly needs row-level diagnostics and accepts the performance and memory cost.
- Keep validation code free of credentials and external services unless routed through the context/datasource sub-skills.
