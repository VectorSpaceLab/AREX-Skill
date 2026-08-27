# Optimization and Export

Use this reference before changing docTR devices, precision, compile mode, predictor batch sizes, or ONNX export settings.

## Device placement

All public docTR model and predictor objects in this sub-skill are PyTorch modules. Move the predictor or raw model to the selected device before inference.

```python
import torch
from doctr.models import recognition_predictor

predictor = recognition_predictor("crnn_vgg16_bn", pretrained=True).eval()

if torch.cuda.is_available():
    device = torch.device("cuda")
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

predictor = predictor.to(device)
```

Practical guidance:

- CPU is valid for correctness checks and small inference, but it can be slow for full documents or large batches.
- CUDA is the best-supported acceleration path for training, half precision, and high-throughput inference.
- MPS can run regular inference on Apple Silicon when PyTorch supports the needed operations; validate outputs and fall back to CPU if an operation is unsupported.
- Do not move only the inner model when using a full predictor unless you know how the wrapper prepares tensors. Moving the whole predictor is the safer pattern.
- Use `eval()` for inference and `torch.inference_mode()` around raw-model calls when not using high-level predictors.

## Batch-size tuning

Default predictor batch sizes:

| Predictor | Default batch size | Why it matters |
|---|---:|---|
| `detection_predictor` | 2 | page-size tensors are large |
| `layout_predictor` | 2 | page-size tensors and masks are large |
| `table_predictor` | 2 | table page/crop tensors are large |
| `recognition_predictor` | 128 | word crops are small, so batching helps throughput |
| `crop_orientation_predictor` | 128 | crop classifier is lightweight |
| `page_orientation_predictor` | 4 | page tensors are larger |

Increase batch size only after checking device memory. If a CUDA/MPS out-of-memory error appears, reduce the relevant predictor batch size first before switching architectures.

## Half precision: BF16 and FP16

docTR's documented half-precision inference support is for PyTorch models on GPU devices.

```python
from doctr.models import ocr_predictor

predictor = ocr_predictor(
    reco_arch="crnn_mobilenet_v3_small",
    det_arch="linknet_resnet34",
    pretrained=True,
).cuda().bfloat16()

result = predictor(doc)
```

Rules:

- Prefer BF16 (`.bfloat16()`) on Ampere-generation NVIDIA GPUs or newer because it preserves FP32 exponent range.
- Use FP16 (`.half()`) on older CUDA hardware only after validating numerical stability.
- Do not use `.half()` or `.bfloat16()` as a CPU optimization; it is not supported for docTR inference on CPU.
- Keep postprocessing validation in place after precision changes. Some model internals convert BF16 outputs to FP32 for operations that need NumPy-compatible dtypes, but this is not a substitute for checking task-level output quality.
- On MPS, use regular FP32 first. Do not assume docTR's BF16/FP16 behavior matches CUDA.

## `torch.compile` for PyTorch models

`torch.compile` can optimize raw PyTorch model modules before they are wrapped in docTR predictors.

```python
import torch
from doctr.models import (
    fast_base,
    vitstr_small,
    ocr_predictor,
    mobilenet_v3_small_crop_orientation,
    mobilenet_v3_small_page_orientation,
    crop_orientation_predictor,
    page_orientation_predictor,
)

compiled_det = torch.compile(fast_base(pretrained=True).eval())
compiled_reco = torch.compile(vitstr_small(pretrained=True).eval())
compiled_crop_orientation = torch.compile(
    mobilenet_v3_small_crop_orientation(pretrained=True).eval()
)
compiled_page_orientation = torch.compile(
    mobilenet_v3_small_page_orientation(pretrained=True).eval()
)

predictor = ocr_predictor(
    det_arch=compiled_det,
    reco_arch=compiled_reco,
    assume_straight_pages=False,
)
predictor.crop_orientation_predictor = crop_orientation_predictor(compiled_crop_orientation)
predictor.page_orientation_predictor = page_orientation_predictor(compiled_page_orientation)
```

Caveats:

- This is PyTorch-only.
- Compile raw model modules, not the full high-level `ocr_predictor`, unless you have separately validated the whole wrapper.
- Use `.eval()` before compiling for inference.
- The recognition architecture `master` is not officially supported for model compilation.
- docTR source explicitly accepts compiled modules in standalone detection, recognition, layout, table, and orientation predictor factories.
- Official support is for PyTorch's default `inductor` backend. Other compile backends are experimental in this context.
- The first compiled call may be slower due to graph capture/compilation; benchmark after warmup.
- Dynamic page sizes, unsupported ops, or backend limitations can cause graph breaks or runtime errors. Fall back to uncompiled raw models when correctness or portability matters more than speed.

## ONNX export: helper signature and behavior

Use `export_model_to_onnx` on raw models, not predictor wrappers.

```python
from doctr.models.utils import export_model_to_onnx

export_model_to_onnx(
    model,
    model_name="model",
    dummy_input=dummy_input,
    input_names=None,
    output_names=None,
    dynamic_axes=None,
    **torch_onnx_kwargs,
)
```

Behavior:

- Writes to `f"{model_name}.onnx"` and returns that path. Pass a path stem such as `"model"` to avoid accidental double `.onnx` suffixes.
- Defaults to input name `"input"` and output name `"logits"` for a single tensor input.
- If `dummy_input` is a tuple, defaults to input names `"input"`, `"masks"` and output names `"logits"`, `"pred_boxes"`.
- Defaults `dynamic_axes` to a dynamic batch dimension for every input and output.
- Calls `torch.onnx.export(..., export_params=True, dynamo=False, verbose=False, **kwargs)`.
- Requires the `onnx` package. Running exported models requires an ONNX runtime such as ONNX Runtime or a compatible lightweight OCR package.

## Exportable model examples

Set `exportable=True` when constructing raw models for ONNX export. This makes model forwards return raw tensor outputs rather than normal postprocessed Python structures.

### Recognition ONNX

```python
import torch
from doctr.models import vitstr_small
from doctr.models.utils import export_model_to_onnx

model = vitstr_small(pretrained=True, exportable=True).eval()
dummy_input = torch.rand((1, 3, 32, 128), dtype=torch.float32)
model_path = export_model_to_onnx(
    model,
    model_name="vitstr_model",
    dummy_input=dummy_input,
)
```

### Detection ONNX

```python
import torch
from doctr.models import fast_base
from doctr.models.utils import export_model_to_onnx

model = fast_base(pretrained=True, exportable=True).eval()
dummy_input = torch.rand((1, 3, 512, 512), dtype=torch.float32)
model_path = export_model_to_onnx(
    model,
    model_name="detector_model",
    dummy_input=dummy_input,
)
```

### Layout ONNX with masks

Layout models consume an image tensor and a boolean padding mask for ONNX export.

```python
import torch
from doctr.models import lw_detr_s
from doctr.models.utils import export_model_to_onnx

model = lw_detr_s(pretrained=True, exportable=True).eval()
dummy_input = torch.rand((1, 3, 512, 512), dtype=torch.float32)
dummy_masks = torch.ones((1, 512, 512), dtype=torch.bool)
model_path = export_model_to_onnx(
    model,
    model_name="layout_model",
    dummy_input=(dummy_input, dummy_masks),
)
```

### Table structure ONNX with multiple outputs

TableCenterNet exposes several output heads. Name each output explicitly.

```python
import torch
from doctr.models import tablecenternet
from doctr.models.utils import export_model_to_onnx

model = tablecenternet(pretrained=True, exportable=True).eval()
dummy_input = torch.rand((1, 3, 1024, 1024), dtype=torch.float32)
head_names = list(model.heads.keys())
model_path = export_model_to_onnx(
    model,
    model_name="table_model",
    dummy_input=dummy_input,
    output_names=head_names,
)
```

### Classification/orientation ONNX

```python
import torch
from doctr.models import mobilenet_v3_small_crop_orientation
from doctr.models.utils import export_model_to_onnx

model = mobilenet_v3_small_crop_orientation(pretrained=True).eval()
dummy_input = torch.rand((1, 3, 256, 256), dtype=torch.float32)
model_path = export_model_to_onnx(
    model,
    model_name="crop_orientation_model",
    dummy_input=dummy_input,
)
```

## Optional backend and dependency guidance

- Core docTR inference in this repository is PyTorch-based.
- CUDA is optional for inference but required for GPU acceleration and the documented half-precision path.
- MPS is optional and should be treated as a regular inference backend with fallback validation.
- `onnx` is needed for export; `onnxruntime` or another runtime is needed to execute exported ONNX graphs.
- Hugging Face Hub loading requires network/cache access unless `from_hub(..., local_files_only=True)` can find files already cached.
- Avoid installing broad optional dependency groups just for model selection. Add only the backend/runtime needed for the requested action.

## Related references

- Architecture and customization patterns: [model-catalog-and-customization.md](model-catalog-and-customization.md)
- Failures and fixes: [troubleshooting.md](troubleshooting.md)
