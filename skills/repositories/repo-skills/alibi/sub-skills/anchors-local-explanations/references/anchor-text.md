# AnchorText Details

## Purpose

Read this file when the user wants a text anchor or when the text sampling strategy needs to be chosen.

## Text sampling strategies

| Strategy | Meaning | Extra / dependency note |
| --- | --- | --- |
| `unknown` | Replace disturbed tokens with unknown-token style perturbations | works with the spaCy path when a model is available |
| `similarity` | Replace disturbed tokens with similar words | needs spaCy support and a loaded language model |
| `language_model` | Mask and refill disturbed tokens with a language model | belongs to the TensorFlow extra |

## Text-specific contract

- The predictor should accept a batch of raw strings, not token ids or numpy vectors.
- The explainer is called on a single text instance, not on a batch of pre-tokenized arrays.
- The `sampling_strategy` must match the initialization arguments you provide.
- The explanation exposes anchor words plus precision and coverage.

## When a text anchor fails

- If spaCy import or model loading fails, run `scripts/check_spacy_model.py`.
- If the user asked for language-model sampling, point them to the TensorFlow extra.
- If the returned anchor is empty or huge, the instance may be near a decision boundary or the dataset may be imbalanced.

## Read next

- `troubleshooting.md` for concrete symptom / cause / recovery notes.
- `scripts/check_spacy_model.py` for a safe no-download model check.
