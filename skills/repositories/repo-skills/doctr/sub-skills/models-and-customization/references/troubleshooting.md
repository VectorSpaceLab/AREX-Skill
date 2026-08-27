# Troubleshooting Models and Customization

Use this reference when standalone model factories, custom weights, whitelists, Hub loading, device moves, compile, or ONNX export fail.

## Decision tree

1. **Unknown architecture?** Check the architecture string against the catalog in [model-catalog-and-customization.md](model-catalog-and-customization.md).
2. **Weights do not load?** Recreate the raw model with the exact trained `vocab`, `class_names`, `classes`, `num_classes`, `input_shape`, and architecture before `from_pretrained`.
3. **Inference output is random or unusable?** Confirm `pretrained=True` or successful `from_pretrained(...)`; `pretrained=False` alone means random weights.
4. **Device/precision failure?** Return to FP32 on CPU or CUDA, then reintroduce MPS, BF16/FP16, or compile one at a time.
5. **ONNX export failure?** Export a raw `exportable=True` model with a correctly shaped dummy input and explicit output names for multi-output models.
6. **Whitelist failure?** Confirm the whitelist intersects the recognition model's own vocabulary.
7. **Hub failure?** Confirm the repo contains docTR-compatible `config.json` and `pytorch_model.bin` and that credentials/cache/network options match the requested operation.

## Factory and architecture errors

### `ValueError: unknown architecture '...'`

Likely causes:

- Typo or wrong task family, such as passing a recognition architecture to `detection_predictor`.
- Passing a generic classifier name to `crop_orientation_predictor` or `page_orientation_predictor`; those string factories accept only `mobilenet_v3_small_crop_orientation` and `mobilenet_v3_small_page_orientation`.
- Passing a raw custom module whose class is not one of the accepted docTR model classes for that predictor.

Fix:

```python
from doctr.models import detection_predictor, recognition_predictor

# Correct: detection arch in detection predictor
det = detection_predictor("fast_base", pretrained=True)

# Correct: recognition arch in recognition predictor
reco = recognition_predictor("parseq", pretrained=True)
```

If a custom raw model is required, wrap only compatible docTR model classes:

- Detection: DBNet, LinkNet, FAST.
- Recognition: CRNN, SAR, MASTER, ViTSTR, PARSeq, VIPTR.
- Layout: LWDETR.
- Table: TableCenterNet.
- Orientation: MobileNetV3 orientation variants.

Compiled versions of those models are accepted by the standalone predictor factories, but arbitrary PyTorch modules are not.

## Pretrained and cache surprises

### `pretrained=False` returns poor predictions

This is expected. It creates a randomly initialized architecture. Use one of:

```python
model = recognition_predictor("crnn_vgg16_bn", pretrained=True)
```

or:

```python
from doctr.models import crnn_vgg16_bn

raw = crnn_vgg16_bn(pretrained=False, vocab=my_vocab)
raw.from_pretrained("recognizer-weights.pt")
model = recognition_predictor(raw)
```

### Download blocked or undesired

Use `pretrained=False` and a local checkpoint, or ask the user to provide a cache/revision policy. For Hub models, `from_hub(..., local_files_only=True)` is appropriate only when the files are already cached.

## Custom checkpoint load errors

### Size mismatch in recognition projection layers

Likely cause: the checkpoint was trained with a different vocabulary.

Fix:

```python
from doctr.models import parseq

model = parseq(pretrained=False, vocab=trained_vocab)
model.from_pretrained("weights.pt")
```

Do not load a custom-vocab checkpoint into the default French-vocabulary model.

### Size mismatch in detection/layout classification heads

Likely cause: class names differ from the checkpoint.

Fix:

```python
from doctr.models import lw_detr_s

model = lw_detr_s(
    pretrained=False,
    class_names=["heading", "paragraph", "figure", "table"],
)
model.from_pretrained("layout-weights.pt")
```

Keep the exact class-name set used during training. Detection and layout constructors may sort class names internally, so store class metadata with the checkpoint.

### `from_pretrained` accepts a path or URL but still fails

Check:

- The file is a PyTorch state dict compatible with the selected architecture, not an entire training checkpoint wrapper unless saved that way for docTR.
- The raw constructor matches the checkpoint architecture.
- Custom vocabulary/class metadata is supplied before loading.
- You did not call `from_pretrained` on a high-level predictor wrapper instead of the raw model.

## Whitelist issues

### `ValueError: The whitelist shares no character with the model's vocabulary`

The whitelist cannot add characters; it only masks model outputs. Inspect the recognition vocabulary first:

```python
from doctr.models import recognition_predictor

predictor = recognition_predictor("crnn_vgg16_bn", pretrained=True)
print(predictor.model.vocab)
```

If required characters are missing, use or train a recognition model with a larger vocabulary, then apply `add_whitelist` to restrict it.

### Characters still look outside the intended language

Check whether:

- The character is actually present in one of the allowed vocab strings.
- Multiple whitelist hooks were registered and not removed.
- The code forgot to use the `WhitelistHandle.remove()` method or context manager.
- `strategy="nearest"` mapped a forbidden accented character onto an allowed base character, which may be expected normalization.

Safe pattern:

```python
from doctr.models.utils import add_whitelist

with add_whitelist(predictor, allowed_vocab):
    result = predictor(doc)
# Hook is removed here.
```

### `mapping` argument errors

- `mapping` is only valid with `strategy="nearest"`.
- Valid mapping values are `None`, `"anyascii"`, `"weights"`, or a dict.
- `strategy` must be `"mask"` or `"nearest"`.

## Device, precision, and compile failures

### CPU half-precision failure

docTR documents half-precision inference for PyTorch models on GPU devices only. Fix by using FP32 on CPU:

```python
predictor = predictor.float().cpu()
```

If GPU is available, prefer BF16 on Ampere-generation NVIDIA GPUs or newer:

```python
predictor = predictor.cuda().bfloat16()
```

Use FP16 only when BF16 is unavailable and output quality has been checked.

### MPS runtime error

MPS support depends on PyTorch operator coverage. Fix by falling back to CPU or CUDA:

```python
try:
    predictor = predictor.to("mps")
    result = predictor(doc)
except RuntimeError:
    predictor = predictor.to("cpu").float()
    result = predictor(doc)
```

Do not combine MPS with compile or half precision until plain FP32 inference works.

### `torch.compile` graph breaks or wrong type in predictor factory

Checklist:

- Compile the raw model, not an arbitrary wrapper.
- Call `.eval()` before `torch.compile` for inference.
- Do not use recognition architecture `master` for compiled inference unless the user accepts unsupported behavior.
- Pass the compiled model into the matching predictor factory.
- Fall back to the uncompiled model if dynamic shapes or backend limitations break execution.

## ONNX export issues

### Export writes an unexpected filename

`export_model_to_onnx` always writes `f"{model_name}.onnx"`.

Fix:

```python
export_model_to_onnx(model, model_name="recognizer", dummy_input=x)
# writes recognizer.onnx
```

Avoid `model_name="recognizer.onnx"` unless a double suffix is acceptable.

### Output names do not match

Defaults are correct for simple single-output models (`logits`) and layout tuple inputs (`logits`, `pred_boxes`). For multi-head table models, pass every output name:

```python
head_names = list(model.heads.keys())
export_model_to_onnx(
    model,
    model_name="table_model",
    dummy_input=dummy_input,
    output_names=head_names,
)
```

### Layout export complains about missing masks

Layout models need `(image_tensor, mask_tensor)` as dummy input for ONNX export:

```python
dummy_input = torch.rand((1, 3, 512, 512), dtype=torch.float32)
dummy_masks = torch.ones((1, 512, 512), dtype=torch.bool)
export_model_to_onnx(model, "layout_model", (dummy_input, dummy_masks))
```

### Exported model output differs from PyTorch

Use this isolation sequence:

1. Export from FP32 raw model first.
2. Use `exportable=True` and `.eval()`.
3. Use the same dummy shape as expected at inference.
4. Validate with CPU ONNX Runtime before enabling CUDA providers.
5. Add custom `input_names`, `output_names`, and `dynamic_axes` only after the default export works.

## Hugging Face Hub issues

### `push_to_hf_hub` raises about missing `run_config` or `arch`

Pass `arch=...` explicitly unless pushing from a training run config that has an `arch` attribute:

```python
push_to_hf_hub(
    model,
    model_name="doctr-custom-recognizer",
    task="recognition",
    arch="parseq",
)
```

### `task` or `arch` validation fails

Use the exact task family:

- `classification`
- `detection`
- `recognition`
- `layout`
- `table_structure`

The architecture must be in that task's supported list. For example, `crnn_mobilenet_v3_large` is valid for `recognition`, not `detection`.

### `from_hub` fails while reconstructing the model

A docTR-compatible Hub repo must contain:

- `config.json` with `arch` and `task` plus task-specific model configuration.
- `pytorch_model.bin` with compatible weights.

If either file is absent or was produced by a non-docTR training/export path, `from_hub` may not be able to reconstruct the model. Download the files manually only with user approval and inspect the config before retrying.

### Credentials or Git LFS failures

- `from_hub` for public repos can work without login if network/cache access is available.
- `login_to_hub` and `push_to_hf_hub` require user credentials.
- `login_to_hub` checks Git LFS. If Git LFS is absent, install/configure it outside the model code path before pushing.
- Never push to Hub unless the user explicitly asks for a publishing side effect.

## Table-specific confusion

### Standalone `table_predictor` returns cells but no OCR text

This is expected. `table_predictor` handles table structure, not text recognition. To associate words with cells in a full document, use the full OCR pipeline with table detection enabled and route output interpretation to the core OCR/KIE and document export sub-skills.

### `table_predictor` is passed into OCR without layout

In the full OCR predictor, table extraction depends on layout regions to find table crops. If constructing lower-level OCR predictors manually, provide both a layout predictor and a table predictor when table extraction is required.

## Minimal safe fallback

When debugging an unknown model issue, reduce to this baseline:

```python
from doctr.models import detection_predictor, recognition_predictor

# No compile, no half precision, no custom weights, CPU-safe.
det = detection_predictor("fast_base", pretrained=False, batch_size=1)
reco = recognition_predictor("crnn_vgg16_bn", pretrained=False, batch_size=2)
```

This validates factory names and wrapper construction without downloads. It is not a quality test because the models are randomly initialized.
