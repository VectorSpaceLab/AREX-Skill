# Troubleshooting post-training tools

## Fast triage

Run the deterministic preflight first:

```bash
python scripts/post_training_preflight.py --model-path model.keras \
  --save-path artifacts/model.tflite --optimize-default
```

It checks paths, project metadata, optimization selection, and safe output
placement without importing DeepDanbooru, loading a model, creating files, or
using the network. For TensorFlow Lite itself, use the tiny local smoke test:

```bash
python scripts/tflite_conversion_smoke.py --output-dir artifacts/tflite-smoke
```

## TFLite failures

| Symptom | Likely cause | Action |
|---|---|---|
| `You must provide project path or model path.` | Neither source was supplied | Give one existing `--model-path` or `--project-path`. |
| `You must provide a path to save tflite model.` | Save path is empty | Provide `--save-path`; create its parent first. |
| `optimization method must be specified` | No optimization was selected | Select `--optimize-default` or `--optimize-experimental-sparsity`; keep the selection explicit. |
| Click rejects a path | Project/model does not exist or has wrong file/dir kind | Fix the path before TensorFlow is invoked. An existing `--save-path` directory is always an error, including with `--allow-existing-output`; that flag only allows replacing an existing regular file. |
| `FileNotFoundError` at save | Save parent does not exist | Create the parent directory; do not point at a directory. |
| Converter reports unsupported op/layer/custom object | Keras model is not convertible under the selected TensorFlow runtime | Preserve the original model, retry default optimization without sparsity, and inspect custom-object/runtime requirements. |
| Output is missing or zero bytes | Conversion did not produce a usable artifact or output was misdirected | Require a regular non-empty `.tflite`; rerun the smoke/interpreter check. |
| Interpreter cannot allocate tensors | Converted operators, shapes, or dtypes are incompatible with the consumer | Record interpreter details, compare preprocessing, and do not claim deployment readiness. |
| Project load cannot find model | `project.json` model value does not match `model-{model}.keras` or `.h5` | Inspect project metadata and model filename; retrain/export via [model training](../../model-training/SKILL.md) if absent. |

`--verbose` changes diagnostics only. It does not make a conversion compatible.
Do not overwrite the source Keras model while experimenting.

## Grad-CAM failures

| Symptom | Likely cause | Action |
|---|---|---|
| Project/model/tags load error | Missing `project.json`, `tags.txt`, or selected `.keras`/`.h5` | Check all project prerequisites and model selection. |
| Target path error or empty directory | Target does not exist or contains no supported image | Start with one local PNG/JPG/JPEG/GIF file. |
| `ModuleNotFoundError: scipy` | Grad-CAM imports `scipy.ndimage` for median filtering | Install/repair the package in the approved runtime, then rerun the import/help check. |
| `ModuleNotFoundError: PIL` | Grad-CAM imports Pillow to read/write PNGs | Install/repair Pillow in the approved runtime; verify `from PIL import Image`. |
| CLI fails before help with `tensorflow_io` import error | DeepDanbooru package import eagerly requires TensorFlow I/O | Repair the package environment; do not confuse this with a model or image failure. |
| Only `input.png` appears | No prediction meets the inclusive `score >= threshold` test | Compare ordinary inference, then lower the threshold diagnostically; do not invent maps. |
| No maps at a very high threshold | Threshold is too high or model scores are low | Try `0.5` or a lower diagnostic value and record the changed selection rule. |
| Output names are surprising | Tag contains unsupported filename characters | Inspect the sanitized `:` and `/` replacements and use a separate output folder. |
| Gradient/median-filter error | Model is not differentiable for the selected path, shape is malformed, or SciPy/runtime is incompatible | Confirm NHWC shape and Keras model load; retry one tag on CPU and preserve logs. |
| Visualization is very slow | One gradient pass is done per selected tag, especially on CPU | Start with one image and a higher threshold; GPU may help but is optional/unverified. |
| `input.png` or maps cannot be written | Output is a file, parent is unwritable, or same-named artifact is locked | Choose a writable disposable directory and inspect permissions. |

The legacy `deepdanbooru.gradcam` module is not the CLI path and runs a test at
import time; avoid it for production troubleshooting.

## Escalation boundaries

Use [Inference and evaluation](../../inference-evaluation/SKILL.md) to verify
scores, image preprocessing, tag order, and ordinary CPU predictions. Use
[Model training](../../model-training/SKILL.md) when no loadable model exists.
GPU errors should be reported separately from required CPU correctness; this
skill does not verify a GPU backend.
