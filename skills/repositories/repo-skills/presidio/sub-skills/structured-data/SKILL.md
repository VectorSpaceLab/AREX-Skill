---
name: structured-data
description: "Use Presidio Structured for Pandas DataFrames, JSON-like data,
  structured mappings, processors, selection strategies, and safe CSV/batch
  recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# structured-data

Use this sub-skill when Presidio must detect or anonymize PII in structured values rather than one free-text string at a time.

## Use this for

- Pandas `DataFrame` analysis and anonymization with `PandasAnalysisBuilder` and `StructuredEngine`.
- JSON-like dictionaries/lists with `JsonAnalysisBuilder`, manual `StructuredAnalysis` mappings, and `JsonDataProcessor`.
- Choosing DataFrame entity selection strategies: `most_common`, `highest_confidence`, or `mixed`.
- Overriding automatically generated field/entity mappings when column semantics are known.
- Reusing anonymizer `OperatorConfig` maps across structured columns or JSON paths.
- Safe CSV and batch-style recipes for dictionaries of columns or small CSV files.

## Route elsewhere

- Free-text analyzer tuning, NLP engines, supported entities, recognizers, score thresholds, allow lists, or model installation → `../analyze-text/SKILL.md`.
- Operator semantics, encryption/decryption, overlap/conflict behavior, custom operators, and detailed anonymizer errors → `../anonymize-text/SKILL.md`.
- CLI scans over files/directories/stdin and CLI YAML config precedence → `../cli-scans/SKILL.md`.
- Image, OCR, DICOM, or bounding-box redaction → `../image-redaction/SKILL.md`.

## Core workflow choices

1. Identify the data shape: Pandas `DataFrame`, JSON-like object, or CSV/batch dictionary.
2. Generate or provide a `StructuredAnalysis(entity_mapping={field_or_path: entity_type})`.
3. Pick the processor: default `PandasDataProcessor` for DataFrames, `JsonDataProcessor` for JSON-like objects.
4. Build an anonymizer operator map with entity-specific entries plus a safe `DEFAULT` fallback.
5. Run `StructuredEngine.anonymize(...)`, then validate that the expected columns/paths changed and non-PII fields stayed stable.

## Read next

- `references/api-reference.md` for imports, signatures, object behavior, defaults, and mutation notes.
- `references/data-formats.md` for DataFrame, JSON path, nested-list, CSV, and manual mapping formats.
- `references/workflows.md` for DataFrame, JSON, mapping override, operator reuse, and CSV/batch recipes.
- `references/troubleshooting.md` for processor mismatches, nested arrays, wrong mappings, selection strategy issues, pandas/model requirements, and operator fallback problems.

## Safe bundled checks

- `python scripts/structured_smoke.py --help`
- `python scripts/structured_smoke.py`
- `python scripts/presidio_csv_batch_smoke.py --help`
- `python scripts/presidio_csv_batch_smoke.py`

The bundled scripts build tiny fixtures in memory or a temporary directory, use a no-download analyzer configuration, and do not assume access to this repository checkout.
