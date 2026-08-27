---
name: deidentification-privacy
description: "Router for local-first PII and PHI extraction, de-identification,
  reversible re-identification, date shifting, surrogate generation,
  streaming/batch redaction, and audit-safe outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# De-identification and privacy

Use this sub-skill for local-first PII/PHI workflows that need:
- `extract_pii` spans, labels, offsets, and confidences;
- `deidentify` text redaction with masking, removal, replacement, hashing, date shifting, or format-preserving output;
- `reidentify` when an authorized mapping is available;
- policy profiles, surrogate generation, patient-keyed date shifts, audit-safe outputs, multilingual or code-mixed identifiers, and no-PHI logging;
- document, streaming, and batch redaction over synthetic or authorized text.

## Go here first

- Need entity interpretation, model selection, or clinical grounding? Use sibling `clinical-extraction-grounding`.
- Need table/row release risk or structured de-identification? Use sibling `structured-risk-evaluation`.
- Need OCR or document intake before redaction? Use sibling `multimodal-document-intake`.
- Need service, adapter, or FHIR/OMOP handoff? Use sibling `interoperability-serving`.

## Core surfaces

- Top-level APIs: `extract_pii`, `deidentify`, `reidentify`
- Privacy helpers: `openmed.core.anonymizer`, `openmed.core.date_shift`, `openmed.core.surrogate_vault`
- Long-text helpers: `openmed.core.document_stream`, `openmed.core.streaming`
- Batch helpers: `openmed.processing.BatchProcessor`

## Default operating rules

- Keep inputs synthetic or already authorized.
- Prefer local loaders, cached checkpoints, and explicit policy names.
- Never log raw source text, mappings, prompts, or PHI-bearing outputs.
- If the task needs re-identification, treat the mapping as sensitive as the source.
- For long documents, stream or batch rather than loading everything into memory.

## Bundled references

- `references/privacy-workflows.md`
- `references/api-reference.md`
- `references/troubleshooting.md`
- `scripts/deidentify_synthetic_note.py`
