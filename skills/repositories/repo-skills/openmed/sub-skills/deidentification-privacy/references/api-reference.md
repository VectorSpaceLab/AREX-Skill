# API reference

This reference summarizes the de-identification and privacy surfaces that the sub-skill should route to.

## Top-level APIs

### `extract_pii`

Use this when you need PII spans, labels, offsets, and confidence scores.

Key inputs:

- `text`: the note or message to analyze.
- `model_name`: a registry key or explicit checkpoint name.
- `confidence_threshold`: the minimum score to keep a span.
- `lang` and `locale`: language routing plus locale-aware behavior.
- `loader`: optional local loader or fixture loader for offline use.
- `custom_recognizer`: institution-specific allow/deny rules.
- `code_mixed`, `token_language_tags`, `lid_model`, `transliterated_name_config`: multilingual routing helpers.
- `budget`: optional cooperative limit for the request.

Output:

- A `PredictionResult` with `.entities`, `.to_dict()`, and JSON-friendly metadata.
- When pandas is available, `to_dataframe()` returns an entity table.

### `deidentify`

Use this when you need redacted text instead of only spans.

Key inputs:

- `method`: one of `mask`, `aadhaar_mask`, `remove`, `replace`, `hash`, `shift_dates`, or `format_preserve`.
- `keep_mapping`: return a reversible mapping for authorized `reidentify` use.
- `patient_key`, `date_shift_days`, `date_shift_max_days`, `date_shift_secret`: date-shift control.
- `consistent`, `seed`, `surrogate_vault`: repeatable surrogate control.
- `policy`: local policy profile name.
- `audit`: request an audit report.
- `loader`, `custom_recognizer`, `code_mixed`, `lang`, `locale`, `budget`: same role as in `extract_pii`.

Output:

- A `DeidentificationResult` with `deidentified_text`, `pii_entities`, `mapping`, `metadata`, `timestamp`, and optionally `audit_report`.

### `reidentify`

Use only with the mapping returned by the same de-identification result.

```python
from openmed import deidentify, reidentify

result = deidentify("Synthetic note: Casey Example.", method="mask", keep_mapping=True)
restored = reidentify(result.deidentified_text, result.mapping)
```

## Supporting modules

### `openmed.core.pii`

Implementation module for extraction, redaction, mappings, and audit handling.

Relevant runtime concepts:

- `PIIEntity`
- `DeidentificationResult`
- `PredictionResult`-style entity payloads
- audit and mapping helpers

### `openmed.core.anonymizer`

Locale-aware surrogate generation.

Use it when `method="replace"` needs realistic fake values.

Important surfaces:

- `Anonymizer`
- `AnonymizerConfig`
- `register_clinical_provider(provider)`
- `register_label_generator(label, generator)`

### `openmed.core.date_shift`

Stable date-shift helpers.

Important surfaces:

- `stable_offset_for(patient_key, max_days, secret)`
- `stable_offset_from_seed(seed, max_days)`
- `DEFAULT_DATE_SHIFT_MAX_DAYS`

### `openmed.core.surrogate_vault`

Cross-document surrogate storage.

Important surfaces:

- `SurrogateVault.in_memory(secret)`
- `SurrogateVault.from_file(path, hmac_secret=...)`
- `text_hash(source_text)`
- `key_for(source_text, label=..., lang=...)`
- `subject_key_for(source_identifier)`
- `configure_name_matching(...)`
- `rotate(...)`
- `save()`

Treat vault files as sensitive linkage artifacts even though they are not plaintext PHI.

### `openmed.core.document_stream`

Sentence-window de-identification for long documents.

Important surfaces:

- `DocumentStreamDeidentifier`
- `deidentify_document_stream(source, ...)`
- `iter_document_windows(source, ...)`
- `DocumentStreamResult`

Use for a single long note when you want global offsets and bounded memory.

### `openmed.core.streaming`

Chunk-fed streaming de-identification.

Important surfaces:

- `StreamingDeidentifier`
- `StreamingDeidentificationEvent`
- `StreamingBufferError`

Use when text arrives in chunks and the caller wants incremental redaction.

### `openmed.processing.BatchProcessor`

Batch and file processing over many notes.

Important surfaces:

- `operation="extract_pii"` or `operation="deidentify"`
- `continue_on_error`, `checkpoint_interval`, and `budget`
- `process_texts(...)`
- `process_files(...)`
- `process_directory(...)`
- `process_files_to_directory(...)`
- `resume_from_checkpoint(...)`
- `iter_process(...)`

Related result types:

- `BatchResult`
- `BatchItemResult`
- `BatchProgress`
- `DatasetRedactionSummary`

Useful reporting helpers:

- `BatchResult.summary()`
- `BatchResult.to_dict()`
- `BatchResult.get_successful_results()`
- `BatchResult.get_failed_results()`

## CLI families

### `openmed deid`

Single-note de-identification, redaction previews, reversible mappings, and audit-friendly one-shot output.

### `openmed pii`

PII extraction and note redaction commands, including batch processing of text and files.

### `openmed batch`

General batch processing with output files, checkpoints, and resume support. Distributed shard planning and report/resume flows belong to the same family when a workload must be split.

### `openmed redact-dataset`

Redact specific free-text columns in tabular data; columns are never inferred automatically.

### `openmed audit`

Generate audit-safe summaries and release evidence from de-identification workflows.

### Common output and resume rules

- `--output` writes machine-readable JSON or text, depending on the command.
- `--checkpoint-path` and `--checkpoint-interval` control crash-safe resume.
- `--resume` or `resume_from_checkpoint=True` only works when the same input order, output path, and configuration are reused.
- Checkpoint metadata is PHI-free; result journals are not.
- Prefer `--json` or `.to_dict()` when another tool will consume the output.
