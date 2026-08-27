---
name: mage-ai
description: "Mage AI repo skill for platform operations, pipeline authoring,
  integrations, dbt, streaming, and AI workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Mage AI

Use this skill for the `mage-ai` repository and package. It is self-contained: future work should rely on the bundled references and scripts in this skill tree, not on the original checkout.

## Quick route map

| User need | Route |
| --- | --- |
| Install Mage, bootstrap a project, start the server, run a pipeline, clean logs/variables, or diagnose auth/logging/runtime startup issues | `sub-skills/platform-ops/` |
| Author batch pipelines with Python, SQL, or R blocks; use runtime variables; work with dynamic blocks or templates | `sub-skills/pipeline-authoring/` |
| Configure `io_config.yaml`, batch data integration pipelines, source/destination profiles, or connector settings | `sub-skills/batch-integrations/` |
| Build or debug real-time pipelines, Kafka/CDC flows, or streaming sources/sinks | `sub-skills/streaming/` |
| Add existing dbt projects, run dbt models or tests, or interpolate Mage values into dbt workflows | `sub-skills/dbt-workflows/` |
| Set up AI generation, documentation helpers, or AI credentials and failures | `sub-skills/ai-workflows/` |

## Shared facts

- Public package name: `mage-ai`
- Console entry point: `mage`
- Python helper: `mage_ai.run(pipeline_uuid, project_path=None, block_uuid=None, run_sensors=True, **global_vars)`
- Supported setup paths in the docs are Docker, `pip`, and `conda`.
- Helpful extras: `mage-ai[ai]`, `mage-ai[streaming]`, and `mage-ai[dbt]`.

## How to use this skill

1. Pick the route that matches the user's task.
2. Read the route's `SKILL.md` and bundled references first.
3. Use the bundled scripts for safe smoke checks when a task needs a quick validation.
4. Keep execution, troubleshooting, and connector details inside the route that owns them.

## Safe starting checks

- `scripts/smoke_cli.py` — import and CLI help smoke test
- `scripts/check_project_layout.py` — inspect a Mage project path without mutating it

## What this skill does not do

- It does not require the original repository checkout once the skill is loaded.
- It does not execute cloud, broker, database, or model side effects unless the user explicitly asks for them.
- It does not replace route-specific guidance with generic Mage documentation.
