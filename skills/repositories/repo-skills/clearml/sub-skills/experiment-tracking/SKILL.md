---
name: experiment-tracking
description: "Instrument Python ML and data scripts with ClearML Task experiment
  tracking, Logger reports, artifacts, configs, models, offline mode, and
  tracking validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Experiment Tracking

Use this sub-skill when a user asks to add, review, or troubleshoot ClearML experiment tracking in a Python script. It covers `Task.init`, `TaskTypes`, connected hyperparameters/configuration, `Logger` reports, artifacts, model metadata, framework auto-logging, offline mode, task reuse, `output_uri`, and static validation.

## When To Use

- Retrofit a training/evaluation script with ClearML tracking while preserving existing `argparse`, config files, framework logging, and model save paths.
- Add explicit reports for scalars, text, images, tables, Plotly, Matplotlib, artifacts, or model metadata.
- Make a script work without credentials by using offline mode and later import the offline session.
- Diagnose missing metrics, duplicate task reuse, upload failures, bad `output_uri`, or logger calls made before `Task.init`.
- Validate a candidate script without importing the user code or contacting a ClearML server.

## Route Elsewhere

- Use `../data-storage/SKILL.md` for `Dataset`, `StorageManager`, `clearml-data`, dataset versioning, cache/download, and object-storage data movement.
- Use `../remote-execution-cli/SKILL.md` for `clearml-task`, `Task.create`, `Task.enqueue`, agents, queues, Docker execution, and remote execution packaging.
- Use `../automation-pipelines/SKILL.md` for `PipelineController`, `PipelineDecorator`, HPO, schedulers, triggers, and pipeline orchestration.
- Use `../routers-services/SKILL.md` for `Task.get_http_router()`, service endpoints, FastAPI/router integration, and the `clearml[router]` extra.

## Essential References

- Read `references/api-reference.md` for verified tracking/reporting signatures, parameter notes, and method-selection guidance.
- Read `references/workflows.md` for concrete instrumentation recipes, logging examples, offline fallback, and validation flow.
- Read `references/troubleshooting.md` for symptoms, likely causes, and fixes across credentials, config, uploads, reuse, offline mode, framework auto-connect, and logger misuse.
- Run `scripts/validate_tracking_script.py --help` to inspect a Python file statically for likely ClearML tracking issues.

## Minimal Instrumentation Pattern

Place `Task.init` near the start of executable code, before training starts and before framework writers, plots, or model checkpoints are created.

```python
from clearml import Task, TaskTypes

task = Task.init(
    project_name="my-project",
    task_name="train-model",
    task_type=TaskTypes.training,
    reuse_last_task_id=False,
    output_uri=True,
)
```

Use `reuse_last_task_id=False` for most repeatable local training runs so previous outputs are not overwritten. Use `continue_last_task=True` only when intentionally appending to an existing task, and prefer an explicit `reuse_last_task_id="<task-id>"` when continuing a known task.

## Connect Inputs

- Let `Task.init(auto_connect_arg_parser=True)` capture common CLI parsers automatically, or pass a dictionary to include/exclude specific arguments.
- Use `task.connect(params, name="General")` for dictionaries, `argparse.Namespace`, `TaskParameters`, model objects, or simple config classes.
- Use `task.connect_configuration(config_path_or_dict, name="train_config")` before reading a JSON/YAML/config file so remote overrides can replace the file or dictionary.
- Use `ignore_remote_overrides=True` on `connect` or `connect_configuration` only when the script must not accept UI/backend overrides.

## Report Outputs

- Get a logger with `logger = task.get_logger()` or, inside helper functions after initialization, `Task.current_task().get_logger()`.
- Report scalar curves with `logger.report_scalar(title="train", series="loss", value=loss, iteration=step)`.
- Report text with `logger.report_text("message")`; stdout, stderr, and Python logging are also captured when `auto_connect_streams=True`.
- Report images/plots/tables with `report_image`, `report_matplotlib_figure`, `report_plotly`, and `report_table`.
- Upload one-time artifacts with `task.upload_artifact(name="metrics", artifact_object=metrics, wait_on_upload=True)` when later code depends on upload success.
- Register a live pandas DataFrame with `task.register_artifact(...)` only when dynamic synchronization is intended; otherwise prefer `upload_artifact`.

## Model Tracking

- Let framework auto-connect track supported model files when possible through `auto_connect_frameworks=True` or a framework-specific mapping such as `{"pytorch": ["*.pt", "*.pth"]}`.
- Use `OutputModel(task=task, name="model")` when manually registering or uploading model weights.
- Call `output_model.update_labels(labels)` for class mappings and `output_model.update_weights(weights_filename="model.pt")` for local weights; use `register_uri="..."` for an existing remote model URL.
- Use `InputModel(model_id=...)` or `InputModel(name=..., project=...)` for existing model inputs, then connect it with `task.connect(input_model, name="pretrained")` if the task should record it.

## Offline And Credentials Pattern

Use offline mode when the script must run without credentials or network access:

```python
from clearml import Task

Task.set_offline(True)
task = Task.init(project_name="offline", task_name="train")
# training and reporting here
task.close()
Task.set_offline(False)
Task.import_offline_session(task.get_offline_mode_folder())
```

Set offline mode before `Task.init`. Close the task before switching back online. Do not use `Task.create` for offline experiment capture.

## Validation Checklist

- `from clearml import Task` exists and `Task.init(...)` is called exactly once for the main process.
- `Task.init` has stable `project_name`, `task_name`, and a suitable `task_type` from `TaskTypes`.
- `Task.init` happens before parser parsing, framework logger/writer creation, Matplotlib plotting, model checkpoint setup, and `Logger` reporting.
- Repeated local runs use `reuse_last_task_id=False`, unless intentional reuse/continue behavior is documented.
- Artifact/model uploads have `output_uri=True` or a configured storage URI when server file storage is not enough.
- Offline fallback sets `Task.set_offline(True)` before `Task.init` and closes/imports the session when appropriate.
- Manual reports use `task.get_logger()` or `Task.current_task().get_logger()` after initialization, not `Logger()` construction.
- The script still runs without optional ML frameworks if the requested change is limited to ClearML instrumentation.

## Static Helper

Run the bundled validator against a candidate script:

```bash
python scripts/validate_tracking_script.py path/to/train.py
```

The helper parses the file with `ast`, never imports the script, never imports ClearML, and never contacts a server. Treat warnings as review prompts; it cannot prove runtime server connectivity, storage credentials, optional framework installation, or remote override behavior.
