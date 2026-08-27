# Chunking And Sidecars

## Dispatch Rules

Chunking is selected per document from the stored `process_options` plus frozen `chunk_options` snapshot:

- If `process_options` explicitly contains `F`, `R`, `V`, or `P`, processing dispatches to the corresponding built-in file chunker using the standardized chunker contract.
- If no chunk selector is present, processing honors `LightRAG.chunking_func` on the legacy path; the default function is fixed-token chunking.
- `chunk_options` is snapshotted at enqueue time and slimmed to the active strategy so later `addon_params` mutations do not change already-enqueued documents.
- Processing records `doc_status.metadata.chunk_method` and a compact `doc_status.metadata.chunk_opts` string reflecting the strategy and parameters actually used.

## Strategy Summary

| Selector | Function | Best fit | Key caveats |
| --- | --- | --- | --- |
| `F` | `chunking_by_fixed_token` / default `chunking_by_token_size` path | Predictable token windows; simple text inserts; separator-based splitting with optional character split. | Structural semantics are limited; no embedding cost. |
| `R` | `chunking_by_recursive_character` | Plain text, Markdown, code/log-like content, mixed Chinese/English prose, low-cost fallback. | Separator cascade is text-based and table-unaware. |
| `V` | `chunking_by_semantic_vector` | Prose where semantic shifts matter more than literal separators. | Requires a usable embedding function; no overlap parameter; over-limit results can be recursively split. |
| `P` | `chunking_by_paragraph_semantic` | Structured documents with heading/table sidecars from native, MinerU, or Docling. | Requires a `.blocks.jsonl` sidecar for full behavior; missing sidecar degrades rather than inventing structure. |

The installed `lightrag.chunker` package exports `chunking_by_fixed_token`, `chunking_by_recursive_character`, `chunking_by_semantic_vector`, `chunking_by_paragraph_semantic`, and `chunking_by_token_size`.

## Strategy Parameter Sources

The chunker snapshot is built from `addon_params['chunker']` when present, otherwise from environment-driven defaults. Strategy-specific values override legacy top-level defaults.

- `fixed_token`: `chunk_token_size`, `chunk_overlap_token_size`, `split_by_character`, `split_by_character_only`.
- `recursive_character`: `chunk_token_size`, `chunk_overlap_token_size`, `separators`.
- `semantic_vector`: `chunk_token_size`, `breakpoint_threshold_type`, `breakpoint_threshold_amount`, `buffer_size`, `sentence_split_regex`.
- `paragraph_semantic`: `chunk_token_size`, `chunk_overlap_token_size`, `drop_references`.

`P` has its own default chunk size and must not be assumed to inherit the global fixed-token size.

## Sidecar Directory Shape

Structured parsers write a LightRAG sidecar directory. The production path is a workspace-local parsed-artifact directory under the ingestion storage area; reusable guidance should refer to it conceptually, not to an absolute source checkout.

Typical files:

```text
<canonical filename>.parsed/
├── <base>.blocks.jsonl
├── <base>.drawings.json
├── <base>.tables.json
├── <base>.equations.json
└── <base>.blocks.assets/
```

`blocks.jsonl` starts with a `type="meta"` row followed by `type="content"` rows. Content rows carry `blockid`, `content`, `heading`, `parent_headings`, `level`, `session_type`, `positions`, and inline placeholder tags for tables, drawings, and equations.

## Sidecar Consumers

- Parser workers return `blocks_path` when structured sidecars exist.
- `analyze_multimodal` reads sidecar modality files and writes `llm_analyze_result` plus `llm_cache_list` into drawings, tables, or equations when the corresponding process option and runtime capability are enabled.
- `P` chunking reads `.blocks.jsonl` to align chunk boundaries with heading/paragraph/table structure.
- `F`, `R`, and `V` can backfill `sidecar.refs` onto chunks by matching output text spans to `blocks.jsonl`; this gives block-level provenance even when the chunker itself ignores structure.
- Multimodal chunks can be appended from sidecar analysis results after base text chunks are built.

## Paragraph-Semantic `P` Behavior

`P` treats each content line from `.blocks.jsonl` as a basic semantic block, then applies heading/table-aware transformations:

- Keeps small tables whole; slices large tables along JSON row arrays or HTML `<tr>` rows.
- Glues leading explanations to first table slices and trailing commentary to last slices.
- Preserves heading and `parent_headings` metadata; heading-only blocks glue forward to deeper children.
- Merges small same-branch sections without crossing parent-heading boundaries.
- Can drop references when configured by `drop_references` / `drop_rf` or `CHUNK_P_DROP_REFERENCES`.

When `.blocks.jsonl` is missing or unusable, `P` cannot infer document hierarchy and falls back toward recursive text splitting rather than pretending sidecar structure exists.

## Multimodal Flow

`i`, `t`, and `e` control whether modality sidecars are analyzed after parsing:

- `i` reads drawings and raster assets for VLM-style image analysis; non-raster formats such as WMF/EMF/SVG previews may be marked skipped.
- `t` reads table sidecars and analyzes table content with text-capable model roles.
- `e` reads equation sidecars and analyzes LaTeX/text equations with text-capable model roles.
- If no relevant option is set, if `blocks_path` is absent, or if the blocks file is missing, analysis can be marked skipped in doc-status metadata.

Provider credentials and role-specific model setup are outside this sub-skill; route those tasks to `../../llm-providers/SKILL.md`.

## Doc-Status Metadata To Watch

Useful metadata fields that survive status transitions include:

- `process_options`: original per-document option string.
- `parse_engine`: engine that ran or the encoded stored engine parameters.
- `parse_start_time`, `parse_end_time`, `parse_stage_skipped`, `parse_warnings`.
- `analyzing_start_time`, `analyzing_end_time`, `analyzing_stage_skipped`.
- `chunk_method`, `chunk_opts`, and optional `hard_fallback_split`.
- `source_file`: original pending-parse basename, separate from canonical display `file_path`.

Use these fields to explain whether a document failed in parsing, skipped multimodal analysis, used a cache-hit external parser path, changed chunk strategy, or skipped KG extraction with `!`.

## Safe Script Decision

Do not bundle maintainer-only fixture mutation helpers such as a golden-regeneration script. If a future agent needs parser debugging, document `python -m lightrag.parser.cli` as installed module behavior and keep runtime checks read-only.
