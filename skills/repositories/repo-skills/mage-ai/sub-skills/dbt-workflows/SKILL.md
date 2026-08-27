---
name: dbt-workflows
description: "Mage dbt project setup, model execution, tests, and variable interpolation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# dbt Workflows

Use this route for Mage's dbt integration.

## Owns

- Adding an existing dbt project to Mage
- Running a single dbt model, selected models, or model tests
- dbt profile selection and variable interpolation
- `block_output(...)` interpolation from upstream Mage blocks
- dbt setup, preview, and test workflows in Docker-oriented Mage deployments

## Excludes

- Plain SQL block authoring, which belongs in `pipeline-authoring`
- Project bootstrap, auth, logging, and deployment, which belong in `platform-ops`
- Connector/profile configuration outside dbt, which belongs in `batch-integrations`
- Streaming connectors, which belong in `streaming`
- AI generation, which belongs in `ai-workflows`

## Use this route when

- The user asks how to add or run a dbt project inside Mage
- The user wants to run or preview a dbt model from a pipeline block
- The user asks about `dbt tests`, `dbt build`, or profile/variable behavior in Mage

## Bundled reference

Read `references/dbt-workflows.md` for the setup flow, model-selection patterns, interpolation rules, and connector notes.

## Core reminders

- The docs describe dbt support as Docker-oriented in OSS.
- `mage-ai[dbt]` is the relevant extra for dbt support.
- `block_output(...)` is Mage-side interpolation that happens before dbt runs.
