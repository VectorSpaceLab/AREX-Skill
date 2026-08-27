---
name: great-expectations
description: "Use Great Expectations GX Core for data context setup, datasource
  and asset configuration, expectation suites, validation runs, checkpoints,
  actions, and Data Docs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Great Expectations

Use this repo skill when a task is about Great Expectations (GX Core): validating data quality, configuring GX contexts, connecting data assets, authoring expectation suites, running validations, interpreting validation results, or orchestrating checkpoints and Data Docs.

## Start Here

1. Install GX Core if needed with `pip install great_expectations`, then confirm the package imports with `import great_expectations as gx`; for environment checks, run `python scripts/inspect_gx_environment.py`.
2. Pick the route that matches the user's immediate task; do not read every sub-skill up front.
3. Keep workflows modular: contexts own configuration, datasources own batches, suites own expectations, validations own results, and checkpoints own actions/Data Docs.
4. Prefer safe local examples and tiny fixtures before adding optional services, cloud credentials, or warehouse-specific dependencies.

## Route by Task

- Read `sub-skills/contexts-and-configuration/SKILL.md` for `gx.get_context`, ephemeral vs file contexts, metadata stores, config variables, credentials, analytics toggles, Data Docs settings, and import/context sanity checks.
- Read `sub-skills/datasources-and-assets/SKILL.md` for `context.data_sources`, pandas dataframe assets, filesystem assets, SQLite/SQL assets, batch definitions, batch parameters, and optional Spark/cloud/warehouse backends.
- Read `sub-skills/expectations-and-suites/SKILL.md` for built-in expectations, `ExpectationSuite`, suite persistence, runtime parameters, row conditions, custom expectation subclasses, and suite troubleshooting.
- Read `sub-skills/validations-and-results/SKILL.md` for `ValidationDefinition`, `batch.validate`, batch/suite parameters, result formats, validation result interpretation, and unexpected-row retrieval.
- Read `sub-skills/checkpoints-actions-and-data-docs/SKILL.md` for `Checkpoint`, checkpoint actions, Slack/email notification safety, custom actions, Data Docs updates, and production validation orchestration.

## Shared References and Scripts

- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, version, pandas/pydantic, credential, and workflow routing failures.
- Read `references/repo-provenance.md` to decide whether this skill is stale relative to the source repository revision.
- Read `references/repo-routing-metadata.json` only when importing or updating the managed `repo-skills-router`.
- Run `scripts/inspect_gx_environment.py --help` for a safe public API inspection helper that prints GX version, top-level exports, context managers, and datasource factory availability.

## Minimal API Shape

```python
import great_expectations as gx

context = gx.get_context(mode="ephemeral")
suite = gx.ExpectationSuite(name="quality_suite")
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="id"))
```

The installed package exposes GX primarily through Python APIs. This checkout did not expose package console scripts, so treat command-line guidance as project-specific unless a future version adds documented entry points.

Minimal verification command after installation:

```bash
python -c "import great_expectations as gx; print(gx.__version__); print(gx.get_context(mode='ephemeral'))"
```

## Common Workflow Order

1. Create a context with `gx.get_context(...)` and decide whether metadata should persist.
2. Add or retrieve a datasource and data asset, then create a reusable batch definition.
3. Create an `ExpectationSuite` and add built-in or custom expectation objects.
4. Create a `ValidationDefinition` from a batch definition and suite, then run it with the required `batch_parameters` and optional `expectation_parameters`.
5. Add a `Checkpoint` only when the workflow needs repeatable production orchestration, actions, notifications, or Data Docs.

## Guardrails

- Do not hardcode database passwords, Slack webhooks, SMTP credentials, cloud tokens, or local filesystem secrets in GX config, generated code, logs, or expectation metadata.
- Do not install all optional backends by default; add only the extras or driver packages required for the selected datasource family.
- Do not use `ResultFormat.COMPLETE` or row-level unexpected output on large batches unless the user explicitly needs diagnostics and accepts memory/storage cost.
- Do not send real Slack/email notifications from smoke tests; use configuration checks or mocked actions unless the user authorizes a live send.
- Do not rely on original repository docs, examples, tests, or scripts at runtime; use the bundled references and helper scripts in this skill.
