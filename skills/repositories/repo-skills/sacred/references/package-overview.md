# Sacred Package Overview

## When to read

Read this when deciding whether Sacred is the right package for a Python experiment-management task, or when you need the shared context behind the sub-skills.

## What Sacred does

Sacred helps Python projects make experiments configurable, observable, and reproducible. It adds a structured layer around user experiment code so runs can:

- collect configuration and command-line overrides;
- inject config values into captured functions by parameter name;
- run named commands and variants from Python or a generated CLI;
- save run metadata, stdout, artifacts, resources, metrics, dependencies, sources, and host information through observers;
- control randomness through a root seed and deterministic per-call seeds.

Sacred does not train models by itself. It wraps user training, evaluation, or data-processing code and records the metadata needed to understand and reproduce those runs.

## Public package surface

Import the main objects from `sacred`:

```python
from sacred import Experiment, Ingredient, SETTINGS, cli_option
from sacred.observers import FileStorageObserver
```

Common classes and helpers:

- `Experiment`: top-level experiment/ingredient-like object with `@config`, `@main`, `@automain`, `@capture`, `@command`, `run`, `run_commandline`, `add_artifact`, `open_resource`, `log_scalar`, and observer lists.
- `Ingredient`: reusable configurable component with its own config, captured functions, commands, hooks, and nested ingredients.
- `Run`: per-execution object returned by `Experiment.run`; available inside captured functions through `_run`.
- `SETTINGS`: global settings groups for config behavior, command line behavior, capture mode, discovery, heartbeat interval, and host info.
- `sacred.observers`: built-in observer classes for local files, MongoDB, SQL, TinyDB, queue wrapping, cloud storage, and notifications.

## Optional dependencies and services

The base install covers core experiments, configuration, CLI parsing, dependency/source capture, and local file observation. Optional workflows need extra packages or services:

| Workflow | Extra requirements | Notes |
|---|---|---|
| MongoDB observer | `pymongo` and a reachable MongoDB service | Credentials and network policy are user/environment-specific. |
| SQL observer | `sqlalchemy` and a database URL | SQLite can be local; other databases need services and drivers. |
| TinyDB observer/reader | `tinydb`, `tinydb-serialization`, `hashfs` | Local JSON/hashfs storage; useful when querying local runs. |
| S3/GCS observers | `boto3` or `google-cloud-storage` plus credentials | Do not run without explicit bucket/credential setup. |
| Slack/Telegram observers | notification packages or APIs plus secrets | Keep webhook URLs and bot tokens out of code and logs. |
| Neptune integration | Neptune Sacred integration packages and API token/project | External package integration, not a Sacred core observer class. |
| TensorFlow summary tracking | TensorFlow compatible with the environment | Optional `sacred.stflow` helper; not required for base Sacred. |

## Sub-skill boundaries

- `experiment-core` owns Python experiment/ingredient/run structure and in-process execution.
- `configuration-and-cli` owns config definitions, config updates, built-in commands, custom commands/options, and command-line quoting.
- `observers-and-logging` owns observers, metrics, info, resources, artifacts, and stored run layouts.
- `reproducibility-and-capture` owns seeds, dependency/source discovery, settings, stdout/stderr capture, clean-repo enforcement, and TensorFlow capture notes.

Use the root [SKILL.md](../SKILL.md) route map to enter the most specific sub-skill first.

## Safe validation pattern

For a new environment or project integration:

1. Run the root environment check script.
2. Run the relevant sub-skill probe script for the workflow being used.
3. Create a tiny local `FileStorageObserver` run before adding external observers.
4. Inspect `print_config` and `print_dependencies` before running expensive code.
5. Document which optional dependencies and services were actually verified.
