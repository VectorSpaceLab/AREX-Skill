# Algorithm Selection for Legacy AIF360 Mitigation

This reference covers `aif360.algorithms` legacy classes. Use [datasets-and-metrics](../../datasets-and-metrics/SKILL.md) for `BinaryLabelDataset`, `RegressionDataset`, group dictionaries, and metric objects. Use [sklearn-interface](../../sklearn-interface/SKILL.md) for pandas/sklearn-compatible estimators.

## Choose by lifecycle stage

| Stage | Use when | Inputs | Output | Classes |
| --- | --- | --- | --- | --- |
| Preprocessing | You can alter training data before model fitting. | `BinaryLabelDataset`; group dictionaries; sometimes repair/optimization options. | Transformed dataset or modified `instance_weights`. | `Reweighing`, `DisparateImpactRemover`, `LFR`, `OptimPreproc` |
| Inprocessing | Fairness must affect model training. | Labeled dataset plus optional estimator/session/constraint objects. | Fitted mitigator; `predict()` returns labels and sometimes scores in a copied dataset. | `AdversarialDebiasing`, `PrejudiceRemover`, `MetaFairClassifier`, `GerryFairClassifier`, `ExponentiatedGradientReduction`, `GridSearchReduction`, `ARTClassifier`, `IntersectionalFairness` |
| Postprocessing | A baseline model already produced labels/scores and cannot be retrained. | Aligned true-label dataset and prediction dataset, usually split into validation and test copies. | Prediction dataset with adjusted labels/scores. | `CalibratedEqOddsPostprocessing`, `EqOddsPostprocessing`, `RejectOptionClassification` |
| Reranking | The output is an ordered list of scored candidates. | `RegressionDataset` with one score column and encoded protected groups. | Reranked `RegressionDataset`. | `DeterministicReranking` |

## Preprocessing APIs

| Class | Signature | Fit/transform pattern | Required output check | Dependency status |
| --- | --- | --- | --- | --- |
| `Reweighing` | `(unprivileged_groups, privileged_groups)` | `fit(dataset)`, `transform(dataset)`, `fit_transform(dataset)` | Labels/features unchanged; `instance_weights` reweighted; total weight preserved up to tolerance when all buckets are present. | Base-safe; smoke script included. |
| `DisparateImpactRemover` | `(repair_level=1.0, sensitive_attribute='')` | `fit_transform(dataset)` | Feature values repaired; protected feature restored; `repair_level` in `[0, 1]`. | Optional/unverified; needs `BlackBoxAuditing`. |
| `LFR` | `(unprivileged_groups, privileged_groups, k=5, Ax=0.01, Ay=1.0, Az=50.0, print_interval=250, verbose=0, seed=None)` | `fit(dataset, maxiter=5000, maxfun=5000)`, `transform(dataset, threshold=0.5)`, `fit_transform(...)` | Output dataset has transformed `features`, binary `labels`, and continuous `scores`. | Optional/unverified in this run; package advertises an `LFR` extra involving `torch`; smoke on target runtime. |
| `OptimPreproc` | `(optimizer, optim_options, unprivileged_groups=None, privileged_groups=None, verbose=False, seed=None)` | `fit(dataset, sep='=')`, `transform(dataset, sep='=', transform_Y=True)`, `fit_transform(...)` | New `BinaryLabelDataset`; labels may be randomized when `transform_Y=True`; instance weights ignored. | Optional/unverified solver path; `OptTools` requires `cvxpy`. |

Preprocessing selection:

- Use `Reweighing` first for a low-risk model-agnostic baseline when the downstream estimator can consume sample weights.
- Use `DisparateImpactRemover` for feature repair, not for label balancing.
- Use `LFR` for latent representations when optimization cost and one-group limitation are acceptable.
- Use `OptimPreproc` only when the task requires explicit distortion/fairness constraints and the runtime has convex optimization support.

## Inprocessing APIs

| Class | Signature | Pattern | Caveats / dependency status |
| --- | --- | --- | --- |
| `AdversarialDebiasing` | `(unprivileged_groups, privileged_groups, scope_name, sess, seed=None, adversary_loss_weight=0.1, num_epochs=50, batch_size=128, classifier_num_hidden_units=200, debias=True)` | TensorFlow session -> `fit(dataset)` -> `predict(dataset)`. | Requires TensorFlow v1 compatibility and one protected group pairing; optional/unverified. Disable eager execution under TF2. |
| `PrejudiceRemover` | `(eta=1.0, sensitive_attr='', class_attr='')` | `fit(dataset)` -> `predict(dataset)`. | Numeric binary dataset; internally uses temporary files and subprocess; pre-impute missing values. |
| `MetaFairClassifier` | `(tau=0.8, sensitive_attr='', type='fdr', seed=None)` | `fit(dataset)` -> `predict(dataset)`. | `type` supports only `"fdr"` and `"sr"`; other values raise. |
| `GerryFairClassifier` | `(C=10, printflag=False, heatmapflag=False, heatmap_iter=10, heatmap_path='.', max_iters=10, gamma=0.01, fairness_def='FP', predictor=LinearRegression())` | `fit(dataset, early_termination=True)` -> `predict(dataset, threshold=.5)`. | Constructor accepts learning `fairness_def` `"FP"` or `"FN"` in this release; avoid heatmap output unless requested. |
| `ExponentiatedGradientReduction` | `(estimator, constraints, eps=0.01, max_iter=50, nu=None, eta0=2.0, run_linprog_step=True, drop_prot_attr=True)` | estimator + fairlearn constraint -> `fit(dataset)` -> `predict(dataset)`. | Optional/unverified; requires `fairlearn` `Reductions`; estimator should accept `sample_weight`; scores require `predict_proba()`. |
| `GridSearchReduction` | `(estimator, constraints, prot_attr=None, constraint_weight=0.5, grid_size=10, grid_limit=2.0, grid=None, drop_prot_attr=True, loss='ZeroOne', min_val=None, max_val=None)` | estimator + fairlearn constraint/grid -> `fit(dataset)` -> `predict(dataset)`. | Optional/unverified `fairlearn`; supports classification or regression depending on constraints/loss. |
| `ARTClassifier` | `(art_classifier)` | Wrap external ART classifier -> `fit(dataset, batch_size=128, nb_epochs=20)` -> `predict(dataset, logits=False)`. | Optional/unverified; requires ART and model backend. Wrapper is not itself a fairness constraint. |
| `IntersectionalFairness` | `(algorithm, metric, accuracy_metric='Balanced Accuracy', upper_limit_disparity=0.03, debiasing_conditions=None, instruct_debiasing=False, upper_limit_disparity_type='difference', max_workers=4, options={})` | `fit(dataset_actual, dataset_predicted=None, dataset_valid=None, options={})` -> `predict(dataset)`. | Experimental composite; allowed algorithms `Massaging`, `AdversarialDebiasing`, `RejectOptionClassification`; metrics include `DemographicParity`, `EqualOpportunity`, `EqualizedOdds`, `F1Parity`; do not pair reject-option with `F1Parity`; imports TensorFlow/progress utilities and was unverified. |

## Postprocessing and reranking APIs

| Class | Signature | Fit/predict pattern | Required inputs |
| --- | --- | --- | --- |
| `CalibratedEqOddsPostprocessing` | `(unprivileged_groups, privileged_groups, cost_constraint='weighted', seed=None)` | `fit(dataset_true, dataset_pred)` -> `predict(dataset, threshold=0.5)` | `dataset_pred.scores` must be calibrated positive-class scores; cost is `weighted`, `fpr`, or `fnr`. |
| `EqOddsPostprocessing` | `(unprivileged_groups, privileged_groups, seed=None)` | `fit(dataset_true, dataset_pred)` -> `predict(dataset)` | `dataset_pred.labels` must contain baseline predicted labels aligned with true labels; solves a linear program. |
| `RejectOptionClassification` | `(unprivileged_groups, privileged_groups, low_class_thresh=0.01, high_class_thresh=0.99, num_class_thresh=100, num_ROC_margin=50, metric_name='Statistical parity difference', metric_ub=0.05, metric_lb=-0.05)` | `fit(dataset_true, dataset_pred)` -> `predict(dataset_pred)` | `dataset_pred.scores` must be positive-class scores in `[0, 1]`; metric name must be one of the three source-supported names. |
| `DeterministicReranking` | `(unprivileged_groups, privileged_groups)` | `fit(regression_dataset)` -> `predict(dataset, rec_size, target_prop, rerank_type='Constrained', renormalize_scores=False)` | `RegressionDataset` with exactly one score/label; `target_prop` length equals number of unprivileged plus privileged groups; rerank type is `Greedy`, `Conservative`, `Relaxed`, or `Constrained`. |

Postprocessing selection:

- Use `EqOddsPostprocessing` when you have hard labels and want equalized odds randomization.
- Use `CalibratedEqOddsPostprocessing` when calibrated scores are available and the objective is generalized FPR/FNR cost parity.
- Use `RejectOptionClassification` when score thresholds around the decision boundary can be tuned.
- Use a validation split for `fit()` and a held-out split for final metric reporting to avoid leakage.

## Metric validation after selection

Always report at least one utility signal and one fairness signal. Common checks include accuracy/balanced accuracy, base rates, statistical parity difference, disparate impact, average odds difference, equal opportunity difference, generalized false-positive/false-negative rates, sample distortion for feature-changing preprocessing, and realized group proportions for reranking.
