---
name: sparrow
description: "Route Sparrow document-intelligence workflows across structured
  extraction, LLM API/CLI operation, OCR, agents, UI deployment, and backend
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Sparrow

Use this repo skill for Sparrow, an API-first document-intelligence platform for structured data extraction, instruction processing, OCR, multi-agent workflows, and UI deployment around local or hosted ML/VLM/LLM backends.

## Start here

1. **Classify the task surface.** Sparrow has separate package, API, OCR, agent, and UI surfaces. Pick the nearest sub-skill below before diving into details.
2. **Check installation and services.** For package/API work, run the safe [environment checker](scripts/check_sparrow_environment.py). For request planning, use [scripts/sparrow_request_builder.py](scripts/sparrow_request_builder.py) before calling a live model.
3. **Treat model backends as explicit choices.** MLX, vLLM/CUDA, Ollama, Hugging Face Spaces, and Mistral API have different hardware, service, credential, and model-download requirements. Do not assume a visible GPU means a backend is ready.
4. **Keep schema and transport separate.** First validate the JSON query/schema and command or form-data fields; then diagnose model output, validation, or backend failures.
5. **Avoid long-running checks by default.** Full VLM/OCR/agent/UI execution can start services, download models, require credentials, or touch databases. Use bundled offline smoke scripts first.

## Sub-skill routing

| Task | Read |
| --- | --- |
| Extract JSON, markdown, page types, or tables from images/PDFs; choose MLX/Ollama/vLLM/HF/Mistral backends; debug Sparrow Parse helpers and model-output validation | [document-extraction](sub-skills/document-extraction/SKILL.md) |
| Build or translate CLI/curl/API requests; operate `/api/v1/sparrow-llm/inference` or `/instruction-inference`; debug query preparation, validation, table templates, protected access, and config | [api-engine-and-cli](sub-skills/api-engine-and-cli/SKILL.md) |
| Run or diagnose the PaddleOCR-backed OCR API, upload or URL OCR, bounding boxes, PDF first-page conversion, and experimental table-enhancement fallback | [ocr-service](sub-skills/ocr-service/SKILL.md) |
| Use Sparrow Agents sync/async API, Prefect/Celery/Redis task flows, built-in medical/trading/bonds agents, payload schemas, and cached-search/credential handling | [agent-workflows](sub-skills/agent-workflows/SKILL.md) |
| Run Gradio or Next UI shells, reason about service topology, dashboard/feedback DB paths, uploads, temporary files, and deployment smoke checks | [ui-and-deployment](sub-skills/ui-and-deployment/SKILL.md) |

## Repo-level references

- [Overview](references/overview.md) summarizes the component architecture and how data moves through Sparrow.
- [Installation and backends](references/installation-and-backends.md) records Python/package/service/backend choices and optional dependency gates.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install, import, backend, service, and schema failures.
- [Provenance](references/repo-provenance.md) records the source snapshot and evidence paths used to build this skill.

## Minimal package checks

Use these checks before expensive model or service runs:

```bash
python -m sparrow_parse
python scripts/check_sparrow_environment.py --json
python scripts/sparrow_request_builder.py extraction \
  --query '{"invoice_number":"str","total":0.0}' \
  --pipeline sparrow-parse \
  --backend ollama \
  --model mistral-small3.2:24b-instruct-2506-q8_0 \
  --file-path invoice.pdf
```

The declared package console command named `sparrow-parse` is broken in the inspected source because package metadata points to `sparrow_parse:main` while the function lives in `sparrow_parse.__main__`. Use package imports or `python -m sparrow_parse` for a package self-message, and use the Sparrow LLM engine/CLI surface for actual extraction requests.

## Common decision points

- **No model yet:** Plan the request and validate schema/options; do not call VLM, OCR, Tavily, or databases.
- **Local extraction:** Choose `document-extraction` plus backend guidance. Prefer MLX on Apple Silicon, vLLM/CUDA where installed, Ollama when a local daemon/model exists, or Mistral/HF when credentials and endpoints are available.
- **HTTP integration:** Choose `api-engine-and-cli`; verify exact form fields, comma-separated `options`, endpoint path, port, protected access, and database logging settings.
- **Pre-OCR:** Choose `ocr-service` when raw OCR text/bounding boxes are needed before VLM extraction.
- **Workflow automation:** Choose `agent-workflows`; verify the LLM API backend is reachable before debugging agents.
- **User-facing app:** Choose `ui-and-deployment`; isolate frontend upload/config errors from backend API and database failures.

## Safety and verification boundaries

- Bundled scripts are offline planners or smoke checks unless their help explicitly says otherwise.
- Full VLM inference may require model downloads, GPU/Apple Silicon/Ollama/Mistral/HF readiness, and nontrivial VRAM.
- Full OCR inference may initialize PaddleOCR and download/load model weights.
- Agent async execution requires Redis/Celery workers; bonds web search may require Tavily credentials unless cached search results are used.
- Dashboard/feedback logging can require Oracle DB settings; keep database checks read-only unless the user authorizes writes.
