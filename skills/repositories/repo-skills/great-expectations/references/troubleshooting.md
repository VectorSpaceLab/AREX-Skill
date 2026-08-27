# Great Expectations Troubleshooting

Use this reference for failures that cut across contexts, datasources, expectations, validations, checkpoints, and optional integrations.

## Import and Version Problems

Symptoms:
- `ModuleNotFoundError: No module named 'great_expectations'`
- `AttributeError` for top-level exports such as `get_context`, `ExpectationSuite`, `ValidationDefinition`, or `Checkpoint`
- Behavior differs from this skill's API examples

Likely causes:
- The package is not installed in the Python environment running the code.
- Another environment or an old GX release is active.
- Code uses legacy Great Expectations APIs from older tutorials.

Recovery:
1. Run `python scripts/inspect_gx_environment.py` from this skill or a similar import check in the target environment.
2. Verify `import great_expectations as gx` and `gx.__version__`.
3. Prefer the current class-based API shown in this skill: `gx.get_context`, `gx.ExpectationSuite`, `gx.ValidationDefinition`, and `gx.Checkpoint`.
4. If a task references old `DataContext`, YAML checkpoint, or legacy validator flows, translate it to the current route before editing.

## Optional Dependency Problems

Symptoms:
- Imports fail for Spark, SQLAlchemy drivers, cloud SDKs, or warehouse-specific packages.
- Datasource factories exist but connections fail at import or engine creation time.
- Pandas file readers fail for Parquet or Excel.

Likely causes:
- Base GX dependencies are installed, but optional backend packages are missing.
- Driver packages or system libraries are not compatible with the selected backend.
- Credentials or network access are unavailable.

Recovery:
1. Identify the selected datasource family first: pandas dataframe, filesystem pandas, SQLite, generic SQL, Spark, cloud storage, or warehouse.
2. Read `sub-skills/datasources-and-assets/references/optional-backends.md` before installing broad extras.
3. Install only the missing backend package or documented extra needed for that route.
4. Prefer SQLite or pandas filesystem smoke checks when validating GX behavior independent of external services.

## Pydantic and Validation Errors

Symptoms:
- `ValidationError` during expectation, datasource, action, or context object creation.
- Field names are rejected even though older snippets mention them.
- Literal values such as `notify_on`, `result_format`, `condition_parser`, or datasource type are rejected.

Likely causes:
- GX objects are pydantic models with strict field names and literals.
- A parameter belongs to a different object layer.
- Code mixed legacy string/dict configs with the current class-based API.

Recovery:
1. Check the nearest sub-skill API reference for the object being constructed.
2. Move datasource parameters to datasource/asset methods, expectation parameters to expectation classes, validation runtime values to `run(...)`, and action settings to action constructors.
3. Use supported literals: result formats such as `BOOLEAN_ONLY`, `BASIC`, `SUMMARY`, `COMPLETE`; notification values such as `all`, `success`, `failure`, `info`, `warning`, `critical`.
4. For dynamic expectation thresholds, use `$PARAMETER` dictionaries and pass matching `expectation_parameters` at validation time.

## Context and Credential Problems

Symptoms:
- `gx.get_context()` returns an ephemeral context when persistence was expected.
- Config variable substitution does not resolve.
- Cloud mode or token errors appear in a local GX Core workflow.
- Data Docs or stores write to unexpected locations.

Recovery:
1. Read `sub-skills/contexts-and-configuration/SKILL.md` and choose `mode="ephemeral"` or `mode="file"` deliberately.
2. Put secrets in environment variables, config variables, or supported secret-manager references, not in expectation suites or generated code.
3. Reinitialize the context after changing persistent file configuration.
4. Avoid Cloud mode unless the task is explicitly about GX Cloud and credentials are available.

## Result Size and Performance Problems

Symptoms:
- Validation output is huge or slow.
- Stored validation results or notification payloads become too large.
- Unexpected row requests time out or consume too much memory.

Recovery:
1. Start with `SUMMARY` or `BASIC` result format.
2. Use `COMPLETE`, `include_unexpected_rows`, and full unexpected row retrieval only on bounded diagnostic batches.
3. Route detailed result-format work to `sub-skills/validations-and-results/references/result-formats-and-outputs.md`.
4. Route checkpoint payload concerns to `sub-skills/checkpoints-actions-and-data-docs/references/checkpoint-api.md`.

## Safe Routing Checklist

- Context or config failure: `sub-skills/contexts-and-configuration/SKILL.md`
- Data connection, assets, or batch discovery: `sub-skills/datasources-and-assets/SKILL.md`
- Expectation classes, suites, row conditions, or custom expectations: `sub-skills/expectations-and-suites/SKILL.md`
- Validation execution, result formats, or unexpected rows: `sub-skills/validations-and-results/SKILL.md`
- Checkpoints, actions, notifications, or Data Docs: `sub-skills/checkpoints-actions-and-data-docs/SKILL.md`
