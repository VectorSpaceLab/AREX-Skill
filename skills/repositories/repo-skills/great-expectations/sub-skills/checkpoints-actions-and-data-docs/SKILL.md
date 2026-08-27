---
name: checkpoints-actions-and-data-docs
description: "Build, save, and run GX Checkpoints; configure actions,
  notifications, custom actions, and local Data Docs updates safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Checkpoints, Actions, and Data Docs

Use this sub-skill when a task needs production-style Great Expectations orchestration: running one or more saved validations through a Checkpoint, updating Data Docs, sending notifications, or adding custom post-validation actions.

## Route by task

- Read [Checkpoint API](references/checkpoint-api.md) to construct `gx.Checkpoint`, persist it with `context.checkpoints`, pass `batch_parameters` and `expectation_parameters`, choose checkpoint result formats, and summarize `CheckpointResult` objects.
- Read [Actions and notifications](references/actions-and-notifications.md) before adding `UpdateDataDocsAction`, `SlackNotificationAction`, `EmailAction`, or a custom `ValidationAction`; this reference covers `notify_on`, `notify_with`, credential safety, and no-network tests.
- Read [Data Docs](references/data-docs.md) when configuring local or networked Data Docs sites, calling `context.build_data_docs()`, opening docs, or diagnosing stale docs.
- Read [Troubleshooting](references/troubleshooting.md) when checkpoints have no validation definitions, notification credentials are missing, Slack/email sends happen unexpectedly, Data Docs are absent/stale, results are too verbose, or custom action payloads do not match.
- Run [scripts/run_checkpoint_smoke.py](scripts/run_checkpoint_smoke.py) for a tiny no-network checkpoint smoke workflow that builds an ephemeral pandas validation, runs a checkpoint, and optionally exercises a safe local `UpdateDataDocsAction` in a temporary file project.

## Prerequisite routes

- For context mode, file-project persistence, config variables, and credential substitution, read `../contexts-and-configuration/SKILL.md`.
- For datasource, asset, and batch-definition setup, read `../datasources-and-assets/SKILL.md`.
- For expectation suites and custom expectations, read `../expectations-and-suites/SKILL.md`.
- For validation-definition creation, result interpretation, and unexpected rows, read `../validations-and-results/SKILL.md`.

## Core public APIs

- Import GX as `import great_expectations as gx`.
- Import actions from `great_expectations.checkpoint` or `great_expectations.checkpoint.actions`, including `UpdateDataDocsAction`, `SlackNotificationAction`, `EmailAction`, and `ValidationAction`.
- Construct checkpoints with `gx.Checkpoint(name=..., validation_definitions=[...], actions=[...], result_format=...)`.
- Persist checkpoints with `context.checkpoints.add(...)` or `context.checkpoints.add_or_update(...)`; retrieve with `context.checkpoints.get(name)` and list/delete with `all()` and `delete(name)`.
- Run checkpoints with `checkpoint.run(batch_parameters=..., expectation_parameters=..., run_id=...)` and inspect `result.success`, `result.run_results`, and `result.describe_dict()`.

## Guardrails

- Never place real Slack webhooks, bot tokens, SMTP passwords, or recipient lists in code, generated skills, logs, or committed GX config; use config variables or environment substitution.
- Do not include Slack/email actions in smoke tests unless the test explicitly mocks network calls; notification actions call external APIs when `notify_on` matches the result.
- Put `UpdateDataDocsAction` before notification actions for readability, even though GX prioritizes Data Docs actions internally so notification renderers can use fresh docs links.
- Prefer `SUMMARY` or `BASIC` for routine checkpoint runs; reserve `COMPLETE` for bounded diagnostics because it can inflate stored validation results and notification payloads.
