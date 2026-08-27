# Pipelines and partner packages

This reference covers `optimum.pipelines.pipeline`, accelerator selection, and the dependency boundary between base Optimum and partner implementations.

## What base Optimum provides

Base Optimum provides a dispatcher:

```python
from optimum.pipelines import pipeline
```

The dispatcher mirrors many arguments from `transformers.pipeline` and adds an `accelerator` selector. It does not itself implement ONNX Runtime or OpenVINO model execution. Instead, it imports and delegates to partner packages when available.

Important signature shape:

```python
pipeline(
    task=None,
    model=None,
    config=None,
    tokenizer=None,
    feature_extractor=None,
    image_processor=None,
    processor=None,
    framework=None,
    revision=None,
    use_fast=True,
    token=None,
    device=None,
    device_map=None,
    torch_dtype="auto",
    trust_remote_code=None,
    model_kwargs=None,
    pipeline_class=None,
    accelerator=None,
    **kwargs,
)
```

## Accelerator selection

`accelerator` may be:

| Value | Behavior | Required partner availability |
| --- | --- | --- |
| `None` | Auto-select OpenVINO first if available, otherwise ONNX Runtime if available, otherwise raise `ImportError`. | Either `optimum-intel[openvino]` or `optimum-onnx[onnxruntime]`. |
| `"ort"` | Import `optimum.onnxruntime.pipeline` and delegate. | `optimum-onnx` with ONNX Runtime support. |
| `"ov"` | Import `optimum.intel.pipeline` and delegate. | `optimum-intel` with OpenVINO support. |
| `"ipex"` | Raise a deprecation `ValueError`. | No longer supported; use `ov`. |
| Other string | Raise `ValueError` explaining valid choices. | Not applicable. |

When `accelerator=None`, OpenVINO is preferred over ONNX Runtime if both partner stacks are installed and importable.

## Safe availability check

This check does not download models:

```python
from optimum.utils.import_utils import (
    is_onnxruntime_available,
    is_openvino_available,
    is_optimum_intel_available,
    is_optimum_onnx_available,
)

print("optimum-onnx:", is_optimum_onnx_available())
print("onnxruntime:", is_onnxruntime_available())
print("optimum-intel:", is_optimum_intel_available())
print("openvino:", is_openvino_available())
```

The CLI probe also reports whether `export onnx` appears in help:

```bash
python scripts/probe_optimum_cli.py
```

## Calls that may download or need cache

These calls can use Hugging Face Hub metadata or weights if a local model and components are not supplied:

```python
pipeline("text-classification", accelerator="ort")
pipeline("text-classification", model="some-model-id", accelerator="ov")
```

For offline or deterministic work:

- Prefer local model directories that are already exported for the target runtime.
- Pass explicit `task`, `model`, `tokenizer`/processor components, and `accelerator`.
- Avoid `trust_remote_code=True` unless the user explicitly approves the code trust boundary.
- Avoid default model selection unless network/cache use is allowed.

## Installing partner stacks

Base metadata exposes optional extras for partner features. Use the user's package manager and environment policy, for example:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnx]"
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime]"
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime-gpu]"
python -m pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
python -m pip install --upgrade --upgrade-strategy eager "optimum[intel]"
```

Then verify imports and help:

```bash
python scripts/probe_optimum_cli.py --run-env
python - <<'PY'
from optimum.utils.import_utils import is_optimum_onnx_available, is_onnxruntime_available
print(is_optimum_onnx_available(), is_onnxruntime_available())
PY
```

## Optional ONNX/ORT/OpenVINO verification

Only run actual export or pipeline inference when all of the following are true:

- The user requested runtime verification beyond base routing.
- The needed partner package is installed.
- Model weights are already cached locally or network access is approved.
- The target output directory and cleanup behavior are explicit.
- Runtime budget is sufficient.

Typical optional checks:

- `optimum-cli export onnx --help` after installing the ONNX partner package.
- A tiny cached local-model export to a temporary directory.
- `pipeline(..., accelerator="ort")` or `pipeline(..., accelerator="ov")` with local/cached model assets.

Do not treat missing partner packages as a base-skill failure. Report them as optional dependency boundaries.

## Common dispatcher errors

| Symptom | Meaning | Recovery |
| --- | --- | --- |
| `ImportError` says install `optimum-onnx[onnxruntime]` or `optimum-intel[openvino]`. | No usable accelerated pipeline backend is installed. | Install a matching partner stack or use regular `transformers.pipeline`. |
| `ValueError: The ipex accelerator is deprecated...` | `accelerator="ipex"` is no longer supported by this dispatcher. | Use `accelerator="ov"` for OpenVINO. |
| `ValueError: Accelerator X not recognized...` | Unsupported accelerator string. | Use `"ort"` or `"ov"`. |
| Pipeline call hangs or reaches the network. | Default model/component loading or model id resolution is fetching Hub assets. | Supply local model and tokenizer/processor, or approve/cache downloads first. |
