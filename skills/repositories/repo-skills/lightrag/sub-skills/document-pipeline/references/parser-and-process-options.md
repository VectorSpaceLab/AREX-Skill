# Parser And Process Options

## Pipeline Entry Shapes

LightRAG has two ingestion shapes that eventually enter the same pipeline:

- Raw/text inserts persist `full_docs` rows with `parse_format="raw"`; their content is already text and parser workers pass it through.
- File uploads or scans persist `full_docs` rows with `parse_format="pending_parse"`; parser workers resolve a real extraction engine, persist parsed text/sidecar data, then continue to analyze, chunk, and KG extraction.
- Previously parsed LightRAG documents use `parse_format="lightrag"` and are resumed by the internal reuse parser.
- Stored `parse_engine` wins for `pending_parse`; if absent, routing is resolved from filename/default rules. Encoded external parameters stay inside `parse_engine`, for example `mineru(page_range=1-3,language=en)`.

## Public Routing Symbols

Use these installed-package functions when code needs routing behavior instead of reimplementing parsing rules:

- `resolve_parser_directives(file_path, parser_rules=None, require_external_endpoint=True)` returns a `ParserDirectives` object with `engine`, sanitized `process_options`, canonical `chunk_params`, and canonical `engine_params`.
- `resolve_file_parser_engine(...)` returns only the chosen engine.
- `resolve_file_parser_directives(...)` returns the backward-compatible `(engine, process_options)` tuple.
- `parse_process_options(value)` returns a `ProcessOptions` view with `images`, `tables`, `equations`, `skip_kg`, `chunking`, and `chunking_explicit`.
- `validate_process_options(options)` reports unsupported characters and multiple chunk selectors.
- `encode_parse_engine(engine, params)` and `decode_parse_engine(value)` round-trip stored engine parameter syntax.
- `default_chunker_config()`, `resolve_chunk_options(...)`, `slim_chunk_options(...)`, and `chunk_strategy_key(...)` build the per-document chunk option snapshot consumed later by processing.

## Engine Selection Order

The parser engine for a file is selected in this order:

1. Final filename hint segment, such as `report.[native-P].docx`, `paper.[mineru(page_range=1-3)-iteP].pdf`, or `notes.[-R].md`.
2. First matching `LIGHTRAG_PARSER` rule, such as `docx:native-teP;pdf:mineru-R;*:legacy-R`.
3. Suffix default for native-exclusive formats such as `textpack`.
4. `legacy` fallback.

Hints strip from the canonical stored basename only when they are recognized. `canonicalize_parser_hinted_basename("a.[native-R].docx")` stores `a.docx`; nested hints strip only the final supported hint.

## Engine Syntax

- `legacy`: legacy plain-text extraction; no structured sidecar.
- `native`: local structured parser for supported native formats such as `docx`, `md`, and `textpack`; no external service.
- `mineru`: external MinerU parser for PDF/office/image-like formats; service endpoint/token configuration may be required.
- `docling`: external Docling parser for supported document/image formats; service endpoint configuration may be required.
- Third-party parsers can participate through the parser registry and `lightrag.parsers` entry points; if registered, they use the same hint/rule/CLI dispatch path.

Rules match suffixes without dots. Use `pdf:mineru`, not `*.pdf:mineru`. Rule separators may be `;` or `,`, but `;` avoids confusion because commas inside parameter blocks are parameter separators.

## Filename Hint Forms

- `[ENGINE]`: choose an engine, keep default/rule process options.
- `[ENGINE-OPTIONS]`: choose both engine and process options.
- `[-OPTIONS]`: keep the routed engine and override process options only.

Important validation behavior:

- `[iet]` is invalid because it lacks the leading hyphen; use `[-iet]` for options-only hints.
- Empty hints, unsupported engines, unsupported suffix/engine combinations, missing required external endpoints, unsupported option characters, and multiple chunk selectors fail fast on ingestion paths.
- A non-empty filename options string wholesale-overrides rule options; chunk parameters overlay per selector, with filename parameters winning over rule parameters.

## Process Option Letters

`process_options` is a compact string stored on `full_docs` and mirrored to `doc_status.metadata.process_options` when present.

| Letter | Meaning | Notes |
| --- | --- | --- |
| `i` | Analyze drawing/image sidecars | Requires sidecar-producing parser output and VLM-enabled runtime to produce successful image analysis. |
| `t` | Analyze table sidecars | Uses table sidecars and text analysis flow. |
| `e` | Analyze equation sidecars | Equations are text/LaTeX-oriented, not image VLM analysis. |
| `!` | Skip KG extraction | Chunks are still built and stored; entity/relation extraction is skipped for that document. |
| `F` | Fixed-token chunking | Default chunk selector when no explicit selector is present. |
| `R` | Recursive-character chunking | Robust low-cost choice for plain text and mixed-language prose. |
| `V` | Semantic-vector chunking | Uses embeddings to find sentence-level semantic breakpoints. |
| `P` | Paragraph-semantic chunking | Best with structured `.blocks.jsonl` sidecars from native/MinerU/Docling. |

Only one of `F`, `R`, `V`, or `P` may appear logically. `validate_process_options` reports multiple chunking modes such as `RP`; `parse_process_options` otherwise picks the first selector in raw order.

## Chunk Parameters In Hints And Rules

Attach chunk parameters to the chunk selector in parentheses:

```text
notes.[-R(chunk_ts=800,chunk_ol=80)].md
LIGHTRAG_PARSER=pdf:legacy-R(chunk_ts=800,chunk_ol=80);*:legacy-R
paper.[-P(chunk_ts=2400,chunk_ol=120,drop_rf=true)].pdf
```

Supported canonical parameters and aliases:

| Canonical | Alias | Strategies | Type | Meaning |
| --- | --- | --- | --- | --- |
| `chunk_token_size` | `chunk_ts` | `F` / `R` / `V` / `P` | integer >= 1 | Strategy-specific token target/cap. |
| `chunk_overlap_token_size` | `chunk_ol` | `F` / `R` / `P` | integer >= 0 | Overlap for strategies that support overlap. |
| `drop_references` | `drop_rf` | `P` | boolean | Drop trailing references/bibliography-like section before paragraph-semantic chunking. |

`process_options` remains a pure selector string; parsed parameter values are stored in the document's `chunk_options` snapshot.

## Engine Parameters

External parser parameters attach to the engine token and are encoded into the stored `parse_engine` value. They affect parser requests and raw-bundle cache signatures.

```text
paper.[mineru(page_range=1-3,language=en,local_pm=ocr)-P].pdf
scan.[docling(ocr=true)-R].pdf
LIGHTRAG_PARSER=pdf:mineru(language=en);*:legacy-R
```

Supported parameters:

| Engine | Canonical | Alias | Notes |
| --- | --- | --- | --- |
| `mineru` | `page_range` | `pr` | Repeat the key for multiple segments, such as `page_range=1-3,page_range=5`. Multi-segment ranges require official mode. |
| `mineru` | `language` | none | OCR/model language value such as `en` or `ch`. |
| `mineru` | `local_parse_method` | `local_pm` | Local-only enum: `auto`, `txt`, or `ocr`. |
| `docling` | `force_ocr` | `ocr` | Boolean override for OCR behavior. |

Do not attach engine parameters to `legacy` or `native`; validation rejects them.

## Parser CLI Behavior

For single-file parser debugging, use the installed module entry point:

```bash
python -m lightrag.parser.cli <input_file> --engine <engine> --preview 5
```

The CLI drives the same parser registry dispatch path as the pipeline worker for one file. It writes sidecar/raw debug outputs under the chosen output parent, does not archive the source file, and does not start the full ingestion pipeline. External-service engines still need their normal environment when the raw cache misses; a non-empty raw cache can avoid the service call in CLI mode.
