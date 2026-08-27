# Experiment Tracking Workflows

Use these recipes to add ClearML tracking without changing the user's training semantics. Keep instrumentation near the executable entry point, keep config/model paths relative or user-provided, and preserve existing parser/config/framework behavior unless the user asks to simplify it.

## 1. Retrofit A Training Script

1. Add imports near the existing ML imports:

   ```python
   from clearml import Task, TaskTypes
   ```

2. Initialize ClearML at the start of `main()` or immediately after the `if __name__ == "__main__":` guard, before framework loggers, TensorBoard writers, Matplotlib plotting, checkpoint callbacks, or model saving are configured:

   ```python
   task = Task.init(
       project_name="my-project",
       task_name="train-model",
       task_type=TaskTypes.training,
       reuse_last_task_id=False,
       output_uri=True,
   )
   ```

3. Connect hyperparameters after defaults are known and before training uses them:

   ```python
   params = {"lr": 0.001, "batch_size": 64, "epochs": 10}
   params = task.connect(params, name="General")
   ```

4. Replace hard-coded values or pass the connected object into existing code. For dictionaries, use the returned dictionary because ClearML may wrap it to propagate changes.

5. Add explicit logger calls for important metrics:

   ```python
   logger = task.get_logger()
   logger.report_scalar("train", "loss", value=float(loss), iteration=global_step)
   logger.report_scalar("valid", "accuracy", value=float(acc), iteration=epoch)
   ```

6. Upload summary artifacts and flush at the end of short scripts:

   ```python
   task.upload_artifact("metrics", artifact_object=metrics, wait_on_upload=True)
   logger.flush(wait=True)
   task.close()
   ```

## 2. Preserve `argparse` And CLI Behavior

ClearML can capture parsers automatically when `Task.init(auto_connect_arg_parser=True)` is used. For simple scripts, initialize ClearML before `parser.parse_args()` and let auto-connect capture values.

```python
def main():
    task = Task.init(project_name="examples", task_name="train", reuse_last_task_id=False)

    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()
```

If a script already parses arguments before it can initialize ClearML, connect the resulting namespace explicitly:

```python
args = parser.parse_args()
task = Task.init(project_name="examples", task_name="train", auto_connect_arg_parser=False)
args = task.connect(args, name="Args")
```

Use a mapping to avoid logging secrets or bulky values:

```python
task = Task.init(
    project_name="examples",
    task_name="train",
    auto_connect_arg_parser={"api_key": False, "password": False},
)
```

## 3. Connect YAML, JSON, Or Python Configs

Call `connect_configuration` before reading the file so a remote worker can receive backend-edited config contents.

```python
from pathlib import Path
import yaml

config_path = task.connect_configuration(Path("configs/train.yaml"), name="train_yaml")
with open(config_path, "rt", encoding="utf-8") as handle:
    config = yaml.safe_load(handle)
```

For dictionaries or lists, pass the object directly:

```python
config = {"optimizer": {"name": "adam", "lr": 0.001}}
config = task.connect_configuration(config, name="train_config")
```

Use `ignore_remote_overrides=True` when a config is audit-only and must not be edited by remote execution.

## 4. Report Scalars, Text, Images, Tables, And Plots

Get one logger and pass it to helpers. Avoid constructing `Logger()` manually.

```python
logger = task.get_logger()
```

Recommended report calls:

```python
logger.report_scalar("train", "loss", value=float(loss), iteration=step)
logger.report_text(f"epoch={epoch} status=ok")
logger.report_table("validation", "summary", iteration=epoch, table_plot=summary_df)
logger.report_image("samples", "prediction", iteration=step, image=image_array)
logger.report_plotly("analysis", "roc", figure=plotly_figure, iteration=epoch)
logger.report_matplotlib_figure("analysis", "confusion", figure=plt, iteration=epoch)
```

Practical conventions:

- Use the same `title` for a graph group and different `series` names for train/valid/test curves.
- Use monotonically increasing `iteration` values; mix epoch and step axes only intentionally.
- For local image files, call `report_image(..., local_path="path/to/image.png")` rather than passing the path positionally.
- For short-lived scripts, call `logger.flush(wait=True)` before exit.

## 5. Upload Artifacts Safely

Use `upload_artifact` for static snapshots:

```python
ok = task.upload_artifact(
    name="metrics",
    artifact_object={"accuracy": float(acc), "loss": float(loss)},
    wait_on_upload=True,
    retries=2,
)
if not ok:
    raise RuntimeError("ClearML failed to upload metrics artifact")
```

Supported objects include paths, folders, wildcards, dictionaries, pandas DataFrames, NumPy arrays, PIL images, and pickled objects when `auto_pickle=True`. Prefer explicit serialization for custom classes instead of enabling pickle by default.

Use `register_artifact` only for a pandas DataFrame that should be watched and dynamically synchronized:

```python
task.register_artifact("training_samples", dataframe, metadata={"split": "train"})
```

If artifact uploads fail, verify `Task.init(output_uri=True)` or a real storage URI, ClearML file-server reachability, and cloud storage credentials/extras.

## 6. Track Models Explicitly

For supported frameworks, let auto-connect capture native save/load behavior first:

```python
task = Task.init(
    project_name="examples",
    task_name="train",
    auto_connect_frameworks={"pytorch": ["*.pt", "*.pth"], "matplotlib": True},
    output_uri=True,
)
```

For manual model registration:

```python
from clearml import OutputModel

output_model = OutputModel(task=task, name="classifier")
output_model.update_labels({"cat": 0, "dog": 1})
output_model.update_weights(weights_filename="model.pt")
```

For a preexisting model input:

```python
from clearml import InputModel

input_model = InputModel(model_id=model_id)
task.connect(input_model, name="pretrained")
```

Use `OutputModel.set_upload_destination(uri)` if the model needs a destination different from the task-level `output_uri`.

## 7. Offline Fallback For No Credentials Or No Network

Wrap initialization with an explicit offline option controlled by the user, environment, or CLI flag:

```python
from clearml import Task

if args.clearml_offline:
    Task.set_offline(True)

task = Task.init(project_name="examples", task_name="train", reuse_last_task_id=False)

try:
    train()
finally:
    task.close()
    if args.clearml_offline:
        offline_session = task.get_offline_mode_folder()
        Task.set_offline(False)
        print(f"ClearML offline session saved: {offline_session}")
```

Do not import the offline session automatically unless credentials/network are available and the user wants upload in the same run. Import later with:

```python
Task.import_offline_session(offline_session)
```

## 8. Avoid Duplicate Tasks On Repeated Runs

Default `reuse_last_task_id=True` can surprise users because recent development tasks with the same project/name may be reused. Choose one policy explicitly:

- New task every local run: `reuse_last_task_id=False`.
- Continue a known task: `reuse_last_task_id="task-id"`, `continue_last_task=True`.
- Continue and offset metric iterations manually: `continue_last_task=<integer offset>`.

When retrofitting scripts, prefer `reuse_last_task_id=False` unless the user specifically asked for resume/continue semantics.

## 9. Framework Auto-Logging Choices

Use `auto_connect_frameworks=True` for default broad capture, or a mapping when the user needs tighter behavior:

```python
task = Task.init(
    project_name="examples",
    task_name="train",
    auto_connect_frameworks={
        "matplotlib": True,
        "tensorboard": {"report_hparams": False},
        "pytorch": ["*.pt", "*.pth"],
        "scikit": True,
        "detect_repository": True,
    },
)
```

Disable noisy or unsupported integrations with `False`, but keep explicit `Logger` reports for core metrics so tracking does not depend entirely on optional framework patches.

## 10. Validate Before Handing Back

Run the bundled static helper:

```bash
python scripts/validate_tracking_script.py train.py
```

Use `--json` when integrating into another checker:

```bash
python scripts/validate_tracking_script.py train.py --json
```

Review warnings for initialization order, missing imports, missing `project_name`/`task_name`, default reuse behavior, artifact upload without an `output_uri`, logger calls before `Task.init`, offline-mode misuse, and missing final flush/close in short scripts.

## 11. PyTorch-Like End-To-End Pattern

A robust retrofit for a PyTorch-like script typically includes:

```python
from clearml import Task, TaskTypes

Task.set_offline(args.clearml_offline)
task = Task.init(
    project_name="vision",
    task_name="resnet-train",
    task_type=TaskTypes.training,
    reuse_last_task_id=False,
    output_uri=True,
    auto_connect_frameworks={"pytorch": ["*.pt", "*.pth"], "matplotlib": True},
)
config_path = task.connect_configuration("configs/train.yaml", name="train_config")
params = task.connect(vars(args), name="Args")
logger = task.get_logger()
```

Then add `logger.report_scalar` in train/validation loops, `logger.report_image` for representative predictions, `task.upload_artifact` for final metrics/config snapshots, and `OutputModel` for model weights if framework auto-connect does not capture them.
