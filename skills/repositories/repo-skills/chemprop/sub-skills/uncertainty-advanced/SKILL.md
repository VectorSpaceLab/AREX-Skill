---
name: uncertainty-advanced
description: "Route advanced Chemprop workflows for uncertainty estimation,
  calibration, conformal evaluation, Ray Tune hpopt, model conversion,
  transfer/foundation starts, and interpretation planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Uncertainty and Advanced Workflows

Use this sub-skill when the user needs Chemprop 2.2.x uncertainty outputs or advanced workflow routing around `chemprop predict`, `chemprop hpopt`, `chemprop convert`, transfer/foundation starts, or interpretation. Keep basic `chemprop train` command construction in `training-cli`, prediction mechanics in `prediction-fingerprints`, and Python model internals in `python-api-modeling`.

## Route Here For

- Selecting `--uncertainty-method`, `--calibration-method`, and `--evaluation-methods` for prediction-time uncertainty.
- Checking compatibility between uncertainty estimators and training task types such as `regression-mve`, `regression-evidential`, `regression-quantile`, `classification-dirichlet`, and `multiclass-dirichlet`.
- Designing calibration datasets and matching calibration feature side files to test/prediction inputs.
- Adding conformal prediction coverage checks for regression, multilabel classification, or multiclass classification.
- Planning Ray Tune hyperparameter optimization with `chemprop hpopt` and optional dependency caveats.
- Converting older model artifacts with `chemprop convert`, then routing converted models into prediction with the correct featurizer mode.
- Triaging transfer learning, foundation initialization, and interpretation workflows when they affect advanced Chemprop routing.

## Route Elsewhere

- Ordinary `chemprop train` commands, task/loss/metric basics, split handling, ensembles, replicates, and output layout: use `../training-cli/SKILL.md`.
- Plain `chemprop predict` or `chemprop fingerprint` command mechanics, output suffixes, model path discovery, and fingerprint layer selection: use `../prediction-fingerprints/SKILL.md`.
- Programmatic construction of Chemprop datasets, MPNN modules, predictors, metrics, or Lightning loops: use `../python-api-modeling/SKILL.md`.
- Deep schema design for reaction, multicomponent, atom/bond, constraint, or descriptor inputs: use the data and specialized task sub-skills when present.

## Fast Uncertainty Patterns

Regression MVE with calibration and evaluation:

```bash
chemprop predict \
  --test-path test.csv \
  --model-path runs/mve/model_0/best.pt \
  --output test_mve_unc.csv \
  --uncertainty-method mve \
  --cal-path calibration.csv \
  --calibration-method zscaling \
  --evaluation-methods nll-regression miscalibration_area ence spearman
```

Ensemble variance from multiple model files:

```bash
chemprop predict \
  --test-path test.csv \
  --model-paths runs/ensemble/model_0/best.pt runs/ensemble/model_1/best.pt \
  --output ensemble_unc.csv \
  --uncertainty-method ensemble
```

Quantile conformal regression:

```bash
chemprop predict \
  --test-path test_with_targets.csv \
  --model-path runs/quantile/model_0/best.pt \
  --output conformal_intervals.csv \
  --uncertainty-method quantile-regression \
  --cal-path calibration.csv \
  --calibration-method conformal-regression \
  --conformal-alpha 0.1 \
  --evaluation-methods conformal-coverage-regression
```

## Required Reading

- `references/uncertainty.md`: estimator, calibrator, evaluator aliases; compatibility rules; output interpretation; calibration feature alignment.
- `references/hyperparameter-optimization.md`: `chemprop hpopt` command design, Ray Tune controls, search-space pruning, and optional dependency failures.
- `references/conversion-transfer-interpretation.md`: `chemprop convert`, v1 featurizer requirements, transfer/foundation routing, and interpretation triage.
- `references/troubleshooting.md`: fixes for missing hpopt dependencies, calibration mismatches, evaluator target requirements, method/task incompatibility, conformal alpha, conversion, and foundation model issues.
- `scripts/chemprop_uncertainty_args.py`: self-contained planner that validates common uncertainty/hpopt/convert flag combinations without importing Chemprop.

## Decision Checklist

1. Identify the trained model family before choosing uncertainty flags: plain regression/classification, MVE, evidential, quantile, Dirichlet, dropout, or ensemble.
2. Decide whether uncertainty is raw, calibrated, or conformalized; calibration requires `--cal-path` plus matching parsing and feature flags for calibration data.
3. Add `--evaluation-methods` only when the prediction/test CSV includes target labels that match model output columns.
4. For `ensemble`, pass at least two model artifacts; for `dropout`, choose `--uncertainty-dropout-p` and `--dropout-sampling-size` deliberately.
5. Use hpopt for training hyperparameter search, then apply the generated `best_config.toml` in a later `chemprop train` run.
6. Use `chemprop convert` before inference only for older model artifact formats; v1-to-v2 converted models need v1 atom featurization at prediction time.
7. When foundation or transfer initialization is part of the plan, confirm checkpoint/foundation exclusivity and freeze semantics before adding hpopt or uncertainty layers.

## Evidence Base

This sub-skill distills Chemprop 2.2.3 behavior from the uncertainty estimator/calibrator/evaluator registries, prediction-time uncertainty CLI implementation, hpopt and convert CLI implementations, public hpopt/convert tutorials, uncertainty and hpopt notebook recipes, transfer/foundation examples, interpretation examples, and unit tests for uncertainty utilities and conversion. Runtime content is self-contained and does not require reopening repository docs, examples, or tests.
