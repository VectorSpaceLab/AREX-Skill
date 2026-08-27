# Optional extras, contrib modules, and Hugging Face Hub

Use this reference for optional dependency groups, `doctr.contrib.ArtefactDetector`, and docTR's Hugging Face Hub helper functions. These surfaces often require extra packages, model downloads, GPU/provider checks, or credentials; make those requirements explicit before running anything with side effects.

## Optional extras map

| Extra | Installs | Use it for | Typical failure when missing |
|---|---|---|---|
| `html` | `weasyprint` | HTML input and URL/page-to-document workflows such as `DocumentFile.from_url` or `read_html` | import/runtime error for HTML conversion |
| `viz` | `matplotlib`, `mplcursors` | `Document`/`Page` visualization, result display, the Streamlit demo's plots, and `ArtefactDetector.show()` | `ModuleNotFoundError` for visualization packages |
| `contrib` | `onnxruntime` | `doctr.contrib.ArtefactDetector` and other contrib ONNX-runtime modules | error saying the contrib module requires `onnxruntime` |

Install only the extras needed for the user's task:

```bash
pip install "python-doctr[viz]"            # visualization and demo plots
pip install "python-doctr[html]"           # HTML/URL document input
pip install "python-doctr[contrib]"        # contrib ArtefactDetector runtime
pip install "python-doctr[viz,html,contrib]"
```

The base package already depends on `huggingface-hub`; no docTR extra is required merely to call `from_hub`, but network access, cache state, and credentials may still matter.

## `doctr.contrib.ArtefactDetector`

Use `ArtefactDetector` when the task is to detect document artefacts such as bar codes, QR codes, logos, or photos in already loaded document images. It is not a replacement for text detection/OCR; route OCR work to the core OCR sub-skill.

### Runtime contract

```python
from doctr.contrib import ArtefactDetector
from doctr.io import DocumentFile

doc = DocumentFile.from_images(["invoice.png"])
detector = ArtefactDetector(batch_size=2, conf_threshold=0.5, iou_threshold=0.5)
artefacts = detector(doc)
print(artefacts)
```

Returned value:

- a list with one entry per input image;
- each image entry is a list of dictionaries;
- each dictionary has `label`, `confidence`, and `box`;
- `box` is `[xmin, ymin, xmax, ymax]` in image pixel coordinates;
- default labels are `bar_code`, `qr_code`, `logo`, and `photo`.

### Constructor options

| Argument | Meaning | Default |
|---|---|---|
| `arch` | default artefact model key | `"yolov8_artefact"` |
| `batch_size` | number of images per ONNXRuntime batch | `2` |
| `model_path` | local ONNX model path; avoids default model download | `None` |
| `labels` | class labels matching the model outputs | default artefact labels |
| `input_shape` | channel/height/width used for resize and scaling | `(3, 1024, 1024)` |
| `conf_threshold` | minimum class score before NMS | `0.5` |
| `iou_threshold` | NMS overlap threshold | `0.5` |
| `**kwargs` | forwarded to the model download helper when `model_path` is not supplied | none |

The default constructor downloads a bundled ONNX model on first use. For offline or controlled deployments, provide `model_path` and verify the model file is already present.

### Custom ONNX model

A custom model should be a YOLOv8-style ONNX export with dynamic batch size. Oriented bounding box inference is not supported by this helper. Keep `labels` and `input_shape` consistent with the exported model:

```python
from doctr.contrib import ArtefactDetector

detector = ArtefactDetector(
    model_path="custom_artefact_detector.onnx",
    labels=["table", "figure"],
    input_shape=(3, 1024, 1024),
    conf_threshold=0.4,
    iou_threshold=0.5,
)
```

The base predictor creates an ONNXRuntime inference session with CUDA and CPU providers listed. If the CUDA provider is unavailable or the installed `onnxruntime` build is CPU-only, expect CPU execution or provider warnings rather than guaranteed GPU acceleration.

### Visualization

`detector.show()` draws labelled rectangles over the stored inputs and results. It requires the visualization dependencies (`matplotlib`, commonly installed through the `viz` extra) in addition to `contrib`.

## Hugging Face Hub loading

Use `from_hub(repo_id, **kwargs)` to load a docTR-compatible PyTorch model repository. The repository must contain:

- `config.json` with `arch` and `task` keys plus the model configuration;
- `pytorch_model.bin` with the matching state dict;
- a `task` value supported by docTR: `classification`, `detection`, `recognition`, `layout`, or `table_structure`;
- an `arch` value present in docTR's architecture registry for that task.

Example:

```python
from doctr.io import DocumentFile
from doctr.models import from_hub, ocr_predictor

pages = DocumentFile.from_images(["document.jpg"])
det_model = from_hub("owner/doctr-detection-model")
reco_model = from_hub("owner/doctr-recognition-model")
predictor = ocr_predictor(det_arch=det_model, reco_arch=reco_model, pretrained=True)
result = predictor(pages)
```

`from_hub` forwards keyword arguments to the underlying Hub download calls, so use Hub-supported options such as `revision`, `cache_dir`, `local_files_only`, or token handling when appropriate. Do not hard-code secret tokens in code examples; use environment-managed or already-configured credentials.

## Hugging Face Hub pushing

Use `push_to_hf_hub` only after the model has been trained/evaluated and the user has approved publishing. The helper saves the model state dict and a docTR config, creates a model repository, and uploads a generated model card plus files.

```python
from doctr.models import login_to_hub, push_to_hf_hub
from doctr.models import recognition

# Run only after the user approves interactive authentication.
login_to_hub()
model = recognition.crnn_mobilenet_v3_large(pretrained=True)
push_to_hf_hub(
    model,
    model_name="doctr-crnn-mobilenet-v3-large-example-v1",
    task="recognition",
    arch="crnn_mobilenet_v3_large",
)
```

Important caveats:

- `login_to_hub()` uses an existing Hub token when available; otherwise it triggers interactive login. It also checks for Git LFS and raises an error if Git LFS is missing.
- `push_to_hf_hub` requires either `arch=...` or `run_config=...`; missing both raises `ValueError`.
- Supported `task` values are `classification`, `detection`, `recognition`, `layout`, and `table_structure`.
- The `arch` must be valid for the selected task; a recognition architecture cannot be pushed as a detection task.
- Repository creation uses non-overwrite behavior. Existing repositories are not overwritten by this wrapper.
- The wrapper creates a model repository using the configured Hub identity and token. If the user needs privacy settings, organization placement, repository reuse, or advanced metadata, plan that explicitly before calling the helper.
- Loading and pushing are PyTorch-model workflows in this code path; do not advertise TensorFlow, ONNX, or arbitrary file layouts as compatible with `from_hub` unless separately implemented.

## Credential policy

For any task involving private Hub repos or publishing:

1. ask the user to confirm that they want authentication or publishing side effects;
2. prefer an already-configured token/session or environment-managed credentials;
3. never request that a raw token be pasted into a generated runtime file;
4. never log tokens, command histories containing tokens, or full private repository URLs with embedded credentials;
5. record whether the operation was only planned, dry-run inspected, or actually executed.
