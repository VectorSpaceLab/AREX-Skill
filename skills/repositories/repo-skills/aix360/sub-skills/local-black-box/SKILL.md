---
name: local-black-box
description: "Guide local post-hoc explanations for black-box predictors on
  tabular, text, image, and generic structured inputs with AIX360 0.3.0
  wrappers, output checks, and local metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Local black-box explanations

Use this route when the user wants a local, post-hoc explanation of an already
trained predictor: LIME, SHAP, feature attribution, GroupedCE/ICE, nearest-
neighbor contrastive examples, faithfulness, monotonicity, or an explanation
visualization. Start by identifying the input representation, the model output
contract, and whether the requested result is an attribution, a perturbation
curve, or a contrastive exemplar.

## Choose the method

- **Tabular or generic structured classification/regression:** use
  `LimeTabularExplainer` for a sparse local surrogate, `KernelExplainer` for
  model-agnostic SHAP values, or `GroupedCEExplainer` for numeric ICE/GCE
  perturbation curves. Use a scalar target-output callable for one class or a
  regressor.
- **Text:** use `LimeTextExplainer` with a callable that accepts a list of raw
  strings and returns a two-dimensional class-probability matrix. Use SHAP's
  own text-compatible model-specific API only when that optional SHAP version
  supports it; AIX360's `KernelExplainer` wrapper does not tokenize text for
  you.
- **Image:** use `LimeImageExplainer` with a batch image classifier callable.
  It returns a LIME `Explanation`; use its mask accessor for visualization.
  SHAP `DeepExplainer` or `GradientExplainer` is a model/backend-specific
  alternative, not a drop-in image adapter.
- **Contrastive structured examples:** use
  `NearestNeighborContrastiveExplainer` when a learned embedding and examples
  from a different predicted class are useful. It is not recourse: it does
  not promise feasible, actionable, or minimal changes.
- **Feature-effect inspection:** use GroupedCE with one numeric feature for
  ICE, or several selected numeric features for pairwise GCE grids. It is
  model-agnostic but needs a representative reference data frame.

Read [API reference](references/api-reference.md) for exact signatures and
shapes, [workflows](references/workflows.md) for self-contained recipes, and
[troubleshooting](references/troubleshooting.md) before changing dependencies.
The bundled [output checker](scripts/check_model_output.py) validates the
most common callable contracts without downloading data or importing an
optional backend.

## Common callable contract

Validate the callable independently before constructing an explainer. For
classification, `predict_proba(X)` must preserve the batch axis and return
`(n_rows, n_classes)`; class names must have exactly `n_classes` entries. Do
not pass integer labels, a one-dimensional probability vector, or a single
class column to a LIME classification callable without adapting it. For a
single target output, use a callable such as
`lambda X: model.predict_proba(X)[:, target_class]` and validate the resulting
`(n_rows,)` scores for SHAP/GroupedCE as appropriate. For NN contrastive, the
model callable must return integer-like class labels, not probabilities.

For a single row, retain a two-dimensional input when the model expects a
batch (`X[[i]]`, not `X[i]`). Text classifier callables receive a list of
strings. Image classifier callables receive a batch/list of images. Keep
feature order, sparse representation, preprocessing, feature names, and
class order identical between the model and the explainer.

## Validate and report

1. Record input type/shape, feature names or token/image convention, model
   callable, class order, background/reference data, random seed, and optional
   dependency status.
2. Run a tiny prediction probe, then construct the chosen wrapper and explain
   one deliberately selected instance.
3. Check the returned structure rather than only printing it: LIME
   `Explanation.as_list(label=...)` or `as_map()`, SHAP value dimensions and
   class axis, GroupedCE grid lengths, or contrastive neighbor/distance
   alignment.
4. If explaining a classifier, compare the selected output class with the
   model's prediction. Use `faithfulness_metric` and
   `monotonicity_metric` only with aligned one-row feature arrays and a model
   exposing `predict_proba`; see the metric caveats in the references.
5. Report approximation, sampling, background-data, segmentation, and
   dependency limits. A plot is a presentation of an explanation, not proof
   of faithfulness.

## Boundaries and routes

- CEM, recourse, certification, GLANCE, or OT matching: route to
  [counterfactual-and-certification](../counterfactual-and-certification/SKILL.md).
- ProtoDash, rule induction, IMD, or TED: route to
  [interpretable-models](../interpretable-models/SKILL.md).
- TSICE, TSLime, or TSSaliency: route to
  [time-series](../time-series/SKILL.md).
- Dataset constructors, downloads, or dataset lifecycle: route to
  [datasets-and-metrics](../datasets-and-metrics/SKILL.md). Local explanation
  metrics themselves are covered here because their arguments must align with
  the selected explanation.

This route does not promise that every optional backend is installable on a
modern Python environment. LIME is an independent optional extra; SHAP and
GroupedCE require SHAP; NN contrastive fitting requires TensorFlow. The
historical package metadata also names incompatible legacy TensorFlow/Keras
stacks for some SHAP/neural paths. If an import or backend probe fails, retain
that failure in the report and follow the recovery matrix rather than silently
substituting a different method.
