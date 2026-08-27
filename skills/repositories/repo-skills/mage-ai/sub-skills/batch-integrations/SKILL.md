---
name: batch-integrations
description: "Mage batch data integration pipelines, io_config.yaml, and
  connector configuration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Batch Integrations

Use this route for non-streaming data integration pipelines and connector configuration.

## Owns

- `io_config.yaml` layout and profile resolution
- Batch data integration pipelines that move data between one source and one destination
- Source/destination configuration, schema settings, bookmarks, and stream selection
- Variable interpolation in integration configs
- Connector families exposed by the repo and the sibling `mage_integrations` package
- Safe validation of connector configuration without running the connector against a live service

## Excludes

- Batch block code itself, which belongs in `pipeline-authoring`
- Real-time message streams, which belong in `streaming`
- dbt orchestration, which belongs in `dbt-workflows`
- CLI bootstrap, auth, logging, and deployment, which belong in `platform-ops`
- AI generation, which belongs in `ai-workflows`

## Use this route when

- The user asks how to configure a source or destination profile
- The user wants to understand `io_config.yaml`
- The user needs help with data integration pipeline schema, bookmark, or prefix behavior
- The user wants to extend or reason about connector configuration

## Bundled reference

Read `references/connectors-and-config.md` for the config shape, interpolation rules, connector families, and source/destination workflow.

## Bundled troubleshooting

Read `references/troubleshooting.md` for Docker, profile, credential, local-host, and S3 credential failures.

## Bundled script

- `scripts/inspect_io_config.py` — safely inspect profiles and key presence without printing secrets

## Core reminders

- The docs and source treat data integrations as Docker-oriented because of connector dependencies.
- `io_config.yaml` belongs in the project root.
- Use this route for the configuration layer; use `pipeline-authoring` for the block logic that consumes the integration output.
