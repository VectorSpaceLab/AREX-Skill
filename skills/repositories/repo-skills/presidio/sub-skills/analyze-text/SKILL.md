---
name: analyze-text
description: "Use Presidio Analyzer for text PII/PHI detection, custom
  recognizers, NLP engines, score thresholds, allow lists, and YAML-configured
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# analyze-text

Use this sub-skill for free-text Presidio Analyzer work:

- single-text or batch PII/PHI detection
- custom pattern, deny-list, and remote recognizers
- supported entities, languages, country filters, and context words
- score thresholds, allow lists, and ad hoc recognizers
- NLP engine selection and model configuration
- optional GLiNER, LangExtract, Azure AI Language, and AHDS routing

## Route elsewhere

- Text anonymization and deanonymization → sibling anonymize-text skill
- DataFrame / JSON structured workflows → sibling structured-data skill
- Image OCR / bbox redaction → sibling image-redaction skill
- CLI file or directory scans → sibling cli-scans skill
- HTTP service startup or deployment → root service reference, not this sub-skill

## Primary surface

- `AnalyzerEngine`
- `BatchAnalyzerEngine`
- `RecognizerRegistry`
- `Pattern`
- `PatternRecognizer`
- `RecognizerResult`
- `AnalyzerEngineProvider`
- `NlpEngineProvider`
- `NoOpNlpEngine`

## Preferred workflow

1. Pick `AnalyzerEngine` for one text or `BatchAnalyzerEngine` for many values.
2. Load recognizers into a `RecognizerRegistry`.
3. Choose an NLP engine:
   - default spaCy path
   - `NoOpNlpEngine` for no-download, pattern-only flows
   - Stanza / Transformers / GLiNER / LangExtract / Azure AI Language / AHDS when configured
4. Call `analyze()` with entities, thresholds, context, allow lists, or ad hoc recognizers.

## Safe bundled checks

- `scripts/analyzer_smoke.py`
- `scripts/custom_recognizer_smoke.py`

## Reference notes

- `references/api-reference.md`
- `references/recognizers-and-nlp.md`
- `references/supported-entities-and-languages.md`
- `references/troubleshooting.md`

## Fast troubleshooting

- Missing default spaCy model: install the documented default model or use `NoOpNlpEngine` with custom recognizers.
- Unsupported language or unknown entity: confirm the registry, NLP engine, and entity name all match.
- Threshold or allow-list surprise: check request-level threshold precedence and exact vs regex allow-list matching.
- Regex timeout or flags: review `global_regex_flags`, request `regex_flags`, and `REGEX_TIMEOUT_SECONDS`.
- Optional extra missing: install only the extra needed for the configured recognizer or NLP engine.
