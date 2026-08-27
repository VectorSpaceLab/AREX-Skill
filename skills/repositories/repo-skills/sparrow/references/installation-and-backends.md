# Installation and backend guide

Sparrow is split across Python packages/services and a Next UI. Choose only the dependency set needed for the user task; avoid installing every optional backend by default.

## Python and system prerequisites

- Python 3.12 is the documented target for current Sparrow workflows.
- PDF conversion uses `pdf2image` and requires Poppler tools such as `pdftoppm`.
- Full VLM inference usually needs a prepared model backend and sufficient memory.
- Agent async execution requires Redis/Celery workers in addition to the FastAPI service.
- UI dashboard/feedback features can require Oracle DB settings, while ordinary extraction uploads primarily need the backend APIs.

## Install by workflow

| Workflow | Minimum install direction | Extra prerequisites | Notes |
| --- | --- | --- | --- |
| Direct Sparrow Parse package inspection/use | `pip install sparrow-parse` or install a local package copy | Poppler for PDF splitting; backend client packages as needed | Package version inspected here was `1.5.6`. |
| MLX VLM extraction | `sparrow-parse[mlx]` on Apple Silicon | macOS arm64, MLX/MLX-VLM compatible model | Do not try to verify MLX on Linux. |
| vLLM/CUDA extraction | `sparrow-parse[linux]` or a repo-compatible vLLM environment | NVIDIA GPU, compatible driver/wheel, model files or service | CPU import does not prove vLLM extraction works. |
| Ollama extraction/instruction | `ollama` client plus Sparrow Parse/LLM API deps | Running Ollama daemon and pulled model | A connection/model list check should precede extraction. |
| Mistral/Hugging Face backends | Mistral or Gradio/HF client deps | API token or reachable Space, network | Keep tokens out of scripts and generated files. |
| LLM API/CLI | FastAPI, uvicorn, Typer, Python multipart, Sparrow Parse or Instructor deps | Optional database config only when protected/logging paths require it | Use `api-engine-and-cli` for exact fields/flags. |
| OCR API | PaddleOCR, PaddlePaddle, FastAPI, Pillow, pdf2image | Poppler for PDFs; OCR model download/runtime | Use OCR smoke script before loading models. |
| Agents API | FastAPI, Prefect, Celery, Redis client, aiohttp, domain deps | Redis server/workers; Sparrow LLM API backend; Tavily key for uncached bonds search | Web API and Celery worker register different built-ins; see `agent-workflows`. |
| Gradio UI | Gradio, requests, geolocation, DB client deps where enabled | Running LLM API; optional Oracle DB for dashboard/feedback | Validate backend service first. |
| Next UI | Node/npm package install from the Next app package metadata | Running backend APIs; optional DB-backed dashboard routes | Use `ui_config_check.py` before install/build. |

## Backend readiness checklist

Before running an expensive backend, record:

1. Backend method and model name or service endpoint.
2. Hardware/service requirement: Apple Silicon, CUDA GPU, Ollama daemon, cloud credentials, HF Space, or PaddleOCR model runtime.
3. Input type: text-only, image, PDF, table-heavy document, or multi-page document.
4. Validation mode: normal JSON schema, wildcard all-data, page-type classification, markdown, table template, instruction, validation query, or annotation.
5. Safe preliminary check: request-builder output, JSON schema validation, API route availability, or pure response parser smoke.

## Verified during skill creation

The skill was built against source evidence and a private Python 3.12 inspection environment. Verified facts translated into public guidance:

- `sparrow-parse` package metadata and import reported version `1.5.6`.
- `python -m sparrow_parse` printed the package message.
- The declared `sparrow-parse` console entry point is broken upstream because metadata points at `sparrow_parse:main`; use package imports or Sparrow LLM CLI/API for actual workflows.
- Key `sparrow_parse` classes imported for signature inspection: `InferenceFactory`, `VLLMExtractor`, `ImageOptimizer`, `PDFOptimizer`, and `TableDetector`.
- LLM FastAPI route and `engine.run` signatures were inspected without starting a service.
- Torch CUDA import saw CUDA devices in the inspection environment, but no vLLM model or VLM extraction was run. Treat CUDA/vLLM extraction as optional and unverified until the target runtime proves it.

Do not copy private environment paths, activation commands, or machine-specific details into user-facing instructions. Ask the user for their target deployment layout if a command requires a component directory.
