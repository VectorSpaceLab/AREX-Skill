---
name: nlp-validation
description: "Route Deepchecks NLP work for TextData, labels, metadata,
  properties, embeddings, and suites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# NLP Validation

Use this sub-skill when the task is about `deepchecks.nlp.TextData`, NLP suites, labels, predictions, metadata, properties, embeddings, or offline-safe NLP smoke prep.

## Start here

- [API reference](references/api-reference.md) for constructor signatures, label formats, suite factories, and prediction/probability rules.
- [Workflows](references/workflows.md) for text classification, token classification, properties/metadata/embeddings, model evaluation, and no-download patterns.
- [Troubleshooting](references/troubleshooting.md) for NLP-specific failures.

## Use for

- `TextData(raw_text=...)` or `TextData(tokenized_text=...)`
- `task_type` and label setup for text classification, token classification, and documented multilabel text classification
- `metadata`, `categorical_metadata`, `properties`, `categorical_properties`, and `embeddings`
- `deepchecks.nlp.suites.data_integrity`, `train_test_validation`, `model_evaluation`, and `full_suite`
- `train_predictions`, `test_predictions`, `train_probabilities`, `test_probabilities`
- optional `deepchecks[nlp]` and `deepchecks[nlp-properties]` dependency guidance

## Route elsewhere

- Tabular `Dataset` work → [tabular-validation](../tabular-validation/SKILL.md)
- Vision `VisionData` work → [vision-validation](../vision-validation/SKILL.md)
- Result export, HTML/JSON, or CI gating → [results-and-integrations](../results-and-integrations/SKILL.md)
- Package install or global import troubleshooting → `../../references/troubleshooting.md`

## Safe smoke helper

- `python scripts/deepchecks_nlp_smoke.py --help`
- `python scripts/deepchecks_nlp_smoke.py --scenario text-classification --suite model-evaluation`
- `python scripts/deepchecks_nlp_smoke.py --scenario token-classification --skip-run`

## Notes

- Prefer precomputed metadata, properties, and embeddings when you need to avoid downloads or heavy model initialization.
- Prefer `tokenized_text` for token classification so label alignment stays explicit.
- Use `text` as the runtime raw-text accessor; `raw_text` is the constructor input.
