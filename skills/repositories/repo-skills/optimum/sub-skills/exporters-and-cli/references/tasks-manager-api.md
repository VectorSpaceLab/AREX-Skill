# TasksManager and ExporterConfig API

This reference covers task/library/model/backend mapping APIs, task synonyms, backend config registration, exporter config constructor lookup, and the responsibilities of `ExporterConfig`.

## Mental model

`optimum.exporters.tasks.TasksManager` is the central router used by exporter backends. It maps:

- task name -> model loading class,
- library name -> supported task loaders,
- model type + exporter backend -> exporter config constructors,
- task synonyms -> canonical task names.

Supported library names in this base API are:

- `transformers`
- `diffusers`
- `timm`
- `sentence_transformers`

Optional libraries must be installed before their model classes or metadata can be imported. Do not assume those packages are present in a base Optimum environment.

## Safe task and synonym checks

These calls do not download models:

```python
from optimum.exporters.tasks import TasksManager

all_tasks = sorted(TasksManager.get_all_tasks())
canonical = TasksManager.map_from_synonym("causal-lm")          # "text-generation"
synonyms = TasksManager.synonyms_for_task("text-generation")
```

Common synonym examples:

| Synonym | Canonical task |
| --- | --- |
| `causal-lm` | `text-generation` |
| `causal-lm-with-past` | `text-generation-with-past` |
| `default` | `feature-extraction` |
| `masked-lm` | `fill-mask` |
| `seq2seq-lm` | `text2text-generation` |
| `sequence-classification` | `text-classification` |
| `summarization` | `text2text-generation` |
| `translation` | `text2text-generation` |
| `zero-shot-classification` | `text-classification` |
| `text-to-speech` | `text-to-audio` |
| `vision2seq-lm` | `image-to-text` |

Use `map_from_synonym()` before reporting an invalid task to a user.

## Model class lookup without downloads

For known task/library combinations, `get_model_class_for_task()` returns the loading class and does not load weights:

```python
model_cls = TasksManager.get_model_class_for_task(
    task="text-classification",
    framework="pt",
    model_type="bert",
    library="transformers",
)
```

Notes:

- Only framework `"pt"` is supported for export.
- If the task is unknown, `KeyError` lists valid task names for the selected library.
- Some tasks map to multiple auto classes; passing `model_type` helps choose the correct loader.
- Custom classes exist for special model/task pairs such as `pix2struct`, `visual_bert`, `vitpose`, and selected time-series model types.

## Library and task inference

`infer_library_from_model()` and `infer_task_from_model()` accept a model id/path, model instance, or model class.

Safe cases:

```python
library = TasksManager.infer_library_from_model(model_instance)
task = TasksManager.infer_task_from_model(model_class)
```

Potentially network/cache-dependent cases:

```python
library = TasksManager.infer_library_from_model("some-hub-model-id")
task = TasksManager.infer_task_from_model("some-hub-model-id")
```

For local directories, task inference is intentionally limited; pass `task` explicitly. In offline environments, pass `task`, `library_name`, and `framework` explicitly rather than relying on Hub metadata.

## Backend support lookup

Backend config maps are populated by backend packages. In a base install, maps for `onnx`, `openvino`, or other partner backends may be empty or unavailable.

```python
supported = TasksManager.get_supported_tasks_for_model_type(
    model_type="bert",
    exporter="onnx",
    library_name="transformers",
)
```

Expected failure surfaces:

- Unknown model type: `KeyError` listing supported model types for the library.
- Known model type but unknown backend: `KeyError` listing supported backends for that model type.
- Known backend but unsupported task: later constructor lookup raises `ValueError` with supported tasks.

If a user expects `onnx` but lookup fails, verify the ONNX partner package is installed and its exporter config module has been imported or registered.

## Exporter config constructor lookup

```python
constructor = TasksManager.get_exporter_config_constructor(
    exporter="onnx",
    model_type="bert",
    task="text-classification",
    library_name="transformers",
)
export_config = constructor(transformers.BertConfig())
```

Arguments:

- `exporter`: backend name such as `onnx`, `openvino`, or a custom backend name.
- `model`: model instance; optional if `model_type` is provided.
- `task`: defaults to `feature-extraction`; synonyms may be accepted when mapped to a supported task.
- `model_type`: architecture identifier; required when no model instance is provided.
- `model_name`: used only to improve error messages.
- `exporter_config_kwargs`: extra keyword arguments partially applied to the constructor.
- `library_name`: should be explicit; defaulting to `transformers` is deprecated and may become an error.

## Backend config registration

Use `create_register()` to register config constructors in memory:

```python
from optimum.exporters.tasks import TasksManager

register_for_backend = TasksManager.create_register("new-backend", overwrite_existing=False)

@register_for_backend("bert", "text-classification", library_name="transformers")
class BertNewBackendConfig(MyBackendExporterConfig):
    pass
```

Behavior:

- The decorator validates task names against `TasksManager.get_all_tasks()` after removing `-with-past` for validation.
- If the task is already registered for that model/backend and `overwrite_existing=False`, the existing constructor is kept.
- If `overwrite_existing=True`, the new constructor replaces the existing one.
- `-with-past` tasks require the config class to set `SUPPORTS_PAST = True`; otherwise registration raises `ValueError`.
- Registration mutates process-local `TasksManager` mappings. It does not write files or install packages.

Use the bundled probe to exercise this behavior safely:

```bash
python scripts/tasks_manager_probe.py --demo-registration
python scripts/tasks_manager_probe.py --demo-registration --include-error-examples
```

## ExporterConfig base responsibilities

`optimum.exporters.base.ExporterConfig` describes how a model is exported for a backend. Backend-specific config classes typically subclass it.

Constructor:

```python
ExporterConfig(config, task, int_dtype="int64", float_dtype="fp32")
```

Important class attributes:

| Attribute | Responsibility |
| --- | --- |
| `NORMALIZED_CONFIG_CLASS` | Normalizes model config fields used by dummy input generation and export metadata. |
| `DUMMY_INPUT_GENERATOR_CLASSES` | Ordered generators used by `generate_dummy_inputs()`. |
| `ATOL_FOR_VALIDATION` | Absolute tolerance for conversion validation, globally or per task. |
| `MIN_TORCH_VERSION` | Minimum supported PyTorch version for that config. |
| `MIN_TRANSFORMERS_VERSION` | Minimum supported Transformers version for that config. |
| `PATCHING_SPECS` | Optional operator/module patches needed before export. |

Important instance responsibilities:

- `inputs`: abstract property defining dynamic axes for input tensors.
- `outputs`: base common output names for tasks; backend subclasses commonly refine this into backend-specific axis mappings.
- `values_override`: disables `use_cache` when present unless overridden.
- `is_transformers_support_available`: checks installed Transformers version against the config minimum.
- `is_torch_support_available`: checks PyTorch availability and version against the config minimum.
- `generate_dummy_inputs(framework="pt", **shape_kwargs)`: builds dummy inputs for every declared input using the configured dummy input generators, `int_dtype`, and `float_dtype`.

## Probe script

Run:

```bash
python scripts/tasks_manager_probe.py
```

The probe:

- imports `TasksManager`,
- lists task counts and selected synonym mappings,
- checks safe model-class lookup,
- attempts the requested backend/model/task constructor lookup without downloading models,
- demonstrates registration and overwrite behavior when requested,
- reports missing partner backend config modules gracefully.
