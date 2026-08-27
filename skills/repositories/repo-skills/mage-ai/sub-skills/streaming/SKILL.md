---
name: streaming
description: "Mage streaming pipelines, real-time sources, sinks, and connector
  configuration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Streaming

Use this route for real-time Mage pipelines and message-oriented connectors.

## Owns

- Streaming pipeline structure: source, transformer, sink
- `SourceFactory` and `SinkFactory` connector selection
- Kafka, CDC, and other live streaming source/sink configs
- Streaming executor knobs such as `executor_count` and `executor_type`
- Message metadata, batch size, checkpointing, and live connector troubleshooting

## Excludes

- Batch data integrations and `io_config.yaml`, which belong in `batch-integrations`
- Batch pipeline block code, which belongs in `pipeline-authoring`
- dbt orchestration, which belongs in `dbt-workflows`
- CLI/bootstrap/auth/logging, which belong in `platform-ops`
- AI generation, which belongs in `ai-workflows`

## Use this route when

- The user asks about real-time pipelines
- The user mentions Kafka, CDC, Pub/Sub, Kinesis, RabbitMQ, or similar live connectors
- The user needs sink selection or source-selection guidance for streaming
- The user is debugging a streaming connector failure or runtime mode issue

## Bundled reference

Read `references/streaming-connectors.md` for the source/sink matrix, connector patterns, executor settings, and message-handling notes.

## Bundled troubleshooting

Read `references/troubleshooting.md` for connection, auth, live-broker, and test-environment failures.

## Core reminders

- Streaming pipelines are different from batch integrations; do not route them through `batch-integrations`.
- The repo's streaming source class tests can try live connection checks unless the environment is treated as test.
- Many connectors require extra packages and external services that are not part of a plain CPU-only install.
