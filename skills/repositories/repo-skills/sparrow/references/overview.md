# Sparrow overview

Sparrow is an API-first document-intelligence platform. The repo combines a Python package for visual document parsing, API services, an OCR service, agent workflows, and UI shells.

## Component map

| Component | Role | Primary inputs | Primary outputs | Owning sub-skill |
| --- | --- | --- | --- | --- |
| Sparrow Parse package | Vision/document extraction library that prepares prompts, splits PDFs, crops images, detects tables, and calls a configured VLM/OCR backend | Images, PDFs, JSON example schemas, hints, backend config | JSON strings/objects, markdown, page labels, table JSON, page counts | `document-extraction` |
| Sparrow LLM engine/API | Typer command and FastAPI service wrapping `sparrow-parse`, `sparrow-instructor`, and simple instructor pipelines | CLI args or multipart/form fields: `query`, `pipeline`, `options`, file, flags | Parsed JSON/text response, validation metadata, API errors | `api-engine-and-cli` |
| Sparrow OCR service | FastAPI wrapper around PaddleOCR post-processing | Uploaded image/PDF or URL, bbox/debug/table flags | OCR text, optional bounding boxes, processing metadata | `ocr-service` |
| Sparrow Agents | FastAPI + Prefect/Celery workflow orchestration for multi-step domain workflows | Data payloads or files plus agent name/config | Immediate result or async task id/status/result | `agent-workflows` |
| Sparrow UI | Gradio and Next interfaces over the API services | Browser uploads/forms/API calls | Interactive extraction results, dashboard/feedback views | `ui-and-deployment` |

## Typical data flow

1. A UI, CLI, API client, or agent receives a document or text instruction.
2. The LLM API or agent decides the pipeline (`sparrow-parse`, `sparrow-instructor`, or a built-in agent flow).
3. Sparrow Parse converts query intent into a VLM prompt, prepares image/PDF input, optionally applies hints, cropping, table-only extraction, OCR enhancement, markdown conversion, or page-type prompts.
4. A selected backend performs inference: MLX, vLLM/CUDA, Ollama, Hugging Face Space, Mistral API, or another model service.
5. The pipeline parses model output, optionally validates it against a generated JSON schema, and returns JSON/text.
6. Agents may chain multiple API calls, cached data, web search, or business logic.
7. UIs display results and optionally log usage or feedback through database-backed dashboard paths.

## Surfaces that look similar but are different

- `sparrow-parse` package internals and Sparrow LLM API are not the same surface. Use package guidance for direct extraction code; use API/CLI guidance for `curl`, form fields, and service ports.
- OCR service is a preprocessing/text-extraction service. VLM structured extraction belongs to Sparrow Parse or the LLM API.
- Agents call Sparrow services and add domain workflows; they are not replacements for backend setup.
- UI failures often originate in backend services or database logging, not just frontend code.

## Backend model families

- **MLX:** Apple Silicon local models. Not applicable on Linux hosts.
- **vLLM/CUDA:** NVIDIA-oriented production inference. Requires compatible GPU, drivers, Python/package versions, and downloaded/served models.
- **Ollama:** Local daemon/model workflow. Requires `ollama serve` and pulled multimodal/text model names.
- **Hugging Face Spaces:** Remote Gradio client workflow. Requires reachable Space and any needed token.
- **Mistral:** Cloud OCR/VLM/text workflow. Requires API key and network access.
- **PaddleOCR:** OCR service runtime. May download/load OCR models and requires image/PDF dependencies.

Use the root checker and sub-skill smoke scripts to validate request construction and pure parsing before running backend-heavy inference.
