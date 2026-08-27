---
name: preprocessing-and-symbols
description: "Routes pyts sample-wise preprocessing, approximation, symbolic
  discretization, and bag-of-words workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# preprocessing-and-symbols

Use this sub-skill when a user needs to scale, impute, discretize, approximate,
or symbolically encode univariate time series.

## What this covers

- Sample-wise preprocessing: `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`,
  `RobustScaler`, `PowerTransformer`, `QuantileTransformer`,
  `KBinsDiscretizer`, `InterpolationImputer`.
- Approximation and symbolic transforms: `PiecewiseAggregateApproximation`,
  `SymbolicAggregateApproximation`, `DiscreteFourierTransform`,
  `MultipleCoefficientBinning`, `SymbolicFourierApproximation`.
- Bag-of-words helpers: `WordExtractor`, `BagOfWords`.
- Shape, dtype, binning, and window-size constraints that make later modeling
  workflows predictable.

## What this excludes

- Dataset loading: use `../datasets-and-loaders/SKILL.md`.
- Feature extraction, images, and decomposition: use
  `../feature-extraction-and-images/SKILL.md`.
- Metrics and classifiers: use `../metrics-and-classifiers/SKILL.md`.
- Multivariate wrappers: use `../multivariate-workflows/SKILL.md`.

## Start here

1. Read `references/workflows.md` for the safe end-to-end recipes.
2. Read `references/api-reference.md` for the verified signatures and key
   parameter defaults.
3. Read `references/troubleshooting.md` when a preprocessing or symbolic call
   fails on NaNs, shapes, or invalid bin/window settings.
4. Run `scripts/smoke.py` to confirm the installed package and the symbolic
   workflow on tiny arrays.

## Useful triggers

- "scale each time series independently"
- "impute missing values in a time series"
- "PAA/SAX/DFT/Bag-of-Words"
- "how do I discretize time series before classification?"
- "why does BagOfWords reject my input shape?"

## Routing hints

- If the user wants a reusable symbolic feature representation, stay here long
  enough to choose the right transform and then route to the feature or
  classifier sub-skill if modeling is the real end goal.
- If the user is asking about `WordExtractor` or `BagOfWords`, remember that
  list-like symbolic input works better than an object array wrapper.
- If the user needs a downstream classifier or image transform, do not bury
  that logic here; hand off to the owning sub-skill.

## Links

- Read `references/workflows.md` for the most common recipes.
- Read `references/api-reference.md` for the verified public signatures.
- Read `references/troubleshooting.md` for NaN, constant-array, and binning
  errors.
- Run `scripts/smoke.py` for a quick installed-package smoke test.
