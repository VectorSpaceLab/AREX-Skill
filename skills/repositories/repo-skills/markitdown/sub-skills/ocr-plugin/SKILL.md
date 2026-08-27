---
name: ocr-plugin
description: "Use and troubleshoot the markitdown-ocr LLM Vision plugin for OCR
  in PDF, DOCX, PPTX, and XLSX conversions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MarkItDown OCR Plugin

Use this sub-skill when a task needs `markitdown-ocr`, the MarkItDown plugin that inserts LLM Vision OCR text from images embedded in PDF, DOCX, PPTX, and XLSX files.

## Start Here

- For installation, plugin discovery, safe no-credential checks, Python and CLI usage, supported formats, and converter priority behavior, read [references/workflows.md](references/workflows.md).
- For plugin entry points, `LLMVisionOCRService`, OCR converter classes, constructor kwargs, output blocks, and warning/fallback semantics, read [references/api-reference.md](references/api-reference.md).
- For missing OCR blocks, undiscovered plugins, missing `llm_client` or `llm_model`, API warnings, scanned PDFs, and format-specific image extraction limits, read [references/troubleshooting.md](references/troubleshooting.md).
- To verify import and discovery without real LLM calls, run `python scripts/check_ocr_plugin.py --require-entry-point` from this sub-skill directory.

## Routing Boundaries

- Use this sub-skill for the `markitdown-ocr` distribution, the `ocr` plugin entry point, `MarkItDown(enable_plugins=True, llm_client=..., llm_model=...)`, `llm_prompt`, `LLMVisionOCRService`, and OCR-enhanced PDF/DOCX/PPTX/XLSX converters.
- Route generic plugin authoring, custom `DocumentConverter` design, and non-OCR plugin debugging to `../plugin-development/SKILL.md`.
- Route ordinary built-in conversion, stream/path/URI APIs, non-plugin CLI use, and core MarkItDown exceptions to `../core-conversion/SKILL.md`.
- Route Azure Document Intelligence or Azure Content Understanding extraction to `../cloud-integrations/SKILL.md`.
- Do not make real LLM calls unless the user supplies credentials, an OpenAI-compatible vision client, and explicit approval for network/API use.

## Quick Checklist

1. Install `markitdown-ocr` in the same environment that runs `markitdown`; install an OpenAI-compatible client package separately when real OCR is needed.
2. Confirm discovery with `markitdown --list-plugins` or `python scripts/check_ocr_plugin.py --require-entry-point`.
3. Enable plugins and pass both `llm_client` and `llm_model` to `MarkItDown(...)`; without both, the plugin still loads but OCR text is skipped or falls back to standard conversion.
4. Expect OCR text to appear as `*[Image OCR] ... [End OCR]*` blocks; absence of those blocks means no OCR text was inserted.
5. Treat LLM/API failures as non-fatal warning conditions: conversion should continue, but the affected image contributes no OCR text.
