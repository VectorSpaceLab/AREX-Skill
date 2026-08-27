# Anchor Workflows

## Purpose

Use this file to choose the right anchor variant and remember the small set of inputs each one needs.

## Workflow choice

| Variant | Best for | Main inputs | Typical output |
| --- | --- | --- | --- |
| `AnchorTabular` | Tabular rules over feature ranges or categorical values | batch predictor, `feature_names`, optional `categorical_names`, training data for `fit` | anchor terms, precision, coverage |
| `AnchorText` | Token-based rules over raw text | batch predictor on `List[str]`, `nlp` or `language_model`, sampling settings | anchor words, precision, coverage |
| `AnchorImage` | Rule over superpixels in a single image | image predictor, `image_shape`, segmentation function or built-in segmentation name | anchor superpixels, precision, coverage |

## Tabular workflow

- Fit on a representative training set before explaining.
- Use `disc_perc` to decide quantile bins for continuous features.
- Keep `feature_names` and `categorical_names` aligned with the encoded columns the predictor sees.
- The explanation returns a readable rule together with precision and coverage.

## Text workflow

- The predictor should accept a batch of raw strings.
- `sampling_strategy='unknown'` replaces disturbed tokens with `UNK`-style perturbations.
- `sampling_strategy='similarity'` needs a spaCy-backed path.
- `sampling_strategy='language_model'` is the heaviest path and belongs in the TensorFlow extra.
- Use `check_spacy_model.py` before trying to debug a missing model.

## Image workflow

- The predictor should accept a single image with a channel dimension.
- The segmentation function should return a 2D array of segment ids.
- Built-in segmentation is optional; a safe custom segmentation function is often easiest for smoke tests.

## Safe usage pattern

1. Confirm the input modality.
2. Run the matching smoke helper on a tiny example.
3. If the text path is missing spaCy support, stop and repair the environment before trying again.
4. If the image path fails, check the segmentation function before tuning the explainer.

## Read next

- `anchor-text.md` for the text-specific sampling matrix.
- `troubleshooting.md` for common errors and recoveries.
- `scripts/smoke_anchor_tabular.py` and `scripts/smoke_anchor_image.py` for quick checks.
