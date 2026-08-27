# Troubleshooting Pipelines and Models

## `ValueError: task or pipeline_name is required`

Pass at least one of:

```python
pipeline(task=Tasks.text_classification, ...)
pipeline(task='local-task', pipeline_name='local-pipeline', ...)
```

For custom/local smoke tests, provide both a custom task string and an explicit
`pipeline_name` so no default hub lookup is needed.

## Registry `KeyError`: type not in registry group

Symptoms mention a type, registry, and group, for example `custom-x is not in the
pipelines registry group local-task`.

Checklist:

1. Import the module that registers the class before calling `pipeline(...)` or
   `build_model(...)`. Registration is side-effect based.
2. Confirm the decorator group matches the task:
   `@PIPELINES.register_module(group_key=task, module_name='name')`.
3. Confirm the config or `pipeline_name` uses the same `module_name`.
4. For model/preprocessor builders, confirm the `model.type` or
   `preprocessor.type` appears in the correct `MODELS` or `PREPROCESSORS` group.
5. If a lazy import target exists but fails, inspect the underlying import error;
   the registry may be present but an optional dependency may be missing.

## Default model unexpectedly downloads or fails

`pipeline(task=...)` without `model=` may download a default model. To avoid
network access, use a local model directory, an already-loaded `Model`, or a
custom local pipeline with `model=None`. Pin `model_revision` when using hub ids.

## CUDA or device confusion

The pipeline factory defaults to `device='gpu'` when `device` is omitted. In
CPU-only environments, pass `device='cpu'` explicitly. Accepted device strings
include `cpu`, `gpu`, `gpu:0`, `cuda`, and `cuda:0`. Torch device creation can
fall back to CPU when CUDA is unavailable, but that does not verify GPU behavior.

If `device_map` is provided to `Pipeline`, the base class asserts that
`device == 'gpu'`; do not pass both a CPU device and a device map.

## Optional dependency import failure

Many task pipelines import optional packages lazily only when constructed.
Failures may mention `transformers`, `torch`, `tensorflow`, `cv2`, `PIL`, audio
libraries, video codecs, `swift`, or task-specific CUDA extensions.

Actions:

1. Verify the user actually needs that task/backend.
2. Install only the minimal dependency variant for the selected workflow.
3. Retry a CPU-safe or smaller pipeline if the backend is optional.
4. Do not treat a CPU import as proof that CUDA/ROCm/MPS/domain accelerators work.

## Trust/remote-code refusal

Errors may say plugins, `allow_remote`, Python config loading, or extra model repo
code requires `trust_remote_code=True`.

Safe response:

1. Stop automatic loading.
2. Identify the exact model repository and revision.
3. Review whether it declares plugins, `allow_remote`, or `.py` config/code.
4. Enable `trust_remote_code=True` only if the user or policy trusts that source.
5. Keep the decision scoped to that model/revision; do not set it globally.

Do not use `trust_remote_code=True` to bypass ordinary registry, missing-file, or
missing-dependency errors.

## Python config refused

`Config.from_file('...py')` can execute top-level Python. Use JSON/YAML config for
portable local workflows. If a trusted Python config is genuinely required, pass
`trust_remote_code=True` to the config-loading path that supports it and document
why the code is trusted.

## Output key failure

The base pipeline output checker may raise that expected output keys are missing.
Fix the pipeline's `postprocess` to return the keys declared for the task, or use
a custom task string without a declared output contract for local smoke tests.
For user-facing inference, inspect `result.keys()` and access via `OutputKeys`.

## Batched call shape errors

If `p(inputs, batch_size=N)` fails but `p(input)` succeeds:

- Ensure `preprocess` returns a dict for each sample.
- Ensure values can be concatenated or collected by `_batch`.
- Override `_batch` for nested/custom objects.
- Ensure `forward` returns a batched dict whose values can be sliced per item.
- Ensure `postprocess` accepts one sliced item, not the whole batch.

## `MsDataset` returns a generator

When input is an `MsDataset`, the base pipeline returns a generator over results.
Use:

```python
for item in p(dataset):
    ...
# or
first = next(p(dataset))
```

Dataset acquisition and schema issues belong in `../datasets-config/SKILL.md`.

## Local model directory lacks configuration

ModelScope-native loading expects `configuration.json`. If the directory lacks
it, ModelScope may attempt Hugging Face fallback depending on installed packages
and config files. For a native ModelScope model, add or locate the proper
configuration; for HF models, use `use_hf=True` or the HF-compatible path when
appropriate.
