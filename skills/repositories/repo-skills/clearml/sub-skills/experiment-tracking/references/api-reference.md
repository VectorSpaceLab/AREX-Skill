# Experiment Tracking API Reference

This reference summarizes the ClearML 2.1.9 tracking APIs future agents usually need when instrumenting a Python script. It is distilled from installed API inspection plus source docstrings.

## Public Imports

```python
from clearml import Task, TaskTypes, Logger, InputModel, OutputModel, Model
```

`TaskTypes` is exported as `Task.TaskTypes`. Valid task types include `training`, `testing`, `inference`, `data_processing`, `application`, `monitor`, `controller`, `optimizer`, `service`, `qc`, and `custom`.

## Task Creation And Lookup

### `Task.init`

Verified signature:

```python
Task.init(
    project_name: Optional[str] = None,
    task_name: Optional[str] = None,
    task_type: Task.TaskTypes = TaskTypes.training,
    tags: Optional[Sequence[str]] = None,
    reuse_last_task_id: Union[bool, str] = True,
    continue_last_task: Union[bool, str, int] = False,
    output_uri: Union[str, bool, None] = None,
    auto_connect_arg_parser: Union[bool, Mapping[str, bool]] = True,
    auto_connect_frameworks: Union[bool, Mapping[str, Union[bool, str, list]]] = True,
    auto_resource_monitoring: Union[bool, Mapping[str, Any]] = True,
    auto_connect_streams: Union[bool, Mapping[str, bool]] = True,
    deferred_init: bool = False,
) -> Task
```

Parameter notes:

- `project_name` and `task_name`: use stable, descriptive names. If omitted, ClearML derives names from the repository or script, which is convenient but less explicit for generated code.
- `task_type`: use `TaskTypes.training` for training, `TaskTypes.testing` for evaluation, `TaskTypes.inference` for inference scripts, `TaskTypes.data_processing` for preprocessing, and route controllers/pipelines elsewhere.
- `tags`: list of strings for filtering tasks in the UI.
- `reuse_last_task_id`: default `True` can overwrite a recent same-project/name development task by reusing the ID and clearing prior outputs. Use `False` for repeated local runs unless the user explicitly wants reuse.
- `continue_last_task`: appends to an existing task and offsets metric iterations. Use with care; a string value also supplies the task ID to continue.
- `output_uri`: `True` uses the default file server. A URI such as `s3://bucket/path`, `gs://bucket/path`, `azure://...`, or a shared path uploads artifacts/models there if storage credentials and extras are configured. `False` disables default upload destinations.
- `auto_connect_arg_parser`: `True` captures supported parsers automatically; a mapping can include or exclude specific names, with `"*": False` as a default-exclude pattern.
- `auto_connect_frameworks`: `True` patches supported frameworks. A mapping can limit frameworks or model-file wildcards, for example `{"pytorch": ["*.pt", "*.pth"], "matplotlib": True}`.
- `auto_resource_monitoring`: controls CPU/GPU/resource plots. Disable only when the user explicitly wants no resource monitoring.
- `auto_connect_streams`: controls stdout, stderr, and logging capture. A mapping can separately control `stdout`, `stderr`, and `logging`.
- `deferred_init`: returns before backend initialization completes; use only when startup latency matters and early auto-logged events can be missed.

### Related task methods

```python
Task.current_task() -> Task
Task.get_task(task_id=None, project_name=None, task_name=None, tags=None, allow_archived=True, task_filter=None) -> Task
Task.clone(source_task=None, name=None, comment=None, parent=None, project=None) -> Task
Task.close(self) -> None
Task.flush(self, wait_for_uploads: bool = False) -> bool
Task.mark_started(self, force: bool = False) -> None
```

Use `Task.current_task()` inside helper functions only after `Task.init`. Use `Task.get_task` and `Task.clone` for existing task references; remote execution and enqueueing are covered by the remote-execution sub-skill.

## Connecting Parameters And Configurations

### `Task.connect`

Verified signature:

```python
Task.connect(self, mutable: Any, name: Optional[str] = None, ignore_remote_overrides: bool = False) -> Any
```

Supported objects include `argparse` objects, dictionaries, `TaskParameters`, `InputModel`, `OutputModel`, classes, and class instances. Dictionaries are returned as a proxy-like dictionary so later assignments can be propagated. For dictionaries and `TaskParameters`, `name` controls the hyperparameter section name. Set `ignore_remote_overrides=True` only when a remote worker must not apply UI/backend parameter edits.

Common patterns:

```python
params = {"lr": 0.001, "batch_size": 64}
params = task.connect(params, name="General")

args = parser.parse_args()
args = task.connect(args, name="Args")
```

Prefer connecting parser objects before or near parsing when adapting scripts with heavy CLI usage. If relying on `auto_connect_arg_parser=True`, avoid duplicate manual `task.connect(args)` unless the user wants a second explicit section.

### `Task.connect_configuration`

Source-verified signature:

```python
Task.connect_configuration(
    self,
    configuration: Union[Mapping, list, Path, str],
    name: Optional[str] = None,
    description: Optional[str] = None,
    ignore_remote_overrides: bool = False,
) -> Union[dict, Path, str]
```

Use this before reading a config file. For file inputs, the returned path is the path the script should read because remote execution can replace it with the UI/backend-edited version. Local config paths should be relative when intended for remote execution.

```python
config_path = task.connect_configuration("configs/train.yaml", name="train_yaml")
with open(config_path, "rt", encoding="utf-8") as handle:
    config = yaml.safe_load(handle)
```

## Logging API

Get the logger from the initialized task:

```python
logger = task.get_logger()
# or inside helpers after Task.init:
logger = Task.current_task().get_logger()
```

Important verified signatures:

```python
Logger.report_scalar(self, title: str, series: str, value: float, iteration: int) -> None
Logger.report_text(self, msg: str, level: int = 20, print_console: bool = True, *args: Any, **_: Any) -> None
Logger.report_image(self, title: str, series: str, iteration: Optional[int] = None, local_path: Optional[str] = None, image=None, matrix=None, max_image_history: Optional[int] = None, delete_after_upload: bool = False, url: Optional[str] = None) -> None
Logger.report_table(self, title: str, series: str, iteration: Optional[int] = None, table_plot=None, csv: Optional[str] = None, url: Optional[str] = None, extra_layout: Optional[dict] = None, extra_data: Optional[dict] = None) -> None
Logger.report_plotly(self, title: str, series: str, figure, iteration: Optional[int] = None) -> None
Logger.report_matplotlib_figure(self, title: str, series: str, figure, iteration: Optional[int] = None, report_image: bool = False, report_interactive: bool = True) -> None
Logger.flush(self, wait: bool = False) -> bool
```

Additional source-verified methods useful for richer reporting:

```python
Logger.report_single_value(self, name: str, value: float) -> None
Logger.report_histogram(...)
Logger.report_line_plot(...)
Logger.report_scatter2d(...)
Logger.report_confusion_matrix(...)
Logger.report_surface(...)
Logger.report_media(...)
Logger.set_default_upload_destination(self, uri: str) -> None
Logger.get_default_upload_destination(self) -> str
```

Guidance:

- Use `title` for the metric/plot group and `series` for the curve or variant within that group.
- Always pass deterministic `iteration` values for scalar/image/table/plot reporting so charts align with training steps or epochs.
- Use `report_image` with `image`, `matrix`, `local_path`, or `url`; do not pass a raw image path as a positional value without naming `local_path`.
- Use `logger.flush(wait=True)` or `task.flush(wait_for_uploads=True)` at the end of short scripts when uploaded reports/artifacts must be available before process exit.

## Artifacts

### `Task.upload_artifact`

Verified signature:

```python
Task.upload_artifact(
    self,
    name: str,
    artifact_object: Union[str, Mapping, pandas.DataFrame, numpy.ndarray, PIL.Image.Image, Any],
    metadata: Optional[Mapping] = None,
    delete_after_upload: bool = False,
    auto_pickle: Optional[bool] = None,
    preview: Any = None,
    wait_on_upload: bool = False,
    extension_name: Optional[str] = None,
    serialization_function: Optional[Callable[[Any], Union[bytes, bytearray]]] = None,
    retries: int = 0,
    sort_keys: bool = True,
) -> bool
```

Supported static artifact inputs include local file/folder/wildcard paths, dictionaries, pandas DataFrames, NumPy arrays, PIL images, and arbitrary objects when `auto_pickle=True`. Use `wait_on_upload=True` for scripts that exit immediately or depend on upload completion. Use `retries` for flaky storage backends.

### Registered artifacts

Source-verified signatures:

```python
Task.register_artifact(self, name: str, artifact: pandas.DataFrame, metadata: Dict = None, uniqueness_columns: Union[bool, Sequence[str]] = True) -> None
Task.unregister_artifact(self, name: str) -> None
Task.get_registered_artifacts(self) -> Dict[str, Artifact]
```

Registered artifacts dynamically synchronize a pandas DataFrame. They are not general-purpose static uploads. For one-time files, folders, dictionaries, arrays, or images, use `upload_artifact`.

## Model Objects

Verified constructors:

```python
InputModel(model_id: Optional[str] = None, name: Optional[str] = None, project: Optional[str] = None, tags: Optional[Sequence[str]] = None, only_published: bool = False)
OutputModel(task: Optional[Task] = None, config_text: Optional[str] = None, config_dict: Optional[dict] = None, label_enumeration: Optional[Mapping[str, int]] = None, name: Optional[str] = None, tags: Optional[List[str]] = None, comment: Optional[str] = None, framework=None, base_model_id: Optional[str] = None)
Model(model_id: str)
```

Useful model methods from source:

```python
InputModel.connect(self, task: Task, name: Optional[str] = None, ignore_remote_overrides: bool = False) -> None
OutputModel.connect(self, task: Task, name: Optional[str] = None, **kwargs: Any) -> None
OutputModel.set_upload_destination(self, uri: str) -> None
OutputModel.update_weights(self, weights_filename: Optional[str] = None, upload_uri: Optional[str] = None, target_filename: Optional[str] = None, auto_delete_file: bool = True, register_uri: Optional[str] = None, iteration: Optional[int] = None, update_comment: bool = True, is_package: bool = False, async_enable: bool = True) -> str
OutputModel.update_labels(self, labels: Mapping[str, int]) -> Any
OutputModel.update_design(...)
Model.publish(self) -> None
```

Use `OutputModel(task=task)` for manually tracked outputs and set an upload destination if `Task.init(output_uri=...)` is not enough. Pass either `weights_filename` or `register_uri` to `update_weights`, never both. Use `async_enable=False` when the script must block until model upload succeeds. Use `InputModel` for pretrained or previous models. For supported frameworks, try `auto_connect_frameworks` first because it can capture framework-native save/load patterns.

## Offline Mode

Source-verified signatures:

```python
Task.set_offline(cls, offline_mode: bool = False) -> None
Task.is_offline(cls) -> bool
Task.import_offline_session(cls, session_folder_zip: str, previous_task_id: Optional[str] = None, iteration_offset: Optional[int] = 0) -> Optional[str]
```

Rules:

- Call `Task.set_offline(True)` before `Task.init`.
- Offline mode is supported for `Task.init`, not `Task.create`.
- Do not switch offline mode off while the current task is still open; call `task.close()` first.
- Use `Task.import_offline_session(task.get_offline_mode_folder())` after reconnecting online to upload an offline run.

## Framework Auto-Logging

`Task.init(auto_connect_frameworks=True)` enables auto-patching for supported frameworks and tools, including Matplotlib, TensorBoard/TensorBoardX, TensorFlow/Keras, PyTorch model files, XGBoost, scikit-learn/joblib, LightGBM, FastAI, Hydra, TensorFlow defines, MegEngine, CatBoost, Gradio, and repository detection. Use a mapping to disable noisy integrations or limit model-file patterns:

```python
task = Task.init(
    project_name="examples",
    task_name="train",
    auto_connect_frameworks={
        "pytorch": ["*.pt", "*.pth"],
        "matplotlib": True,
        "tensorboard": {"report_hparams": False},
        "detect_repository": True,
    },
)
```

If automatic framework capture is not visible, add explicit `Logger` calls first; then troubleshoot optional dependencies, initialization order, unsupported file extensions, and disabled auto-connect settings.
