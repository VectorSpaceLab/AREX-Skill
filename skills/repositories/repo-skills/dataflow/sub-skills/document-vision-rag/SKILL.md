---
name: document-vision-rag
description: "Plan document/PDF/VQA/knowledge-cleaning/Agentic
  RAG/retrieval/speech/chemistry workflows, including pdf2model and PDF VQA CLI
  choices, optional MinerU/VLM/OCR backends, LightRAG retrieval, and
  training-side-effect limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Document Vision and RAG

Use this sub-skill for document-centric jobs: PDF/OCR cleanup, visual QA, Agentic RAG, retrieval over cleaned documents, speech transcription, and chemistry extraction from text/OCR output.

## Route by task

- Clean PDFs, URLs, HTML, or mixed documents into markdown or QA-ready chunks: use the workflow notes in `references/document-rag-workflows.md`.
- Decide between PDF VQA extraction, `dataflow pdf2model init --qa vqa`, `dataflow pdf2model train`, and `dataflow pdf2model chat`: use `references/pdf2model-and-vqa.md`.
- Compare API, LightRAG, MinerU, VLM, OCR, LlamaFactory, DataFlex, and audio extras: use `references/serving-and-dependencies.md`.
- Debug missing files, bad suffixes, absent credentials, GPU gaps, or training-state problems: use `references/troubleshooting.md`.

## Safe defaults

- Validate inputs before launching OCR, retrieval, or training.
- Treat MinerU, FlashMinerU, VLM, LightRAG, pdf2vqa, pdf2model, and DataFlex as optional heavy paths.
- Do not present GPU, VLM, OCR, or training behavior as CPU-verified.
- Stop when required documents, model paths, credentials, or hardware are missing; do not silently switch to a different backend.
- Use the bundled validator script for offline preflight checks.

## Bundled helper

- `scripts/check_document_workflow_inputs.py` checks document paths, PDF suffixes, JSON/JSONL columns, and requested env vars without any network call.

## Quick check

```bash
python scripts/check_document_workflow_inputs.py --profile pdf2vqa --doc sample.pdf --jsonl sample.jsonl --require-env MINERU_API_KEY
```
