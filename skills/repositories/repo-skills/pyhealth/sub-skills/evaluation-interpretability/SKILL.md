---
name: evaluation-interpretability
description: "Guides PyHealth metric selection, output-shape validation,
  calibration and prediction sets, fairness/generative evaluation, and model
  interpretability workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyHealth evaluation and interpretability

Use this route once a task/model has produced labels and probabilities or when
the user needs calibration, conformal/prediction sets, fairness, generative
utility/privacy, or explanations.

## Workflow

1. Record the task mode and exact `y_true`/`y_prob` shapes from
   [clinical-tasks](../clinical-tasks/SKILL.md) and
   [models-training](../models-training/SKILL.md).
2. Choose the matching metric family: binary, multiclass, multilabel,
   regression, ranking, drug recommendation, generative, fairness, or
   interpretability. Read [metrics](references/metrics-reference.md).
3. Validate thresholds, class axes, masks, and patient IDs on a deterministic
   fixture. Run `scripts/metric_smoke.py` before a real evaluation.
4. For calibration/prediction sets, reserve calibration data separately and
   read [calibration and prediction sets](references/calibration-and-prediction-sets.md).
5. For explanations, use a trained differentiable model and a meaningful
   baseline/input; read [interpretability](references/interpretability.md).
6. Report metrics with cohort, split, label definition, missingness, threshold,
   random seed, and uncertainty. A score is not clinical validation.

Read [troubleshooting](references/troubleshooting.md) for common shape,
class-balance, calibration, and explanation failures.
