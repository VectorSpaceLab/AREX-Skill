---
name: document-extraction
description: "Use Sparrow Parse for structured extraction from images and PDFs
  with schemas, page types, table/markdown flows, hints, crop/annotation
  options, and pluggable VLM backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# document-extraction

Use this sub-skill when the task is to extract structured JSON, markdown, page type labels, or table data from image/PDF documents through Sparrow Parse.

## Route first

- Use this sub-skill for Sparrow Parse package calls, query/schema construction, page-type detection, markdown/table extraction choices, crop/annotation flags, and backend selection.
- Route FastAPI endpoints, multipart forms, curl commands, and service request construction to `api-engine-and-cli`.
- Route OCR service endpoint operation to `ocr-service`.
- Route UI upload/operation/deployment questions to `ui-and-deployment`.
- Route Sparrow Agents orchestration to `agent-workflows`.

## Operating checklist

1. **Choose the execution surface.** Prefer direct `sparrow-parse` package calls for code-level extraction; use the Sparrow engine/CLI only when the user is already operating that interface. The package console command named `sparrow-parse` is broken upstream; use package imports or `python -m sparrow_parse` for the package self-message.
2. **Build the query.** For schema extraction, pass valid JSON examples such as `{"invoice_number":"str","total":0.0}` or arrays of objects. Use `"*"` for generic all-data extraction. Use page-type candidates with `"*"` only when the task is page classification.
3. **Select backend and model.** Confirm one supported backend method and model/space/API credential before constructing inference. See [references/backend-options.md](references/backend-options.md).
4. **Choose document flow.** For ordinary image/PDF extraction, call `VLLMExtractor.run_inference`. For table-only crops, set `tables_only`; for markdown-first extraction, use the two-stage markdown flow. See [references/document-workflows.md](references/document-workflows.md).
5. **Use safe local helpers before expensive inference.** Build and validate prompts with [scripts/parse_request_builder.py](scripts/parse_request_builder.py). Run the no-model fixture smoke in [scripts/parse_input_smoke.py](scripts/parse_input_smoke.py) before testing a real backend.
6. **Diagnose failures.** Separate invalid user query JSON, invalid model JSON output, backend setup, PDF/poppler, table model downloads, and crop/debug artifacts. See [references/troubleshooting.md](references/troubleshooting.md).

## Key contracts to remember

- `sparrow-parse==1.5.6` exposes `InferenceFactory(config).get_inference_instance()` and `VLLMExtractor().run_inference(...)`.
- `run_inference` returns `(results, num_pages)` and does not itself run schema validation; validation and page-number wrapping are performed by the Sparrow Parse pipeline layer.
- Valid backend methods are `huggingface`, `local_gpu`, `mlx`, `ollama`, `vllm`, and `mistral`; `local_gpu` is a placeholder unless a model is supplied outside the default factory path.
- `validation_off`, `tables_only`, and `apply_annotation` are parsed from extra backend options in the pipeline layer. Page-type, annotation, instruction, validation-query, markdown, and generic `"*"` flows bypass normal schema validation.
- PDF inputs are split into page images before VLM inference; poppler is required for PDF-to-image conversion.
