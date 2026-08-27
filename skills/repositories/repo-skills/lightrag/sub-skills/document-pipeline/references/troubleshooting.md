# Document Pipeline Troubleshooting

## Parser Service Unavailable

Symptoms:

- Routing or startup validation says a rule or filename hint requires a parser endpoint to be configured.
- A MinerU or Docling parse fails before producing sidecars.
- Parser CLI succeeds only when a raw cache already exists.

Actions:

- Confirm whether the chosen engine is local (`legacy`, `native`) or external (`mineru`, `docling`, or a third-party external parser).
- For external engines, check the relevant service endpoint/token configuration in the running LightRAG process; do not hard-code service URLs into reusable skill content.
- If the task only needs local parser debugging, choose `native` where the suffix is supported or `legacy` for plain-text extraction.
- Use `python -m lightrag.parser.cli <file> --engine <engine>` for single-file reproduction; remember that external engines still call their service on cache miss.

## Invalid Hints Or Options

Symptoms:

- `FilenameParserHintError` on upload/scan.
- `ParserRoutingConfigError` during configuration validation.
- Options silently appear absent after direct lower-level sanitization.

Actions:

- Use `[ENGINE]`, `[ENGINE-OPTIONS]`, or `[-OPTIONS]`; options-only hints must start with `-`.
- Use only `i`, `t`, `e`, `!`, `F`, `R`, `V`, and `P` in process options.
- Pick at most one chunk selector; `validate_process_options("RP")` reports an error.
- Put chunk parameters after the selector, such as `R(chunk_ts=800,chunk_ol=80)`, not on a separate token.
- Attach engine parameters only to supported external engines, such as `mineru(page_range=1-3)` or `docling(ocr=true)`.
- Prefer semicolon-separated `LIGHTRAG_PARSER` rules, for example `docx:native-teP;pdf:mineru-R;*:legacy-R`.

## Sidecar Missing Or Fallback Behavior

Symptoms:

- `P` chunking behaves like text splitting.
- Multimodal analysis is skipped.
- `sidecar.refs` are missing from chunks.
- `doc_status.metadata.analyzing_stage_skipped` is present.

Actions:

- Check whether the parser engine can produce a structured sidecar. `legacy` produces raw text and no sidecar.
- Check whether `blocks_path` was returned and whether the blocks file exists.
- For `P`, choose native/MinerU/Docling or another sidecar-producing parser; without `.blocks.jsonl`, paragraph hierarchy cannot be inferred.
- For `i` / `t` / `e`, ensure the corresponding modality sidecar actually exists and the document included that modality.
- Non-raster image assets can be skipped for VLM analysis while the rest of the document continues processing.

## Doc-Status Failures

Symptoms:

- Document is `FAILED` with a parser or processing error.
- A retry/resume reprocesses chunks unexpectedly.
- Metadata values appear to change between stages.

Actions:

- Identify `error_stage` or the latest status transition message if present.
- Read `metadata.parse_engine`, `process_options`, `parse_stage_skipped`, `analyzing_stage_skipped`, `chunk_method`, and `chunk_opts` to reconstruct what the document actually used.
- If a document was resumed with changed `process_options`, stale chunks and KG data may be purged before rebuilding so the final storage matches the current options.
- Empty parser output is a parser failure, not a successful zero-content document.
- Duplicate filename or content-hash attempts can be recorded as failed duplicate rows rather than new documents to process.

## Cancellation Or Refusal States

Symptoms:

- Upload/text insert is refused while a scan or delete is running.
- Scan refuses to start even though no parser appears active.
- Processing call returns quickly without doing work.
- Pipeline status mentions cancellation or internal halt.

Actions:

- Use `pipeline_status` fields, not `busy` alone, to explain the refusal.
- Upload/text refusal during scan classification points to `scanning_exclusive=True`.
- Upload/text refusal during clear/delete points to `destructive_busy=True`.
- Scan refusal during upload points to `pending_enqueues > 0`.
- A second process call during active processing sets `request_pending=True` and returns; this is a nudge, not a failure.
- Cancellation is cooperative; pending documents may remain for retry after the active batch halts.

## Chunker Issues

Symptoms:

- `V` is slow or fails around embeddings.
- `P` chunks are too large or too small.
- Fixed-token split options do not apply to `R`, `V`, or `P`.

Actions:

- `V` requires embeddings because it clusters sentences by semantic distance; route provider setup to `../../llm-providers/SKILL.md`.
- Use strategy-specific chunk parameters in hints/rules or `addon_params['chunker']`; already-enqueued documents keep their frozen snapshot.
- `split_by_character` and `split_by_character_only` apply only to fixed-token behavior.
- `P` has its own default size and can use `drop_references`; tune `P` separately rather than assuming global fixed-token defaults.

## Safe Local Sanity Check

From this sub-skill directory, run:

```bash
python scripts/check_pipeline_symbols.py
```

The script imports installed LightRAG symbols, validates routing/chunker APIs, and checks representative option parsing. It does not start services, call models, create storages, mutate parser artifacts, or run repository tests.
