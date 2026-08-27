---
name: pdf-indexing
description: "Guides classic LLM-assisted PageIndex PDF tree extraction, TOC
  recovery, summaries, and document descriptions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classic PDF Indexing

Use this sub-skill when the user wants the original PageIndex PDF pipeline: TOC detection, TOC transformation, page-number reconciliation, recursive splitting, node summaries, document descriptions, or `page_index(...)` usage.

Do not use it for:

- fast no-LLM PDF extraction -> use `../flash-indexing/`
- Markdown heading trees -> use `../markdown-indexing/`
- workspace retrieval or agent tools -> use `../retrieval-client/`

## Required context

Read these shared references as needed:

- `../../references/workflows.md#classic-pdf-tree-extraction` for the end-to-end workflow.
- `../../references/api-reference.md#classic-pdf-tree-extraction` for verified signatures.
- `../../references/cli-reference.md#bundled-pageindex-cli-wrapper` for flags and examples.
- `../../references/configuration.md` for model defaults and credentials.
- `../../references/data-formats.md#pdf--flash-tree-nodes` for output shape.
- `../../references/troubleshooting.md#classic-pdf-extraction` for common failures.

## Operating flow

1. Confirm that `pageindex` imports with `python ../../scripts/check_env.py`.
2. Confirm model access. The classic PDF path uses LLM calls for TOC handling even when node summaries are disabled.
3. Use the bundled wrapper rather than a source checkout script path:

   ```bash
   python ../../scripts/pageindex_cli.py --pdf_path document.pdf
   ```

4. Tune document-size behavior with `--toc-check-pages`, `--max-pages-per-node`, and `--max-tokens-per-node`.
5. Tune output density with `--if-add-node-summary`, `--if-add-doc-description`, `--if-add-node-text`, and `--if-add-node-id`.
6. Inspect the resulting `structure` tree with 1-based inclusive `start_index` / `end_index` page ranges.

## Important behavior

- The pipeline wraps and sanitizes untrusted document text before model calls and validates physical page markers.
- TOC-with-page-number, TOC-without-page-number, and no-TOC branches are all model-backed.
- The pipeline rejects reordered or modified TOC entries returned by a model and nullifies page indexes not supported by the current chunk.
- Very broad nodes can be recursively split when they exceed configured page/token thresholds.
- The pipeline applies deterministic merge logic before final formatting.

## Common decisions

- If the user lacks model credentials, route to `../flash-indexing/` and use `--flash --no-summary` for first-pass structure.
- If the user wants every node to carry raw text, set `--if-add-node-text yes`, but warn about large JSON outputs.
- If the user wants a document summary, set `--if-add-doc-description yes` and keep summary/model access available.
- If page numbers look wrong, inspect model output stability and retry with better model settings before changing structural thresholds.
