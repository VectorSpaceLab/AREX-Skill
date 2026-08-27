---
name: pipeline-authoring
description: "Mage batch pipeline blocks, templates, runtime variables, and
  dynamic execution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Pipeline Authoring

Use this route for batch pipeline code inside Mage blocks.

## Owns

- Python `data_loader`, `transformer`, `data_exporter`, and `test` blocks
- SQL blocks and their runtime variables
- R blocks and runtime variables
- Dynamic blocks and child-block limits
- Runtime variables, environment variables, secrets, and `kwargs`
- Generated block templates and transformer-action scaffolding
- `mage_ai.run()` for programmatic pipeline execution from Python

## Excludes

- Project bootstrap, server startup, auth, logging, and deployment, which belong in `platform-ops`
- Connector profiles and `io_config.yaml`, which belong in `batch-integrations`
- Real-time message streams, which belong in `streaming`
- dbt model orchestration, which belongs in `dbt-workflows`
- AI-assisted generation, which belongs in `ai-workflows`

## Use this route when

- The user asks how to write or debug a block
- The user asks how to pass runtime data between blocks
- The user asks about dynamic blocks or generated templates
- The user needs to understand SQL/R block syntax or block-output semantics
- The user wants to run a pipeline from Python with `mage_ai.run()`

## Bundled reference

Read `references/block-authoring.md` for the block matrix, template patterns, runtime-variable rules, and dynamic-block behavior.

## Bundled troubleshooting

Read `references/troubleshooting.md` for common compile-time, runtime-variable, SQL, R, and dynamic-block failures.

## Core reminders

- Blocks are discovered through the decorators defined in `mage_ai.data_preparation.decorators`.
- Runtime variables must use valid Python identifiers and primitive/basic container values.
- SQL and R blocks are available, but connector-specific credential setup belongs in another route.
