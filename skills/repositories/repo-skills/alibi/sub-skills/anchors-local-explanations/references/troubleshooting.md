# Troubleshooting

## Predictor input type is wrong

**Symptoms**
- `AnchorTabular` or `AnchorImage` fails with a batching or shape error.
- `AnchorText` rejects the input or behaves as if the text were token ids.

**Likely cause**
- The predictor does not accept the input type that the anchor family expects.

**Fix**
- Tabular and image predictors should accept batched `numpy.ndarray` inputs.
- Text predictors should accept `List[str]` batches of raw strings.
- Re-run the matching smoke script after wrapping the predictor.

## AnchorTabular was not fitted

**Symptoms**
- `explain` fails because the explainer was never fitted.

**Likely cause**
- Tabular anchors need a representative training set before explanation.

**Fix**
- Call `fit` first with a small but representative training set.
- Use the tabular smoke helper to confirm the data layout.

## Text anchor is missing spaCy support

**Symptoms**
- `check_spacy_model.py` fails.
- The import trace points to spaCy or a missing `click` dependency.

**Likely cause**
- The text anchor path needs spaCy support and a usable language model.

**Fix**
- Repair the environment, then rerun `check_spacy_model.py`.
- If the user wants `language_model` sampling, install the TensorFlow extra.

## Image anchor segmentation fails

**Symptoms**
- `AnchorImage` errors on segmentation or superpixel masking.

**Likely cause**
- The segmentation function returned the wrong shape or type.

**Fix**
- Make sure the segmentation function returns a 2D segment-id array.
- Use a tiny custom segmentation function first, then swap in a more realistic one.

## Empty or very long anchors

**Symptoms**
- The returned anchor is empty, black, or unexpectedly long.

**Likely cause**
- The instance lies near a decision boundary or the sampling space is poorly conditioned.

**Fix**
- Lower expectations for the explanation on that instance.
- Check the data balance and sampling strategy.
- Try a different instance or a better predictor wrapper.

## Where to go next

- Read `references/workflows.md` for the modal flow.
- Read `references/anchor-text.md` for text-only sampling decisions.
- Run `scripts/smoke_anchor_tabular.py` or `scripts/smoke_anchor_image.py` to confirm the modality-specific path.
