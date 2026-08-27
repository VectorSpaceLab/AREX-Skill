# Document Output Troubleshooting

## JSON Validation or Version Mismatch

Symptoms:

- Loading exported JSON fails validation.
- A helper says it cannot validate as `DoclingDocument`.
- Fields differ from examples or expected schema names.

Likely causes and fixes:

- The JSON was produced by a different `docling-core` schema version. Re-export with the currently installed Docling package when possible.
- The file is a `ConversionAssets` archive component or other wrapper, not a raw `DoclingDocument` JSON. Locate the inner `document.json` or export with `doc.save_as_json(...)` / `doc.export_to_dict()`.
- The JSON was manually edited or truncated. Validate that it has `schema_name`, `version`, `name`, `body`, `texts`, `tables`, and `pictures` fields as applicable.
- Use the bundled table helper with best-effort fallback when exact validation is not required.

## Referenced Images Are Missing

Symptoms:

- Markdown or HTML contains image links, but files are not present.
- JSON/YAML references images that downstream tooling cannot resolve.
- Page, table, or picture image exports are empty.

Fixes:

- Confirm images were generated during conversion. For PDF image outputs, set `PdfPipelineOptions.generate_page_images=True` and/or `generate_picture_images=True` before conversion.
- Use `ImageRefMode.EMBEDDED` when the output must be a single portable file and size is acceptable.
- Use `ImageRefMode.REFERENCED` only when the output directory and referenced image files are delivered together.
- Use `ImageRefMode.PLACEHOLDER` for text-only outputs or when images are intentionally excluded.
- Some input formats and image types may not expose extractable images; for example, unsupported embedded image formats can be skipped by lower-level readers.

## Empty Tables or Pictures

Symptoms:

- `doc.tables` or `doc.pictures` is empty.
- Table CSV exports have no rows or columns.
- Picture crops cannot be saved.

Fixes:

- Check whether the upstream conversion pipeline enabled the needed enrichment. Table structure and image generation are conversion-time choices, not export-time choices.
- For tables, try `table.export_to_dataframe(doc=doc)` and inspect dataframe shape before assuming export failed.
- For JSON-only workflows, use `scripts/export_tables_from_doc.py --summary-only` to distinguish “no tables in JSON” from “tables exist but cannot be normalized into rows.”
- If tables are present as images only, route to pipeline configuration or advanced pipeline guidance; this sub-skill does not tune OCR/VLM/table detection quality.

## Tokenizer Extras for Chunking

Symptoms:

- Importing `HybridChunker` works, but tokenizer initialization fails.
- Errors mention missing HuggingFace tokenizer, OpenAI tokenizer, or `tiktoken`.
- Chunking attempts to download tokenizer/model files.

Fixes:

- With the full `docling` package, import `HybridChunker` from `docling.chunking`.
- With `docling-core` only, install the needed extra such as `docling-core[chunking]` for HuggingFace tokenizers or `docling-core[chunking-openai]` for OpenAI tokenizers.
- Use a tokenizer already available in the deployment environment, or prefetch tokenizer assets in controlled environments.
- If tokenizer dependencies are not allowed, use `HierarchicalChunker` or a Markdown-first external splitter.

## HybridChunker Length Warning

A transformers warning like “Token indices sequence length is longer than the specified maximum sequence length” can appear while `HybridChunker` counts tokens for long text. In Docling’s documented behavior, this warning can be a false alarm because the chunker may split the oversized sequence after counting it.

Verify produced chunk lengths instead of assuming failure:

```python
max_seen = 0
for chunk in chunks:
    text = chunker.contextualize(chunk)
    token_count = len(tokenizer.tokenize(text))
    max_seen = max(max_seen, token_count)
print(f"longest produced chunk: {max_seen}")
print(f"model max length: {tokenizer.model_max_length}")
```

If produced chunks are still too long, set a stricter tokenizer/max-token configuration, disable peer merging, or switch to a line-preserving chunker for structured content.

## Repeated Table Headers Create Oversized Chunks

Symptoms:

- RAG chunks from wide tables exceed the embedding model limit.
- Every split table row repeats a large header.
- Header repetition improves context but wastes too many tokens.

Fixes:

- Start with `HybridChunker(repeat_table_header=True)` for table retrieval quality.
- Add `omit_header_on_overflow=True` when rows fit without the header but overflow with it.
- Set `merge_peers=False` if neighboring table chunks are being merged into oversized chunks.
- If table line integrity matters more than document hierarchy, use line-based token chunking with a repeated prefix and overflow omission.

## Choosing the Wrong Output Contract

Common corrections:

- Need stable downstream parsing: use JSON/dict/YAML, not Markdown.
- Need compact LLM prompt context: use Markdown or strict text, not full JSON.
- Need visual page review: use HTML or split-page HTML, with image generation enabled during conversion.
- Need table analytics: use dataframe/CSV extraction, not rendered Markdown tables.
- Need retrieval chunks: use native chunkers before flattening all structure to text.
