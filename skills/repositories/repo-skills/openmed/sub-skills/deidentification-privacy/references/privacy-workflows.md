# Privacy workflows

This sub-skill owns local-first PII/PHI extraction, de-identification, reversible re-identification, date shifting, surrogate generation, audit-safe outputs, and no-PHI logging. Keep the text synthetic unless the caller explicitly supplies an authorized real dataset and the right downstream approvals.

## Quick decision guide

| Need | Start with | Notes |
| --- | --- | --- |
| Detect spans and labels | `extract_pii` | Returns offsets, labels, and confidence for later review. |
| Redact text | `deidentify` | Supports `mask`, `remove`, `replace`, `hash`, `shift_dates`, and `format_preserve`. |
| Restore a redacted note | `reidentify` | Use only with the mapping returned by the same de-identification result. |
| Generate stable fake values | `method="replace"` plus `consistent`, `seed`, or `SurrogateVault` | Best when downstream tools still expect plausible values. |
| Shift dates while keeping intervals | `method="shift_dates"` | Use a patient key plus secret for stable offsets across documents. |
| Process a very long document | `DocumentStreamDeidentifier` or `deidentify_document_stream` | Keeps memory bounded while preserving global offsets. |
| Process many notes or files | `BatchProcessor(operation="deidentify")` | Adds progress, checkpoints, and resume support. |
| Redact tabular free-text columns | `openmed redact-dataset` | Produces PHI-free summaries; use explicit text columns only. |

## Single-note workflow

Use `extract_pii` when you need a reviewable list of spans before deciding how to redact:

```python
from openmed import deidentify, extract_pii, reidentify

note = "Synthetic note: Casey Example called 555-0100 on 2026-08-12."

entities = extract_pii(note, lang="en")
redacted = deidentify(note, method="mask", keep_mapping=True, lang="en")
restored = reidentify(redacted.deidentified_text, redacted.mapping)

assert restored == note
```

If the caller only needs redacted text, `deidentify` is enough. If the caller needs both the redacted text and a later reversal, keep the mapping and protect it like source PHI.

## Date shifting

Use date shifting when relative timing matters more than the absolute date.

```python
from openmed import deidentify

result = deidentify(
    "Synthetic visit on 2026-08-12 and follow-up on 2026-08-19.",
    method="shift_dates",
    patient_key="synthetic-patient-708",
    date_shift_secret="synthetic-secret",
    date_shift_max_days=365,
)
```

Guidelines:

- Use `method="shift_dates"`; the date options are ignored otherwise.
- Supply `patient_key` plus `date_shift_secret` when you need stable offsets across sessions.
- Use `date_shift_days` for one fixed offset when patient-keyed behavior is not needed.
- Keep the same `patient_key`, secret, and `date_shift_max_days` for every document that should share an offset.
- Do not place real identifiers in the secret value.

## Surrogates and policy profiles

Use `method="replace"` when downstream tools need realistic fake data instead of placeholders.

```python
from openmed import deidentify
from openmed.core.surrogate_vault import SurrogateVault

vault = SurrogateVault.in_memory("synthetic-surrogate-secret")

result = deidentify(
    "Synthetic note: Casey Example emailed casey.example@example.test.",
    method="replace",
    consistent=True,
    seed=7,
    surrogate_vault=vault,
    lang="en",
    locale="en_US",
)
```

Use policy profiles as local deployment rules, not as a legal conclusion. Common examples in the repo include profiles such as `hipaa_safe_harbor`, `safe_harbor`, `india_dpdp_act`, and `china_pipl`. The profile controls local behavior; it does not replace an institutional privacy review.

## Batch and streaming flows

Use `BatchProcessor` when you already have a list of notes or files. Use the streaming helpers when the document is too long to hold comfortably in memory.

```python
from openmed import BatchProcessor

processor = BatchProcessor(
    operation="deidentify",
    model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1",
    method="mask",
    confidence_threshold=0.7,
)
result = processor.process_texts([
    "Synthetic note one.",
    "Synthetic note two.",
], ids=["note-1", "note-2"])
```

For a very long note, prefer sentence-window helpers:

```python
from openmed.core.document_stream import deidentify_document_stream

result = deidentify_document_stream(
    "Very long synthetic note ...",
    method="mask",
    lang="en",
)
```

For chunk-fed input, use `openmed.core.streaming.StreamingDeidentifier` and flush the final event before saving output.

## Audit-safe output and logging

- Log counts, labels, offsets, hashes, checkpoint ids, and status fields.
- Do not log raw input text, mappings, or unredacted entity text.
- Treat `audit_report`, checkpoint journals, and reversible mappings as sensitive artifacts.
- If a caller wants telemetry or review notes, keep them PHI-free and source-free.

## Routing notes

- Clinical entity interpretation belongs in `clinical-extraction-grounding`.
- Quasi-identifier release risk belongs in `structured-risk-evaluation`.
- OCR, PDF, image, or form intake belongs in `multimodal-document-intake` before redaction.
- Service exposure and interoperability handoff belong in `interoperability-serving`.
