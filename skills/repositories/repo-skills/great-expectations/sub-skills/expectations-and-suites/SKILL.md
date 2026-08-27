---
name: expectations-and-suites
description: "Create and maintain Great Expectations expectation classes and
  suites, including parameters, row conditions, and custom subclasses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Expectations and Suites

Use this sub-skill when a GX Core task is about choosing built-in Expectations, configuring threshold parameters, grouping Expectations into an `ExpectationSuite`, testing expectations against a small batch, or turning repeated checks into a custom Expectation subclass.

## Route First

- For context creation, store configuration, config variables, and file/ephemeral/cloud mode choices, read `../contexts-and-configuration/SKILL.md` first.
- For datasource, asset, batch definition, and batch request setup, read `../datasources-and-assets/SKILL.md` first.
- For running full validations, interpreting `ExpectationSuiteValidationResult`, unexpected rows, and result format trade-offs, read `../validations-and-results/SKILL.md` next.
- For checkpoint orchestration, severity-triggered actions, notifications, and Data Docs, read `../checkpoints-actions-and-data-docs/SKILL.md` next.

## Local References

- Read `references/expectation-api-patterns.md` when selecting built-in `gx.expectations` classes, adding them to suites, or using severity, notes, meta, and result formats.
- Read `references/row-conditions-and-parameters.md` when an expectation needs `$PARAMETER` values, validation-time `expectation_parameters`, or row-level conditional logic.
- Read `references/custom-expectations.md` when repeated ad hoc checks should become a custom subclass with defaults and a clear description.
- Read `references/troubleshooting.md` when expectation instantiation, suite persistence, row conditions, parameters, or custom classes fail.
- Run `scripts/build_suite_from_dataframe.py --help` to see a tiny, safe dataframe workflow that builds a suite and can optionally validate it.

## Core Workflow

1. Import GX and expectations with `import great_expectations as gx` and use the class-first API under `gx.expectations`.
2. Create concrete expectation instances, for example `gx.expectations.ExpectColumnValuesToNotBeNull(column="id")`, rather than relying on legacy string-only configuration when writing new code.
3. Group expectations with `suite = gx.ExpectationSuite(name="...")`, then call `suite.add_expectation(expectation)` for each unique expectation.
4. Persist the suite only when the target `DataContext` should own it: `context.suites.add(suite)` for new suites, `context.suites.add_or_update(suite)` for replace/update workflows, and `context.suites.get(name="...")` to retrieve it.
5. Test an individual expectation or a whole suite against a sample `Batch` before production use with `batch.validate(expectation_or_suite, expectation_parameters=..., result_format=...)`.

## Guardrails

- Keep suite names stable and descriptive; `ExpectationSuite(name=...)` requires a non-empty string.
- Keep `meta` JSON-serializable and reserve credentials or machine-specific paths for context configuration, not expectation metadata.
- Use `severity="critical"`, `"warning"`, or `"info"` to communicate failure impact; downstream checkpoint actions can route on severity.
- Use `$PARAMETER` dictionaries only for expectation fields that accept runtime/suite parameters, and always document the required `expectation_parameters` keys near the suite.
- Do not put datasource setup, checkpoint actions, or large validation-result interpretation in this sub-skill; route to the sibling sub-skills listed above.
