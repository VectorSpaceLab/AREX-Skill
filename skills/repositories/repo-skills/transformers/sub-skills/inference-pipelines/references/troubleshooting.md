# Inference Pipeline Troubleshooting

## Quick Triage

1. Reproduce with the smallest input and `batch_size=1`.
2. Print `transformers.__version__`, task id, model id/path, `device`, `device_map`, `dtype`, and `local_files_only` without printing tokens.
3. Check whether the failure happens during import, config loading, model loading, pipeline construction, or pipeline call.
4. Validate a local config first when offline: `AutoConfig.from_pretrained(path, local_files_only=True)`.
5. Remove acceleration choices (`device_map`, quantization, explicit dtype, batching) until the base pipeline works.
6. Add output shape assertions only after construction and one tiny call succeed.

## Missing Optional Dependencies

Transformers can be imported in a minimal environment, but many pipelines require optional packages.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` mentioning PyTorch or backend classes | `torch` is not installed | Install a compatible PyTorch build for the target CPU/GPU platform, then rerun a tiny pipeline. |
| Image pipeline fails on image loading | missing Pillow or image backend | Install `Pillow`; for some workflows install `torchvision` as well. |
| Detection/segmentation fails after construction | missing vision backend or incompatible torch/torchvision | Verify `import torch`, `import torchvision`, and one local image smoke. |
| ASR/audio classification fails reading files | missing audio libraries such as `soundfile`, `librosa`, or codec support | Install the required audio package and test a tiny local `.wav`/`.flac` file. |
| Video classification fails loading clips | missing video decoder such as decord/pyav or codec support | Install a supported video decoding stack and test a short local clip. |
| `device_map="auto"` fails | missing Accelerate-compatible placement dependency | Install/verify Accelerate and retry without also setting `device`. |

Image-classification debugging pattern:

```python
from PIL import Image
from transformers import pipeline

Image.open("image.png").verify()
pipe = pipeline("image-classification", model=model_id, device=-1)
result = pipe(images="image.png")
assert isinstance(result, list) and "score" in result[0]
```

If this fails before `pipeline()` construction, fix image dependencies. If it fails during model load, fix PyTorch/model files. If it fails during the call, check input type and task/model compatibility.

## Hub, Network, Cache, and Auth Errors

Common causes:

- No network access while using a Hub id.
- `local_files_only=True` with missing local cache files.
- Private or gated model without authentication.
- Model id typo or wrong namespace.
- Unpinned model changed upstream.

Fixes:

```python
from transformers import AutoConfig

config = AutoConfig.from_pretrained("./local-model", local_files_only=True)
assert config.model_type
```

- For offline runs, use a local model directory and `local_files_only=True` for all components.
- For gated/private models, authenticate outside code and use `token=True`; never commit token strings.
- For reproducibility, set `revision` to a pinned commit or trusted tag.
- If a Hub model uses custom code, review and pin it before enabling `trust_remote_code=True`.

## `device` vs `device_map` Conflicts

Problem pattern:

```python
pipeline("text-generation", model=model_id, device=0, device_map="auto")
```

The pipeline implementation warns that `device` overrides `device_map`, which can cause unexpected placement.

Fix:

- For one explicit device, use only `device=0` or `device="mps"`.
- For Accelerate placement or large-model sharding, use only `device_map="auto"`.
- Do not duplicate `device_map` top-level and inside `model_kwargs`.

## Dtype Incompatibility

Symptoms:

- `float16` operation unsupported on CPU.
- MPS backend reports unsupported dtype or op.
- CUDA OOM after switching dtype or batch size.
- Error mentions both `torch_dtype` and `dtype`.

Fixes:

- Prefer `dtype="auto"` in portable code.
- Use `dtype="float16"` mainly for CUDA inference after confirming support.
- Use `dtype="bfloat16"` only on hardware that supports it.
- Remove deprecated `torch_dtype`; use `dtype` instead.
- Do not pass `dtype` both top-level and inside `model_kwargs`.
- Retry with default dtype and `device=-1` to separate model/task issues from hardware issues.

## Unsupported Task or Model Mismatch

Symptoms:

- Unknown task identifier.
- Auto model class cannot be inferred.
- Pipeline says the model type is unsupported for the requested task.
- Missing tokenizer/processor/image processor files.

Fixes:

- Use canonical task ids such as `text-classification`, `text-generation`, `image-classification`, `automatic-speech-recognition`, and `zero-shot-classification`.
- Pick a model advertised for the same task family.
- Pass explicit components when auto-discovery fails:

```python
pipe = pipeline(
    "image-classification",
    model="./model",
    image_processor="./model",
    local_files_only=True,
)
```

- For custom architectures, route to `model-extension`; do not set `trust_remote_code=True` blindly.
- For text generation/chat disagreements, route to `generation` and decide whether `pipeline("text-generation")` or `model.generate()` is the better interface.

## Batch Shape, Nesting, and OOM Issues

Symptoms:

- Output shape differs between single input and list input.
- Text generation returns nested lists for batched prompts.
- Large batch is slower than batch size 1.
- CUDA OOM happens only with batched or long inputs.

Fixes:

- First prove correctness with a single input and `batch_size=1`.
- Normalize output shape at the application boundary.
- Add `truncation=True` or task-supported truncation for variable-length text.
- Avoid batching on CPU or latency-sensitive paths.
- Use small batches for irregular sequence lengths; padding can expand to the longest item in the batch.
- Catch OOM and lower `batch_size`; do not assume batch size 64 is safe.

Example normalizer:

```python
def flatten_generation_outputs(outputs):
    if outputs and isinstance(outputs[0], list):
        return [item for batch in outputs for item in batch]
    return outputs
```

## Trust Remote Code Safety

`trust_remote_code=True` executes model repository Python code. Use it only when all conditions are met:

- The model repository is trusted and reviewed.
- `revision` is pinned.
- The environment is isolated from secrets and sensitive files.
- The workflow cannot use a built-in architecture instead.
- The need is documented in code review.

Safer default:

```python
pipe = pipeline(task="text-classification", model=model_id, trust_remote_code=False)
```

If a model errors and asks for `trust_remote_code=True`, do not automatically enable it. Review the repository code or choose a model with built-in Transformers support.

## Local Path vs Hub Id Confusion

Symptoms:

- A relative path is treated as a Hub id or vice versa.
- Offline load fails despite files being present.
- Components load from mixed local and cached remote sources.

Fixes:

- Use explicit relative or absolute local model directories in application code; for public skill examples use generic `./local-model`.
- Ensure `config.json`, weights, tokenizer/processor files, and generation config when needed are in the same directory or passed explicitly.
- Set `local_files_only=True` for all `from_pretrained` and `pipeline` calls in offline tests.
- Print component `name_or_path` values without leaking machine-specific directories in public logs.

## Small Smoke Checklist

A good fix is complete when:

- `import transformers` succeeds.
- `AutoConfig.from_pretrained(model_or_path, local_files_only=...)` succeeds for the intended source.
- `pipeline(...)` constructs without warnings that affect correctness.
- One tiny representative input returns the expected shape and keys.
- Optional dependency requirements are documented for the chosen modality.
- Offline paths avoid Hub downloads and URL inputs.
- Secret tokens and local machine paths are not logged or committed.
