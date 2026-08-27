---
name: anchors-local-explanations
description: "Routes Alibi requests for AnchorTabular, AnchorText, and
  AnchorImage workflows, including sampling, segmentation, and
  precision/coverage troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Anchors for Local Explanations

Use this sub-skill when a user wants an anchor rule that explains a specific prediction on tabular data, text, or images.

## Trigger phrases

Open this sub-skill when the user mentions:

- anchors or anchor rules
- AnchorTabular, AnchorText, or AnchorImage
- precision, coverage, beam search, or `threshold`
- text sampling strategies such as `unknown`, `similarity`, or `language_model`
- image segmentation, superpixels, or custom `segmentation_fn`

## What this sub-skill owns

- `AnchorTabular`
- `AnchorText`
- `AnchorImage`
- the text sampling helpers and image-segmentation guidance needed to use them

## What it does not own

- SHAP or integrated gradients
- counterfactual methods
- confidence scores or prototype selection
- save/load guidance

## Read next

- `references/workflows.md` for the tabular / text / image route map
- `references/api-reference.md` for the verified AnchorTabular, AnchorText, and AnchorImage signatures
- `references/anchor-text.md` for text-specific sampling details
- `references/troubleshooting.md` for input-shape and dependency failures
- `scripts/check_spacy_model.py` before using a text anchor workflow
- `scripts/smoke_anchor_tabular.py` and `scripts/smoke_anchor_image.py` for safe CPU smokes

## Typical flow

1. Decide whether the anchor is tabular, text, or image.
2. Make sure the predictor accepts the input type the method expects.
3. For tabular data, fit the explainer on a representative training set.
4. For text, decide whether `nlp` or `language_model` sampling is the right perturbation strategy.
5. For images, choose a segmentation strategy that returns sensible superpixels.
6. Use the smoke scripts on tiny synthetic inputs before trying a larger example.

## Good fits

- local explanations for a single prediction
- a rule-based explanation with high precision and explicit coverage
- tabular, text, or image workflows where the user wants human-readable conditions

## Common failure signals

- the predictor is not batched or does not accept the right input type
- AnchorTabular was not fitted before `explain`
- AnchorText is missing a spaCy model or the `language_model` path is not installed
- image segmentation returns the wrong shape or type
- the result is empty or far too long because the instance sits near a decision boundary
