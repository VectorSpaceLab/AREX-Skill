# Install And Environment

## Package Identity

- Distribution package: `marker-pdf`.
- Import root: `marker`.
- Public console scripts: `marker_single`, `marker`, `marker_chunk_convert`, `marker_gui`, `marker_extract`, and `marker_server`.
- Main runtime dependency family: PyTorch, Surya OCR, pdftext/pdfium, Pydantic, Transformers, and provider SDKs for optional LLM services.

## Install Variants

Use the base package for PDF/image conversion and API inspection:

```bash
pip install marker-pdf
```

Use the `full` extra only when the user needs document providers beyond the base PDF/image path:

```bash
pip install 'marker-pdf[full]'
```

The `full` extra covers optional document conversions such as DOCX, PPTX, XLSX, HTML, EPUB, and related rendering/parsing dependencies. Do not install it just to inspect basic CLI help or convert PDFs.

## Optional Surface Dependencies

| Surface | Extra packages usually needed | Notes |
| --- | --- | --- |
| Interactive GUI and extraction app | `streamlit`, `streamlit-ace` | `marker_gui` and `marker_extract` launch Streamlit and fail if `streamlit` is absent. |
| Local API server | `fastapi`, `uvicorn`, `python-multipart` | `marker_server` exposes local FastAPI endpoints and upload handling. |
| Modal deployment example | `modal` plus Modal auth/config | Cloud/network/credential surface; do not run automatically. |
| LLM enhancement | provider credentials and installed provider SDKs | See `sub-skills/llm-extraction-services/SKILL.md`. |

## Device And Backend

Marker can run on CPU, CUDA GPU, or MPS depending on the installed PyTorch and host. Use `TORCH_DEVICE` to force a device when auto-detection is wrong. For batch conversion, lower `--workers` when VRAM is tight; Marker can use several GB of VRAM per worker during conversion.

Use the bundled environment check before running expensive jobs:

```bash
python scripts/marker_environment_check.py --check-cli
```

This checks imports, distribution metadata, torch device facts, and console `--help` without loading models or converting files.

## Model And Cache Expectations

First real conversion may download or initialize model artifacts. Plan for network/cache access unless the deployment preloads models. Avoid using model-download behavior as a smoke test; prefer CLI help and import checks when validating an environment.

## Non-PDF Inputs

Marker supports PDF and image inputs in the core path. For DOCX, PPTX, XLSX, HTML, and EPUB, install the `full` extra and verify the needed provider dependencies. If an input extension is not recognized, route to `configuration-extension` for provider detection and class-path debugging.
