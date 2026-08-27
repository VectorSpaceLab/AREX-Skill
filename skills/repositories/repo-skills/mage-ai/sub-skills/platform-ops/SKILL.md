---
name: platform-ops
description: "Mage CLI, startup, runtime environment, authentication, logging,
  and production operations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Platform Ops

Use this route for installation, project bootstrap, server startup, pipeline execution, maintenance commands, and production/runtime settings.

## Owns

- Install Mage with Docker, `pip`, or `conda`
- `mage init`, `mage start`, `mage run`
- `clean-cached-variables` and `clean-old-logs`
- Server startup behavior, base paths, auth, logging, database URLs, and read-only settings
- Common startup/runtime failures and recovery steps
- Cloud-side `create-spark-cluster` when the user explicitly wants EMR provisioning

## Excludes

- Block code and template authoring, which belongs in `pipeline-authoring`
- Connector profiles and `io_config.yaml`, which belong in `batch-integrations`
- Streaming source/sink configuration, which belongs in `streaming`
- dbt orchestration, which belongs in `dbt-workflows`
- AI generation and documentation helpers, which belong in `ai-workflows`

## Use this route when

- The user asks how to install or launch Mage
- The user asks how to start or stop a local project
- The user asks about CLI flags, `mage` command output, or `mage_ai.run`
- The user needs auth, logging, monitoring, or production configuration guidance
- The user sees startup failures, browser routing issues, database migration problems, or file-descriptor issues

## Bundled reference

Read `references/cli-and-runtime.md` for the command matrix, runtime environment variables, and the differences between local, Docker, and production-style startup.

## Bundled script

- `../../scripts/smoke_cli.py` — safe import and CLI help check
- `../../scripts/check_project_layout.py` — safe project-path inspection without mutation

## Core reminders

- `mage start` and `mage run` expect the repo path to be resolved before database and server setup.
- User authentication is enabled by default in current Mage OSS versions and in Mage Pro.
- `create-spark-cluster` has AWS/EMR side effects; only use it when the user explicitly wants cluster provisioning.
