# Exporters and CLI troubleshooting

Use this guide for Optimum CLI, TasksManager, exporter config, and accelerated pipeline failures.

## `optimum-cli export onnx` is missing after base install

Likely cause: base Optimum registers only the `export` parent command. The `onnx` child command is supplied by the ONNX partner package.

Check:

```bash
optimum-cli --help
optimum-cli export --help
python scripts/probe_optimum_cli.py
python -m pip show optimum optimum-onnx onnxruntime
```

Recovery:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnx]"
# or, if ONNX Runtime inference/optimization is needed:
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime]"
```

Then re-run:

```bash
python scripts/probe_optimum_cli.py --run-env
```

If still absent, make sure `python`, `pip`, and `optimum-cli` point to the same environment.

## `ModuleNotFoundError: No module named 'requests'` when importing `optimum.exporters.tasks`

`TasksManager` imports `requests.exceptions.ConnectionError`. Some minimal base installs may not include `requests` even though exporter inspection needs it.

Recovery:

```bash
python -m pip install requests
python scripts/tasks_manager_probe.py
```

## `optimum.pipelines.pipeline` raises missing partner package `ImportError`

Likely cause: no accelerated backend is installed. Base Optimum only dispatches.

Symptoms include an error asking for one of:

- `optimum-onnx[onnxruntime]`
- `optimum-intel[openvino]`

Recovery:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime]"
# or
python -m pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
```

For plain PyTorch/Transformers inference without accelerated backends, use `transformers.pipeline` instead of `optimum.pipelines.pipeline`.

## `onnxruntime` is missing even though `optimum-onnx` is installed

ONNX export support and ONNX Runtime execution are separate dependency surfaces. A package may provide exporter config/CLI registration without the runtime library needed for ORT inference or optimization.

Check:

```bash
python - <<'PY'
from optimum.utils.import_utils import is_optimum_onnx_available, is_onnxruntime_available
print("optimum-onnx", is_optimum_onnx_available())
print("onnxruntime", is_onnxruntime_available())
PY
```

Recovery:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime]"
```

Use the GPU extra only when the environment has the expected CUDA/runtime compatibility:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime-gpu]"
```

## `accelerator="ipex"` fails

This dispatcher treats `ipex` as deprecated and unsupported.

Recovery: use OpenVINO instead:

```python
from optimum.pipelines import pipeline
pipe = pipeline("text-classification", accelerator="ov")
```

If the user specifically needs Intel Extension for PyTorch behavior, route to the relevant Intel partner package guidance rather than this base dispatcher.

## Invalid task names

Symptoms:

- `KeyError: Unknown task: ...`
- `ValueError: ... doesn't support task ...`
- CLI errors asking for `--task`

Recovery:

```bash
python scripts/tasks_manager_probe.py --task text-classification
```

or in Python:

```python
from optimum.exporters.tasks import TasksManager
print(sorted(TasksManager.get_all_tasks()))
print(TasksManager.map_from_synonym("causal-lm"))
```

Use canonical task names when possible. For local directories and offline work, pass `--task` explicitly; local directory task inference is not generally available.

## Unknown backend or model type in TasksManager

Symptoms:

- `KeyError` says a model type is not supported for a library.
- `KeyError` says a backend is not supported for a model type.
- `get_exporter_config_constructor()` cannot find a constructor.

Likely causes:

- The partner exporter package was not installed or imported.
- The backend config was not registered for that model type.
- The selected task is unsupported for that model/backend pair.

Recovery:

```bash
python scripts/tasks_manager_probe.py --backend onnx --model-type bert --task text-classification
```

If adding a backend in code, use `TasksManager.create_register("backend-name", overwrite_existing=...)` and decide explicitly whether overwriting existing registrations is allowed.

## Custom backend overwrite behavior surprises

`overwrite_existing=False` is the default. If a config already exists for the same model/backend/task, a new registration is skipped silently by design.

Use:

```python
register = TasksManager.create_register("my-backend", overwrite_existing=True)
```

only when replacing an existing config is intentional. The bundled probe can demonstrate both behaviors safely in memory:

```bash
python scripts/tasks_manager_probe.py --demo-registration
```

## Namespace command does not appear in CLI help

Check these conditions:

- The package contributing the command is installed in the same environment as `optimum-cli`.
- The registration module is in the `optimum.commands.register` namespace.
- The namespace directory does not contain `__init__.py`.
- The module defines `REGISTER_COMMANDS`.
- Each command class subclasses `BaseOptimumCLICommand` and has `COMMAND = CommandInfo(...)`.
- Tuple registrations use an existing parent command class, for example `(MyCommand, ExportCommand)`.

Run:

```bash
python scripts/probe_optimum_cli.py --json
```

## Network or cache is needed unexpectedly

These operations may contact the Hugging Face Hub or need cached metadata/weights:

- `TasksManager.infer_library_from_model("model-id")`
- `TasksManager.infer_task_from_model("model-id")`
- `TasksManager.get_model_from_task(...)`
- `optimum.pipelines.pipeline(...)` with a model id or default model
- real `optimum-cli export ...` commands

Recovery:

- Use local model directories and pass explicit `task`, `library_name`, and `framework`.
- Confirm cache availability before offline runs.
- Ask the user before enabling network access, credentials, or model downloads.
- Avoid `trust_remote_code=True` unless the user approves the trust boundary.

## Optional dependency imports fail

Optional libraries such as `diffusers`, `timm`, `sentence_transformers`, `optimum-onnx`, `optimum-intel`, `onnxruntime`, and `openvino` are not base requirements. Install only the stack required for the user's task.

When in doubt, keep the diagnosis at the routing layer: identify the missing partner package and avoid claiming that a backend has been fully verified until an actual partner runtime check has passed.
