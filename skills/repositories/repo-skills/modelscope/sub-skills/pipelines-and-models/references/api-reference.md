# API Reference: Pipelines, Models, Registries, Configs

This reference summarizes ModelScope inference and registry surfaces evidenced by
its quick-tour examples, pipeline/model builders, pipeline/model base classes,
preprocessor/metric builders, output declarations, config loader, and local tests.
It is self-contained for future runtime use; do not rely on the source checkout.

## Imports and core entry points

```python
from modelscope.pipelines import pipeline, Pipeline
from modelscope.models import Model
from modelscope.preprocessors import Preprocessor
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys
```

Builder registries are public enough for custom registration and inspection:

```python
from modelscope.pipelines.builder import PIPELINES, add_default_pipeline_info
from modelscope.models.builder import MODELS, BACKBONES, HEADS, build_model
from modelscope.preprocessors.builder import PREPROCESSORS, build_preprocessor
from modelscope.metrics.builder import METRICS, build_metric
```

Registry construction expects a config dict with at least `type`; the registry
search is grouped by a task or field key. Missing registrations usually raise a
`KeyError` naming the registry, group, and type.

## `pipeline(...)` factory signature and semantics

Signature evidenced in this repository version:

```python
pipeline(
    task: str = None,
    model=None,                  # str | list[str] | Model | list[Model]
    preprocessor=None,
    config_file: str = None,
    pipeline_name: str = None,
    framework: str = None,
    device: str = None,
    model_revision: str = "master",
    ignore_file_pattern: list[str] = None,
    trust_remote_code: bool = False,
    **kwargs,
) -> Pipeline
```

Decision flow:

1. Either `task` or `pipeline_name` is required.
2. If `pipeline_name` is not supplied and `model` is a hub id or local model
   directory, ModelScope reads `configuration.json` to find `pipeline.type`.
3. For text-generation/chat models, the factory may prefer an LLM/external-engine
   pipeline unless overridden by kwargs such as `external_engine_for_llm=False`
   or an explicit `pipeline_name`.
4. If the model is a hub id, the factory normalizes it into a local cached model
   directory, passing `model_revision` and `ignore_file_pattern` to download.
5. If no explicit model is supplied, a task default is looked up from
   `DEFAULT_MODEL_FOR_PIPELINE`; if no default exists, the first registered
   pipeline for that task may be used with `model=None`.
6. If ModelScope cannot identify a registered pipeline, it may try sentence
   transformers for embedding tasks or Hugging Face `transformers.pipeline` when
   transformers is installed.
7. If `device` is omitted, the factory sets `device='gpu'`. For CPU-only and
   deterministic portable runs, pass `device='cpu'` explicitly.
8. Remaining `**kwargs` are merged into the pipeline config. Examples include
   `auto_collate=False`, `batch_size` at call time, `compile=True`, or
   pipeline-specific generation/image/audio parameters. The factory removes LLM
   helper kwargs when the selected pipeline is not `llm`.

`config_file` is passed into the constructed pipeline; the base `Pipeline` reads
that config when provided. The factory itself still needs a registry target from
`pipeline_name` or another path.

## `Pipeline` base call flow

A custom pipeline usually subclasses `modelscope.pipelines.Pipeline` and
implements or overrides:

```python
class MyPipeline(Pipeline):
    def preprocess(self, input, **preprocess_params): ...
    def forward(self, inputs, **forward_params): ...
    def postprocess(self, inputs, **postprocess_params): ...
```

The base `__call__` lifecycle is:

1. Prepare model on first inference when a model exists. For torch models, it
   calls `eval()`, places the model on the selected device, and optionally runs
   compile hooks.
2. Split call-time kwargs with `_sanitize_parameters(...)` into three dicts:
   `preprocess_params`, `forward_params`, and `postprocess_params`. The default
   implementation sends all kwargs to postprocess; override this method when
   custom call arguments must go to preprocessing or forward.
3. Route input shape:
   - a single input runs `_process_single`;
   - a Python list runs each element separately when `batch_size` is absent;
   - a Python list with `batch_size=N` runs `_process_batch` and returns a list;
   - `MsDataset` returns an iterator over per-row `_process_single` results;
   - LLM pipeline classes special-case a list as chat messages.
4. `_process_single` checks task input type, runs `preprocess -> forward ->
   postprocess`, then checks required output keys.
5. Torch forward is wrapped in `torch.no_grad()` and device-placement context;
   if `auto_collate` is true, the base collate function attempts to place arrays
   or tensors on the selected device.
6. `_process_batch` preprocesses each element, merges per-sample dicts into a
   batch dict, runs forward once per chunk, slices each output back per example,
   and postprocesses each per-example output.

Important defaults:

- `postprocess` is abstract in practice; leaving it unimplemented raises
  `NotImplementedError` or abstract-class errors.
- The default `preprocess` delegates to `self.preprocessor(input, **params)` and
  asserts a preprocessor exists.
- The default `forward` delegates to `self.model(inputs, **params)` and asserts
  exactly one model exists.
- `_check_input` uses task declarations. Missing task input definitions warn once
  rather than failing.
- `_check_output` uses `TASK_OUTPUTS`. Missing task output definitions warn once;
  required output-key mismatches fail.

## `Model.from_pretrained(...)`

Signature evidenced in this repository version:

```python
Model.from_pretrained(
    model_name_or_path: str,
    revision: str = "master",
    cfg_dict=None,
    device: str = None,
    trust_remote_code: bool = False,
    **kwargs,
)
```

Behavior:

- A local path is used directly. A non-existing path is treated as a hub model id
  and downloaded with `snapshot_download`, respecting `revision` and
  `ignore_file_pattern` from kwargs.
- `cfg_dict`, when supplied, replaces the config read from the model directory.
- `task=...` in kwargs overrides the task from config. This is useful when a
  saved backbone or base model is reused for a task-specific head.
- `model.model.type` (or legacy `model_type`) identifies the registered model
  class. `Tasks.backbone` routes through the backbone builder.
- `use_hf=True|False|None` controls Hugging Face fallback. `None` auto-selects:
  ModelScope loading is used when supported; otherwise it may attempt HF loading.
- `device='gpu'` is normalized to CUDA-style device names for model loading;
  `device='cpu'` is the safe portable choice. `device_map`, `torch_dtype`, and
  `config` kwargs can be passed through for HF-compatible models.
- When a ModelScope model is built, any `pipeline` section in config is attached
  as `model.pipeline`, allowing `pipeline(task, model=model_obj)` to recover the
  intended pipeline type.

## Preprocessor and metric builders

`Preprocessor.from_pretrained(model_name_or_path, revision='master',
cfg_dict=None, preprocessor_mode='inference', trust_remote_code=False,
**kwargs)` reads a local or hub model config and builds the configured
preprocessor from `PREPROCESSORS` under the field returned by
`Tasks.find_field_by_task(task)`. If no `preprocessor.type` exists, it may use a
model/task preprocessor map or return `None` with warnings. It ignores large
model weight patterns during hub download.

`build_metric(metric_cfg, field='default', default_args=None)` wraps
`METRICS`; a string metric name is converted to `{'type': name}`. Metrics are
primarily routed to training/evaluation workflows, not inference.

## Config loading and trust boundary

`Config.from_file(path, trust_remote_code=False, model_dir=None)` accepts
`.json`, `.yaml`, `.yml`, and `.py` config files. JSON/YAML are passive data.
Python configs execute top-level code as modules, so this version refuses to
load a `.py` config from an untrusted model repo unless `trust_remote_code=True`
is passed. Avoid Python configs for smoke checks; prefer JSON.

`Config` supports attribute access (`cfg.model.type`), `safe_get('a.b', default)`,
`merge_from_dict(...)`, `dump(...)`, and `to_dict()`.

## Remote code and plugins

Use `trust_remote_code=False` by default. Turn it on only after a human or policy
has reviewed and accepted the model repository code/plugins. Trust gates appear
in multiple layers:

- `pipeline(...)` refuses configs with plugins or `allow_remote` unless
  `trust_remote_code=True` or the model owner group is trusted by ModelScope.
- `Model.from_pretrained(...)` refuses plugin-bearing configs unless trusted.
- `Pipeline.check_trust_remote_code(...)` and `Model.check_trust_remote_code(...)`
  are available for custom classes that need extra code execution gates.
- `Config.from_file(..., trust_remote_code=False)` refuses Python configs that
  would execute untrusted code.

Never pass `trust_remote_code=True` merely to work around a registry error. First
inspect the model/config provenance and identify whether plugins, `allow_remote`,
Python configs, or non-ModelScope code are actually required.
