# Workflows: Inference Pipeline and Registry Usage

Use these workflows for safe, reproducible ModelScope inference setup. They are
written to avoid accidental downloads or GPU assumptions unless explicitly
chosen.

## 1. Choose the pipeline construction path

### A. Default model for a task

Use when the user asks for the standard model for a known task and downloads are
allowed:

```python
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

p = pipeline(task=Tasks.word_segmentation, device='cpu')
result = p('今天天气不错，适合出去游玩')
```

Notes:

- This may download the default model for the task.
- If no default model is registered, ModelScope may choose the first registered
  pipeline for that task with `model=None`; many real pipelines still require a
  model and will fail.
- The factory defaults to `device='gpu'` when `device` is omitted. Always pass
  `device='cpu'` for CPU-only environments.

### B. Explicit hub model id

Use when the user gives a ModelScope model id and network/cache access is
allowed:

```python
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

p = pipeline(
    task=Tasks.text_classification,
    model='owner/model-name',
    model_revision='v1.0.0',          # pin when available
    device='cpu',
    ignore_file_pattern=['*.bin'],    # only if the workflow can omit files
    trust_remote_code=False,
)
```

Notes:

- `model_revision` pins the hub snapshot. Pin revisions for reproducibility.
- `ignore_file_pattern` is passed to downloads. Do not ignore weights/configs
  required by the selected pipeline.
- If config declares plugins or `allow_remote`, loading is refused unless
  `trust_remote_code=True` is explicitly accepted.

### C. Local model directory

Use when a model has already been downloaded or assembled locally:

```python
from modelscope.pipelines import pipeline

p = pipeline(
    task='image-classification',
    model='/path/to/local-model-dir',
    device='cpu',
    trust_remote_code=False,
)
```

A local model directory should contain `configuration.json` for ModelScope-native
loading. If it only contains Hugging Face-style files, `Model.from_pretrained` or
`pipeline` may use HF fallback when compatible dependencies are installed.

### D. Explicit `Model.from_pretrained` then pipeline

Use when custom loading kwargs are needed before pipeline construction:

```python
from modelscope.models import Model
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

model = Model.from_pretrained(
    '/path/to/local-model-dir',
    device='cpu',
    task=Tasks.text_classification,
    use_hf=False,
    trust_remote_code=False,
)
p = pipeline(task=Tasks.text_classification, model=model, device='cpu')
```

The pipeline factory can read `model.pipeline` if the loaded config has a
`pipeline` section. If the model object was constructed manually and lacks
pipeline metadata, pass `pipeline_name=...`.

### E. Explicit preprocessor

Use when preprocessing must be controlled or tested separately:

```python
from modelscope.preprocessors import Preprocessor
from modelscope.pipelines import pipeline

pre = Preprocessor.from_pretrained('/path/to/local-model-dir', trust_remote_code=False)
p = pipeline(
    task='text-classification',
    model='/path/to/local-model-dir',
    preprocessor=pre,
    device='cpu',
)
```

If a pipeline subclass overrides `preprocess`, it may ignore the supplied
preprocessor. If the config has no preprocessor, `Preprocessor.from_pretrained`
may return `None` with warnings.

### F. Local config file plus explicit pipeline name

Use for custom/local smoke tests where a ModelScope registry class is already
registered in the current Python process:

```python
p = pipeline(
    task='local-task',
    pipeline_name='local-pipeline',
    model=None,
    config_file='./local-model/configuration.json',
    device='cpu',
)
```

`config_file` is read by the base `Pipeline`; it does not by itself register a
pipeline class. Use a JSON config for safety. A Python config may execute code
and is gated by `trust_remote_code` in the config loader.

### G. Custom pipeline name without model downloads

For deterministic tests, register a simple in-process pipeline and instantiate
with `model=None` and `device='cpu'`. The bundled smoke script demonstrates this
pattern.

## 2. Call the pipeline correctly

```python
single = p(one_input)
items = p([input1, input2])              # list of per-item outputs
batched = p([input1, input2], batch_size=2)
stream = p(ms_dataset)                  # generator over dataset rows
```

Call-time kwargs are pipeline-specific. A custom pipeline can route them by
overriding `_sanitize_parameters`:

```python
def _sanitize_parameters(self, top_k=5, **kwargs):
    return {}, {}, {'top_k': top_k, **kwargs}
```

For batched calls, ensure `preprocess` returns dict values that can be collated
and ensure `forward` returns values with a leading batch dimension or lists that
can be sliced per item. If the default `_batch` behavior is wrong, override
`_batch` in the pipeline subclass.

## 3. Read outputs safely

Prefer `OutputKeys` constants over hard-coded strings:

```python
from modelscope.outputs import OutputKeys

labels = result.get(OutputKeys.LABELS)
scores = result.get(OutputKeys.SCORES)
text = result.get(OutputKeys.TEXT)
image = result.get(OutputKeys.OUTPUT_IMG)
```

Not every task uses labels/scores. Check the task-output reference before
assuming keys. For user-facing code, use `.get(...)` and produce a clear error
that includes available keys when a key is absent.

## 4. Handle device selection

- `device='cpu'`: preferred for portable smoke tests and CPU-only deployments.
- `device='gpu'` or `device='gpu:0'`: accepted alias for CUDA device 0.
- `device='cuda'` or `device='cuda:0'`: also accepted and normalized.
- If omitted, `pipeline(...)` sets `device='gpu'`. This may still fall back to
  CPU for torch device creation when CUDA is unavailable, but explicit CPU avoids
  confusing logs, unnecessary CUDA checks, and unverified GPU expectations.
- Do not claim CUDA, ROCm, MPS, or accelerator correctness from CPU smoke tests.

## 5. Apply `trust_remote_code` policy

Default policy:

```python
trust_remote_code = False
```

Only set `True` after review of the exact model repository, plugins, Python
configs, and remote code. Record that decision near the user workflow. If a load
fails with a trust message, do not blindly retry with trust enabled; first decide
whether the repository is allowed to execute code.

## 6. Optional backend and dependency checks

Many pipelines lazily import domain dependencies when their registry target is
built. A registry target may exist but fail at import time because a package such
as `torch`, `tensorflow`, `transformers`, `opencv-python`, `Pillow`, audio/video
libraries, `swift`, or task-specific CUDA extensions is absent. Treat these as
optional dependency/backend failures unless the user's workflow explicitly
requires that backend.

For a deterministic local smoke, use `scripts/custom_pipeline_smoke.py`; it does
not require a model download, dataset load, training loop, CUDA, or source
checkout.

## 7. Boundaries and routing

- Creating template files through the ModelScope CLI belongs in
  `../customization-and-development/SKILL.md`.
- Training, evaluation, trainer metrics, and checkpoint workflows belong in
  `../training-and-evaluation/SKILL.md`.
- Dataset discovery and `MsDataset.load` details belong in
  `../datasets-config/SKILL.md`.
