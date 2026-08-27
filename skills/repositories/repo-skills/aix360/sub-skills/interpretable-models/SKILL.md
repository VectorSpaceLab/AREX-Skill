---
name: interpretable-models
description: "Choose and operate AIX360's directly interpretable models, rule
  learners, prototypes, model differencing, teaching explanations, and optional
  neural interpretable methods."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Interpretable models

Use this skill when the request is for a model whose prediction mechanism is
itself inspectable, a compact prototype set, an explicit rule list, a
comparison of two models, a label-plus-teaching explanation, or a conceptual
neural interpretability method. This skill covers AIX360 0.3.0 APIs and their
optional dependency boundaries.

## Route before coding

- **Explain an already trained black box with LIME, SHAP, GroupedCE, or a
  neural contrastive method:** route to `../local-black-box/SKILL.md`.
- **CEM, recourse, certification, or optimal transport:** route to
  `../counterfactual-and-certification/SKILL.md`.
- **Time-series explainers:** route to `../time-series/SKILL.md`.
- **Dataset loading, preprocessing, or metric contracts:** route to
  `../datasets-and-metrics/SKILL.md`.

Do not call a rule learner an explainer of an existing model: BRCG, GLRM,
RIPPER, CoFrNet, and TED fit a predictive mechanism from labeled data. IMD
consumes outputs from two already-fitted models. ProtoDash selects exemplars
from a candidate set and can summarize data or support a local comparison.
DIPVAE edits a learned latent generative model. ProfWeight trains a simpler
model using confidence-derived sample weights.

## Operating sequence

1. State the object being produced: prototypes, binary/regression rule model,
   DNF rules, model-difference regions, label/explanation pair, or a latent or
   confidence-profile model.
2. Freeze the training schema. Keep column names and ordering stable; retain
   the fitted `FeatureBinarizer`/`FeatureBinarizerFromTrees` for every later
   transform. Decide how missing values are represented before fitting.
3. Select the smallest dependency family in
   [api-reference.md](references/api-reference.md). Treat optional legacy
   families as unavailable unless their imports and versions are proven.
4. Fit only on training data, then predict or explain on a separately
   transformed/evaluated set. Check output shape, labels/classes, feature names,
   and rule count before interpreting the result.
5. Save a portable semantic summary (rule strings, prototype source indices and
   weights, diff regions, or latent edit settings), not an opaque live object.
6. Report accuracy/coverage or other metrics separately from readability. A
   compact model is not automatically faithful to another model.

## Fast choices

- **Prototype selection:** `ProtodashExplainer.explain(X, Y, m, ...)` returns
  `(weights, indices, objective_history)`; `Y` is the candidate pool and `X`
  is the data being summarized/explained.
- **Binary rule classifier:** binarize a pandas frame, fit
  `BooleanRuleCG` through `BRCGExplainer`, then call `predict` and `explain`.
- **Interpretable regression/classification:** use `LinearRuleRegression` or
  `LogisticRuleRegression` through `GLRMExplainer`; call `predict` (and
  `predict_proba` for logistic) and inspect the coefficient DataFrame.
- **Native rule induction:** fit `RipperExplainer` on a pandas `DataFrame` and
  `Series`, with `target_label` for a binary positive class; call `explain()`
  for a TRXF `DnfRuleSet`.
- **Model differencing:** obtain aligned predictions from two classifiers on
  the same pandas frame, fit `IMDExplainer.fit(X, y1, y2, max_depth=...)`, and
  inspect `diffrules`, `diffregions`, and `metrics`.
- **Teaching explanations:** fit `TED_CartesianExplainer(base_estimator)` on
  `(X, Y, E)` where explanation ids are dense non-negative integers; use
  `predict_explain`, `predict`, and `explain`.
- **Optional neural methods:** use CoFrNet for continued-fraction network
  structure, DIPVAE for latent edits, and ProfWeight for confidence-profile
  weighted simple models only after their backend environments are validated.

## Hard safety checks

- `FeatureBinarizerFromTrees.fit` requires `y`, rejects NaN/None during fit,
  and its transform schema is learned from selected input features. A missing
  selected column is a schema error, not a signal to silently impute.
- `BRCG` solves LPs and can emit no useful clauses; inspect `w`, `z`, and the
  `rules` list rather than assuming a non-empty explanation.
- ProtoDash weights are non-negative but unnormalized; zero, repeated, or
  numerically unstable weights need a smaller candidate set, finite scaled
  inputs, or the alternate optimizer.
- TRXF predicates use `Feature`, `Predicate`, `Conjunction`, and `DnfRuleSet`.
  Preserve typed values and operators when serializing; do not use `repr` as a
  persistence format.
- Do not promise compatibility for legacy TensorFlow/Keras 1.x ProfWeight or
  the optional PyTorch CoFrNet/DIPVAE code from a modern environment without a
  separate probe. See [troubleshooting.md](references/troubleshooting.md).

For concrete call signatures, output contracts, dependency boundaries, and
recovery procedures, read the four bundled references. The tiny smoke helper
is at `scripts/feature_binarizer_smoke.py` and is safe to run locally with
`--help` before running it.
