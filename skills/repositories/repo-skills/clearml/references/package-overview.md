# ClearML Package Overview

This reference summarizes the ClearML package surfaces that are shared across sub-skills.

## What ClearML Provides

ClearML is a Python SDK and CLI suite for:

- Experiment tracking: tasks, hyperparameters, source/version capture, logs, metrics, plots, artifacts, and models.
- Data management: versioned datasets, local cache, remote storage, dataset parents, and CLI operations.
- Remote execution: task creation, repository/script packaging, queues, Docker/runtime metadata, and `clearml-agent` launch flows.
- Automation: pipelines, decorated component steps, HPO, schedulers, triggers, and controller/service tasks.
- Routers/services: optional HTTP proxy routing, endpoint telemetry, and service-style ClearML tasks.

## Common Imports

```python
from clearml import Task, TaskTypes, Logger
from clearml import Dataset, StorageManager
from clearml import InputModel, OutputModel, Model
from clearml import PipelineController, PipelineDecorator
from clearml.automation import HyperParameterOptimizer, TaskScheduler, TriggerScheduler
```

Use `TaskTypes` to choose the task category: `training`, `testing`, `inference`, `data_processing`, `application`, `monitor`, `controller`, `optimizer`, `service`, `qc`, or `custom`.

## Console Scripts

- `clearml-init`: creates a ClearML configuration file interactively or at a selected path.
- `clearml-debug`: inspects token/configuration-related state.
- `clearml-task`: creates or launches a task from a repo, folder, script, module, base task, or offline session.
- `clearml-data`: creates, updates, uploads, finalizes, verifies, lists, compares, and retrieves datasets.
- `clearml-param-search`: runs HPO over a base task or script with JSON-encoded parameter ranges.

Prefer each sub-skill's bundled command builder or validator before running live CLI calls.

## Optional Extras

The base install covers the main SDK and CLIs. Extras are workflow-specific:

| Extra | Needed for |
| --- | --- |
| `s3` | S3 dataset/model/artifact storage integration |
| `gs` | Google Cloud Storage integration |
| `azure` | Azure Blob Storage integration |
| `router` | HTTP router/local proxy support using FastAPI, Uvicorn, and HTTPX |

Do not install every extra by default. Add only the extra tied to the user's requested storage or router workflow.

## Credential And Server Model

Live ClearML operations generally need a server URL and API credentials. They can come from `clearml-init`, a ClearML configuration file, or environment variables such as `CLEARML_API_HOST`, `CLEARML_API_ACCESS_KEY`, and `CLEARML_API_SECRET_KEY`.

Remote execution also needs a `clearml-agent` connected to the selected queue. Dataset upload/download and model/artifact upload need the server files service or configured object storage credentials.

## Offline Mode

Offline experiment capture is useful when credentials or network access are not available. Set offline mode before `Task.init`, close the task after reporting, and import the offline session later. Use the experiment-tracking sub-skill for the exact pattern.

## Choosing A Workflow

- If the user is modifying a Python training/evaluation script, start with experiment tracking.
- If the task has dataset versions, folders, storage URIs, or `clearml-data`, start with data storage.
- If the task is about queues, agents, `clearml-task`, Docker, requirements, or remote code launch, start with remote execution.
- If the task has DAG steps, HPO, recurring jobs, triggers, or pipeline artifacts, start with automation pipelines.
- If the task has HTTP routes, proxy ports, endpoint telemetry, or FastAPI/uvicorn/httpx, start with routers/services.
