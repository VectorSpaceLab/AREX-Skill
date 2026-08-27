---
name: preprocessing
description: "Use Fairlearn preprocessing mitigation with CorrelationRemover and
  PrototypeRepresentationLearner before training downstream estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn preprocessing

Use this sub-skill when the task asks to transform features before training a model: `CorrelationRemover`, `PrototypeRepresentationLearner`, sensitive columns inside `X`, fair representation learning, or a sklearn pipeline that applies unfairness mitigation before an estimator.

## Quick workflow

1. Decide whether the sensitive information is embedded as columns in `X` (`CorrelationRemover`) or supplied separately to a representation learner (`PrototypeRepresentationLearner`).
2. Split data before fitting preprocessing transformers when evaluating performance.
3. Fit the transformer on training features only.
4. Transform train/test features consistently.
5. Train the downstream estimator on transformed features.
6. Return to `../assessment/` to compare utility and disparity before and after preprocessing.

## Read these references

- [`references/workflows.md`](references/workflows.md) for API usage, sklearn pipeline patterns, parameter choices, and validation steps.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing sensitive columns, feature-count mismatches, optimizer convergence, and representation learner edge cases.
- [`scripts/smoke_preprocessing.py`](scripts/smoke_preprocessing.py) for a tiny synthetic check covering both preprocessing APIs.

## Core APIs to recognize

- `CorrelationRemover(*, sensitive_feature_ids=(), alpha=1)`: removes linear correlations between non-sensitive columns and the sensitive columns identified in `X`; output contains transformed non-sensitive features.
- `PrototypeRepresentationLearner(n_prototypes=2, reconstruct_weight=1.0, target_weight=1.0, fairness_weight=1.0, random_state=None, tol=1e-06, max_iter=1000)`: learns prototype-based representations with reconstruction, target, and fairness terms.

## Boundary rules

- This sub-skill owns preprocessing transformations only. It does not own reductions, threshold postprocessing, adversarial neural training, or dataset downloading.
- Use assessment before and after the transformer to quantify the effect. Do not claim the transformation made the model fair without subgroup metrics.
- Route model-fitting constraints to `../reductions/` if the user wants fairness-constrained training rather than feature transformation.
- Route neural adversarial representations to `../adversarial/`; `PrototypeRepresentationLearner` here is not the adversarial neural estimator.

## Operating rules

- Keep train/test leakage under control: fit preprocessing on training data and reuse it on held-out data.
- Keep sensitive-feature semantics visible even if the transformed matrix drops sensitive columns.
- For `CorrelationRemover`, pass column names when using pandas DataFrames; pass integer column indices for numpy arrays.
- For `PrototypeRepresentationLearner`, pass `sensitive_features` to `fit`/`fit_transform` when fairness weighting should use those groups.
- Treat preprocessing as one part of a pipeline. The downstream estimator still needs validation for accuracy, disparity, and calibration where relevant.

## Fast validation

Run:

```bash
python sub-skills/preprocessing/scripts/smoke_preprocessing.py
```

The smoke uses synthetic data only and does not download datasets.
