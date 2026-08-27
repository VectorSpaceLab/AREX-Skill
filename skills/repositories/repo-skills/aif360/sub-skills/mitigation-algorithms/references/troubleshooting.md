# Mitigation Algorithm Troubleshooting

Use this with [algorithm-selection.md](algorithm-selection.md), [workflows.md](workflows.md), and [optional-algorithms.md](optional-algorithms.md). Route dataset schema and metric-construction issues to [datasets-and-metrics](../../datasets-and-metrics/SKILL.md); route sklearn pipeline issues to [sklearn-interface](../../sklearn-interface/SKILL.md).

## Install/import failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Optional warnings mention TensorFlow, fairlearn, inFairness, POT, or similar. | AIF360 imports optional wrappers even when extras are absent. | If the user does not need that class, continue. If they do, install only the named extra and run a tiny smoke. |
| `DisparateImpactRemover` fails with missing `BlackBoxAuditing`. | Optional repairer dependency absent. | Install `aif360[DisparateImpactRemover]`; rerun a no-download feature-repair smoke. |
| `OptimPreproc` helper fails with missing `cvxpy` or solver errors. | `OptTools` requires convex optimization packages/solver support. | Install `aif360[OptimPreproc]`; verify `OptTools` import and a tiny optimization before full data. |
| `AdversarialDebiasing` fails with TensorFlow import, session, or eager-mode errors. | TensorFlow extra missing or wrong execution mode. | Install `aif360[AdversarialDebiasing]`; use TensorFlow v1 compatibility, disable eager execution when needed, and pass a valid session. |
| Reduction methods fail on import or constraint creation. | `fairlearn` extra missing/incompatible. | Install `aif360[Reductions]`; verify constraint names and estimator `sample_weight` support. |
| `ARTClassifier` fails before AIF360 fit. | External ART classifier/dependencies are not valid. | Build and smoke the ART classifier first, then wrap it and measure fairness separately. |
| Base `aif360` breaks after broad extras. | Optional dependency conflicts. | Recreate a clean base environment; add only the selected extra. |

## Dataset/API misuse

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Group matching errors or empty group metrics. | Group dictionaries use wrong protected names or raw values instead of encoded values. | Inspect `protected_attribute_names`, privileged/unprivileged values, and a converted DataFrame; use encoded values such as `0.0`/`1.0` when applicable. |
| `Reweighing` returns `nan`, `inf`, or extreme weights. | At least one `(group, label)` bucket is empty or tiny. | Count group-label buckets; change split, merge rare groups, or choose another algorithm. |
| Reweighing appears to have no model effect. | Downstream estimator ignored `instance_weights`. | Pass sample weights explicitly or use another pre/inprocessing algorithm. |
| Postprocessor fit fails or produces unchanged labels. | Prediction dataset lacks aligned labels/scores; threshold grid or metric bounds infeasible. | Verify true/pred datasets share instance order, labels, protected attributes, and score shape; inspect score min/max and baseline metrics. |
| `scores` shape/range errors. | Scores are missing, 1D/2D shape mismatched, logits supplied, or class order wrong. | Use positive-class probabilities in `[0, 1]` for calibrated/reject-option postprocessing; reshape consistently with dataset labels. |
| Metrics fail after transform. | Dataset copies lost metadata or label/protected maps. | Rebuild through AIF360 dataset constructors and verify metadata before metrics. |

## Workflow-specific notes

### Reweighing

- Expected output: labels and features unchanged; `instance_weights` changed.
- Check total instance weight and weighted mean difference/disparate impact before/after.
- All four privileged/unprivileged by favorable/unfavorable buckets must be populated.

### DisparateImpactRemover

- `repair_level` must be in `[0.0, 1.0]`.
- `sensitive_attribute` should name a protected attribute present in feature names; otherwise the first protected attribute is used.
- It exposes `fit_transform()`. If train/test consistency matters, validate distribution assumptions or choose another method.

### LFR

- Source class supports one unprivileged group and one privileged group.
- Scale numeric features and start with tiny `k`, `maxiter`, `maxfun` for smokes.
- Review continuous `scores` before choosing a classification threshold.

### OptimPreproc / OptTools

- `optim_options` must include the distortion function and optimization settings such as threshold lists, epsilon, and probability bounds.
- Feature/protected/label names must match between fit and transform.
- Non-uniform instance weights are ignored during fit/transform.

### AdversarialDebiasing

- Requires TensorFlow v1-style session handling.
- Disable eager execution under TensorFlow 2 before fitting.
- Supports one protected group pairing in the legacy class; use a composite only after verifying its own constraints.

### PrejudiceRemover

- Keep features numeric, labels binary, missing values imputed, and selected sensitive/class attributes present.
- It writes temporary files and invokes a Python subprocess internally; readonly sandboxes can fail.

### MetaFairClassifier

- `type` must be `fdr` or `sr`.
- `tau` changes the fairness/utility trade-off; compare the target metric and secondary metrics.

### GerryFairClassifier

- Learning `fairness_def` supports `FP` or `FN` in this release.
- Leave `heatmapflag=False` unless the user explicitly wants plots and supplies a safe output target.
- Reduce `max_iters` for initial smokes.

### Fairlearn reductions

- Estimator must fit with `sample_weight` when reductions provide weights.
- If `predict_proba()` is unavailable, `scores` may not be updated; use labels-only metrics or a probabilistic estimator.
- Constraint strings depend on fairlearn version; smoke the installed version.

### ARTClassifier

- For `BinaryLabelDataset`, wrapper converts ART prediction arrays with `argmax`; verify class order.
- The wrapper delegates to ART and does not by itself impose a fairness objective.

### IntersectionalFairness

- Import can fail if TensorFlow/progress dependencies are absent.
- Allowed algorithms: `Massaging`, `AdversarialDebiasing`, `RejectOptionClassification`.
- Allowed metrics include `DemographicParity`, `EqualOpportunity`, `EqualizedOdds`, `F1Parity`; reject-option is not compatible with `F1Parity`.
- Pass valid `StructuredDataset`/`BinaryLabelDataset` inputs, plus predicted/validation datasets for postprocessing mode.

### Equalized odds postprocessors

- `EqOddsPostprocessing` needs aligned predicted labels; degenerate group confusion matrices can make the linear program unstable.
- `CalibratedEqOddsPostprocessing` needs calibrated scores and a valid `cost_constraint` of `weighted`, `fpr`, or `fnr`.
- Set `seed` when stochastic label flipping must be repeatable.

### RejectOptionClassification

- Threshold bounds must be inside `[0, 1]`, low below high, and grid counts positive.
- If fairness constraints cannot be satisfied, widen metric bounds, recalibrate scores, expand the grid, or choose another method.

### DeterministicReranking

- Privileged and unprivileged dictionaries must use the same protected attribute name.
- `target_prop` length must equal all groups, in unprivileged-then-privileged order.
- `rerank_type` must be `Greedy`, `Conservative`, `Relaxed`, or `Constrained`.
- Use `renormalize_scores=False` when preserving original score values matters.

## Escalation checklist

Record package version and extras, dataset type and protected metadata, selected lifecycle stage, exact class signature/hyperparameters, before/after utility and fairness metrics, and whether the blocker is missing dependency, unsupported data shape, score misuse, or algorithm limitation.
