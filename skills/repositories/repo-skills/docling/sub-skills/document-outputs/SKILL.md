---
name: document-outputs
description: "Export DoclingDocument content to Markdown, JSON, YAML, HTML,
  text, DocTags, WebVTT, table files, images, and RAG chunks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Document Outputs

Use this sub-skill after a `ConversionResult` or `DoclingDocument` already exists and the task is about exporting, serializing, extracting tables/pictures, or chunking content for downstream use.

Do not use this sub-skill to obtain a conversion result, tune extraction pipelines, or call remote service chunking APIs; route those to the conversion, pipeline configuration, advanced pipeline, or remote service sub-skills.

## Fast Routes

- For document file/string exports, use `references/export-and-serialization.md`.
- For table and picture post-processing, use `references/export-and-serialization.md` and the bundled `scripts/export_tables_from_doc.py` helper.
- For RAG chunking with `HybridChunker`, `HierarchicalChunker`, or line-based token chunking, use `references/chunking.md`.
- For JSON validation, referenced images, empty tables/pictures, tokenizer extras, oversized chunks, and repeated table headers, use `references/troubleshooting.md`.

## Output Checklist

1. Start from `result.document` or a loaded `DoclingDocument`; conversion setup is out of scope here.
2. Choose the output contract first: human-readable Markdown/HTML/text, machine-readable JSON/YAML/dict, model-oriented DocTags/DocLang, caption-oriented WebVTT, or chunk objects for RAG.
3. Preserve images only when conversion generated images and the export `ImageRefMode` matches the delivery target.
4. For tables, prefer `table.export_to_dataframe(doc=doc)` when Python post-processing is available; use the bundled helper when only Docling JSON is available.
5. For RAG, tune `HybridChunker` around the embedding tokenizer and table-header behavior before changing the upstream conversion pipeline.
