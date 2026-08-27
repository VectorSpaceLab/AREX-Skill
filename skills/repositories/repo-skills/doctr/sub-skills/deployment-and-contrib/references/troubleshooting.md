# Deployment, contrib, and Hub troubleshooting

Use this page after reading the task-specific reference. Do not start services, containers, interactive logins, or Hub pushes just to diagnose unless the user explicitly authorizes that side effect.

## Optional dependency failures

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError` for `matplotlib` or visualization fails | `viz` extra is missing | Install `python-doctr[viz]` or add `matplotlib`/`mplcursors`; needed for `Page.show()`, result visualization, demo plots, and `ArtefactDetector.show()` |
| HTML or URL document input fails around WeasyPrint | `html` extra is missing | Install `python-doctr[html]`; route pure image/PDF loading to normal `DocumentFile` APIs if HTML is not needed |
| `.contrib` module reports that `onnxruntime` is required | `contrib` extra is missing | Install `python-doctr[contrib]` or an appropriate `onnxruntime` variant for the target CPU/GPU provider |
| Streamlit demo import fails | demo-only dependencies are missing | Add Streamlit, pandas, and the `viz` extra; the demo is not part of the minimal package API |
| FastAPI upload route rejects files | missing API dependencies or unsupported MIME type | Ensure FastAPI, Uvicorn, and `python-multipart` are installed; upload as `image/jpeg`, `image/png`, or `application/pdf` |

## FastAPI template issues

| Symptom | Likely cause | Action |
|---|---|---|
| `404` or unexpected redirect for `/ocr` | routes are registered as POST handlers at the prefix root | Use `/ocr/`, `/kie/`, `/detection/`, or `/recognition/`, or use a client that follows redirects |
| Client examples use one port but the server listens on another | manual Uvicorn command and Docker Compose may use different port choices | Pick a single port per deployment and align startup command, container mapping, docs, health checks, and client URL |
| First request is very slow | `pretrained=True` may download weights and the template builds predictors during request handling | Warm the model/cache first, or cache predictors by approved parameter combinations |
| Repeated requests are slow or memory-heavy | predictors are rebuilt per request, large PDFs expand to many page images, or layout/table detection is enabled | Bound file size/page count, lower `det_bs`/`reco_bs`, disable optional layout/table work, or implement a model cache |
| `400 Unsupported file format` | upload `Content-Type` is not one of the accepted MIME types | Set multipart file MIME type correctly and avoid sending arbitrary bytes with a generic content type |
| CUDA expected but CPU is used | PyTorch reports no CUDA in the service process | Check the installed Torch build, container runtime GPU flags, driver compatibility, and `torch.cuda.is_available()` from inside the same runtime |

## Streamlit demo issues

| Symptom | Likely cause | Action |
|---|---|---|
| Demo asks to upload a document | analysis button pressed without an uploaded file | Upload a supported PDF/image before running analysis |
| Heatmap or OCR pane is empty | model failed to load, no page selected, or optional visualization dependency is missing | Check package imports, selected page, model download/cache, and `viz` dependencies |
| Layout dropdown is disabled | layout detection checkbox is off | Enable layout detection before selecting a layout architecture |
| Tables are not shown | no tables were detected or table detection was disabled | Enable table detection and verify the selected page actually contains tables; table detection adds extra model work |
| Browser demo is unsuitable for automation | Streamlit is interactive by design | Use package APIs, CLI helpers, or a FastAPI route instead |

## Docker and GPU issues

| Symptom | Likely cause | Action |
|---|---|---|
| `--gpus all` fails | Docker is not configured for NVIDIA GPUs | Install/configure the NVIDIA container runtime and retry only after user approval |
| Torch cannot initialize CUDA inside docTR image | host driver/CUDA stack is not compatible with the image CUDA base | Use a compatible host driver for CUDA 12.2-based images or run CPU-only |
| Image tag cannot be pulled | tag is outdated or unavailable | Select a current GHCR tag matching dependency set and Python/docTR version |
| Build is slow | local Dockerfile builds Python and installs docTR from a Git reference | Prefer a published image when acceptable, or set build args deliberately and budget time |
| GPU is promised but not measured | static image selection was mistaken for runtime verification | Verify from inside the container with a minimal Torch CUDA check before claiming GPU availability |

## `ArtefactDetector` issues

| Symptom | Likely cause | Action |
|---|---|---|
| Constructor fails before inference | neither default download nor local ONNX model is available | Provide network/cache access for the default model or pass a valid `model_path` |
| ONNXRuntime provider warning | CUDA provider requested but unavailable | Use CPU execution, install the correct ONNXRuntime GPU build, or adjust provider expectations |
| Empty detections | thresholds too high, wrong model/labels, wrong input shape, or no target artefacts | Lower `conf_threshold`, confirm `labels`/`input_shape`, and test with known artefact examples |
| Boxes are badly scaled | custom model input shape does not match `input_shape` | Set `input_shape` to the exported model's channel/height/width |
| `show()` fails | visualization dependencies missing or no stored results | Install `viz`, run the detector before calling `show()`, and use non-interactive plotting settings when appropriate |
| User wants oriented boxes | helper does not support OBB inference | Use a custom pipeline outside `ArtefactDetector` or postprocess a different model manually |

## Hugging Face Hub issues

| Symptom | Likely cause | Action |
|---|---|---|
| `from_hub` cannot find `config.json` or `pytorch_model.bin` | repository is not in docTR Hub format | Use a docTR-compatible repo or create files with the docTR push helper |
| Invalid architecture/task error | `config.json` has an unsupported `task` or an `arch` not registered for that task | Correct the config or use a model architecture supported by the installed docTR version |
| Private model load fails | no usable Hub token/session | Ask the user to configure credentials outside the runtime file, then pass token handling through Hub-supported kwargs |
| `login_to_hub()` fails with Git LFS error | Git LFS is not installed/configured | Install Git LFS and run its one-time setup before pushing |
| `push_to_hf_hub` raises missing `run_config or arch` | neither `arch` nor `run_config` was provided | Pass the exact architecture string or a valid training run configuration |
| `push_to_hf_hub` refuses task/arch combination | architecture does not belong to selected task | Use one of `classification`, `detection`, `recognition`, `layout`, `table_structure` and a matching architecture |
| Repository already exists | wrapper uses non-overwrite repository creation | Choose a new model name or manage the existing repo through a separate, explicit Hub workflow |
| User asks to push without authentication approval | operation has credential and publication side effects | Stop and ask for approval/configured credentials; do not run login or push implicitly |

## Safe diagnostic snippets

These snippets do not start services or push models; use them to clarify runtime state when the user allows local diagnostics.

```python
import doctr
print(doctr.__version__)
```

```python
import torch
print("cuda available:", torch.cuda.is_available())
```

```python
from importlib.util import find_spec
for name in ["weasyprint", "matplotlib", "mplcursors", "onnxruntime", "streamlit", "fastapi", "uvicorn"]:
    print(name, "installed" if find_spec(name) else "missing")
```
