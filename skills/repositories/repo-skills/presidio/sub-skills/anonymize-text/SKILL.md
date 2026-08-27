---
name: anonymize-text
description: "Use Presidio Anonymizer for text replacement, redaction, hashing,
  masking, encryption, decryption, custom operators, batch flows, and overlap
  handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# anonymize-text

Use this sub-skill when the text spans are already known and you need Presidio to transform them.

## Start here
1. Choose the operator map and conflict policy.
2. Pass analyzer spans into `AnonymizerEngine` or `BatchAnonymizerEngine`.
3. For reversible flows, keep the returned `OperatorResult` spans and reuse them with `DeanonymizeEngine`.

## Core APIs
- `AnonymizerEngine` for single-text anonymization.
- `DeanonymizeEngine` for decrypting or keeping text.
- `BatchAnonymizerEngine` and `BatchDeanonymizeEngine` for lists and nested dictionaries.
- `OperatorConfig`, `RecognizerResult`, `OperatorResult`, and `ConflictResolutionStrategy` for input/result plumbing.

## What this sub-skill covers
- Built-in operators: replace, redact, hash, mask, encrypt, keep, custom, decrypt, deanonymize_keep, and optional `surrogate_ahds`.
- DEFAULT precedence and entity-specific overrides.
- Overlap handling, conflict trimming, and space-merge behavior.
- Custom operator extension points.
- Safe smoke scripts in `scripts/`.
- Optional AHDS surrogation when the extra and endpoint are available.

## Route elsewhere
- PII detection, recognizers, NLP, allow-lists, or model setup → `../analyze-text/SKILL.md`
- DataFrame / JSON structured anonymization → `../structured-data/SKILL.md`
- CLI file scanning and config precedence → `../cli-scans/SKILL.md`

## Read next
- `references/api-reference.md`
- `references/operators-and-conflicts.md`
- `references/workflows.md`
- `references/troubleshooting.md`

## Smoke checks
- `python scripts/presidio_text_smoke.py --help`
- `python scripts/custom_operator_smoke.py --help`
