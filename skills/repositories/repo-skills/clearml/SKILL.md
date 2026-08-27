---
name: clearml
description: "Route ClearML Python SDK tasks across experiment tracking,
  data/versioned storage, remote execution CLIs, automation pipelines, HPO,
  schedulers, routers, and services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Repo Skill

Use this skill when a user asks how to use, configure, script, or troubleshoot the ClearML Python SDK. ClearML is an experiment tracking, data management, remote execution, automation, and MLOps SDK exposed through Python APIs and command-line tools.

This root skill is a router. Read the focused sub-skill that matches the user's workflow, then use the linked references and scripts inside that sub-skill.

## Fast Routing

| User task | Read |
| --- | --- |
| Add ClearML to a training or evaluation script; log metrics, plots, artifacts, configs, models, or offline sessions | `sub-skills/experiment-tracking/SKILL.md` |
| Create, sync, version, retrieve, or troubleshoot datasets, storage URIs, `clearml-data`, `Dataset`, `StorageManager`, or HyperDataset/DataView | `sub-skills/data-storage/SKILL.md` |
| Configure ClearML, build `clearml-task` commands, launch code on agents, clone/enqueue tasks, import offline sessions, or debug queues | `sub-skills/remote-execution-cli/SKILL.md` |
| Build pipelines, HPO jobs, schedulers, triggers, controller tasks, or validate `clearml-param-search` JSON | `sub-skills/automation-pipelines/SKILL.md` |
| Use HTTP routers, local proxies, endpoint telemetry, service tasks, or optional `clearml[router]` dependencies | `sub-skills/routers-services/SKILL.md` |

## Package Entry Points

ClearML exposes these common imports:

```python
from clearml import Task, TaskTypes, Logger, Dataset, StorageManager
from clearml import InputModel, OutputModel, Model
from clearml import PipelineController, PipelineDecorator
from clearml.automation import HyperParameterOptimizer, TaskScheduler, TriggerScheduler
```

The package installs these user-facing CLIs:

- `clearml-init` for writing a local ClearML configuration file.
- `clearml-debug` for diagnostic configuration and token checks.
- `clearml-task` for creating or launching remote tasks on `clearml-agent` queues.
- `clearml-data` for dataset creation, sync, upload, finalize, verify, list, and retrieval.
- `clearml-param-search` for command-line hyperparameter search over a task or script.

## Installation And Optional Extras

Use the base package for tracking, datasets, CLIs, storage manager basics, and automation APIs:

```bash
pip install clearml
```

Install optional extras only for the workflow that needs them:

- `clearml[s3]` for S3 object storage integration.
- `clearml[gs]` for Google Cloud Storage integration.
- `clearml[azure]` for Azure Blob Storage integration.
- `clearml[router]` for HTTP router/proxy support through FastAPI, Uvicorn, and HTTPX.

Use `scripts/clearml_environment_check.py` for a read-only import, CLI, optional-extra, and credential-signal check. The script reports only whether secrets/configuration signals are present; it must not print secret values.

## Configuration And Credentials

Most live ClearML workflows need:

- A reachable ClearML server or hosted workspace.
- Credentials from `clearml-init`, a ClearML configuration file, or environment variables such as `CLEARML_API_HOST`, `CLEARML_API_ACCESS_KEY`, and `CLEARML_API_SECRET_KEY`.
- A `clearml-agent` polling the selected queue for remote execution, pipeline steps, HPO jobs, services, and schedulers.
- Storage credentials or configured provider defaults when using S3, Google Cloud Storage, Azure, or shared filesystem destinations.

For code that must run without credentials or network access, use the experiment-tracking sub-skill's offline mode pattern and later import the offline session when a server is available.

## Safety Defaults For Agents

- Prefer generating code, command plans, validation output, and checklists before running live ClearML operations.
- Do not run commands that create tasks, upload data, enqueue jobs, deploy routers, or start services unless the user explicitly wants side effects against a ClearML server.
- Do not echo API keys, secret keys, tokens, or credential file contents.
- Treat examples that require external datasets, queues, GPU frameworks, cloud credentials, or a running ClearML server as evidence, not as safe smoke tests.
- Use bundled scripts in this skill tree rather than relying on the original repository checkout.

## Root References

- `references/package-overview.md` summarizes ClearML imports, CLIs, optional extras, configuration, and workflow selection.
- `references/troubleshooting.md` covers cross-cutting install/import, credentials, server, queue, storage, optional extras, and privacy failures.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill.
- `references/repo-routing-metadata.json` is structured metadata consumed by the managed repo-skills-router import process.
