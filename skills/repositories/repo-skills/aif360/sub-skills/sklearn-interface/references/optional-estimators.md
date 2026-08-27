# Optional Estimators and Extra-Gated Workflows

The verified base environment intentionally installed only the base AIF360 package. Treat every extra-gated workflow in this file as optional/unverified until the named extra is installed and a small workflow is run. Do not describe optional branches as verified solely because their class names import or appear in this reference.

## Base-supported sklearn estimators

These APIs are available from the base package and are the safest defaults for sklearn-compatible workflows.

| API | Status | Use when | Main caveats |
| --- | --- | --- | --- |
| `Reweighing(prot_attr=None)` | Base-supported | Need preprocessing reweighting with protected groups in `X.index`. | `fit_transform` returns `(X, sample_weight)`, not a transformed `X`; use manually or through `ReweighingMeta`. |
| `ReweighingMeta(estimator, reweigher=None)` | Base-supported | Need reweighing inside a sklearn-compatible model wrapper. | Wrapped estimator must support `sample_weight` in `fit`. |
| `CalibratedEqualizedOdds(prot_attr=None, cost_constraint='weighted', random_state=None)` | Base-supported | Need calibrated equalized odds from classifier probabilities. | Binary only; requires probability estimates and exactly two protected groups. |
| `RejectOptionClassifier(prot_attr=None, threshold=0.5, margin=0.1)` | Base-supported | Need fixed reject-option threshold/margin postprocessing. | Binary only; `X` passed to `fit`/`predict` must be a probability DataFrame with protected attributes in the index. |
| `RejectOptionClassifierCV(prot_attr=None, *, scoring, step=0.05, refit=True, **kwargs)` | Base-supported | Need to grid-search reject-option threshold/margin. | Built-in scoring strings are `statistical_parity`, `average_odds`, `equal_opportunity`, `disparate_impact`; sample weights are ignored during scoring with a runtime warning. |
| `PostProcessingMeta(estimator, postprocessor, *, prefit=False, val_size=0.25, **options)` | Base-supported | Need to combine a base estimator and a postprocessor without leakage. | Put preprocessing pipelines inside the base estimator argument; do not put `PostProcessingMeta` as a middle pipeline step. |

## Extra-gated estimators

Install only the extras needed for the requested workflow. Broad `[all]` installs are unnecessary for base metrics and can introduce heavy, conflicting, or platform-specific dependencies.

| API | Extra | Verification status in this skill | Operational notes |
| --- | --- | --- | --- |
| `LearnedFairRepresentations(prot_attr=None, n_prototypes=5, reconstruct_weight=0.01, target_weight=1.0, fairness_weight=50.0, tol=0.0001, max_iter=200, verbose=0, random_state=None)` | `aif360[LFR]` (`torch`) | Optional/unverified | Can act as a transformer and classifier. Fit can be iterative and can raise convergence warnings; preserve protected attrs in `X.index`. |
| `FairAdapt(prot_attr, adj_mat)` | `aif360[FairAdapt]` (`rpy2`) plus R runtime/packages | Optional/unverified | Causal preprocessing for classification or regression. Expects binary protected attr and adjacency matrix aligned to training columns. Construction can reach the R bridge and may try to install missing R packages, so avoid locked/offline environments unless prepared. |
| `AdversarialDebiasing(prot_attr=None, scope_name='classifier', adversary_loss_weight=0.1, num_epochs=50, batch_size=128, classifier_num_hidden_units=200, debias=True, verbose=False, random_state=None)` | `aif360[AdversarialDebiasing]` (`tensorflow`) | Optional/unverified | TensorFlow v1-compatible estimator. Disable eager execution before fitting; close the created TensorFlow session when no longer needed. |
| `ExponentiatedGradientReduction(prot_attr, estimator, constraints, eps=0.01, max_iter=50, nu=None, eta0=2.0, run_linprog_step=True, drop_prot_attr=True)` | `aif360[Reductions]` (`fairlearn`) | Optional/unverified | Classification reduction. `prot_attr` names columns in `X`; `drop_prot_attr=True` removes them before fitting the base estimator while passing them as sensitive features. |
| `GridSearchReduction(prot_attr, estimator, constraints, constraint_weight=0.5, grid_size=10, grid_limit=2.0, grid=None, drop_prot_attr=True, loss='ZeroOne', min_val=None, max_val=None)` | `aif360[Reductions]` (`fairlearn`) | Optional/unverified | Classification or bounded-group-loss regression reduction. `predict_proba` is available only for classification moments; regression branches can raise `NotImplementedError` for probabilities. |
| `SenSeI(module, *, criterion, distance_x, distance_y, rho, eps, auditor_nsteps, auditor_lr, regression='auto', **kwargs)` | `aif360[inFairness]` (`skorch`, `inFairness`, `torch`) | Optional/unverified | Requires torch module, criterion, and inFairness distance objects. `regression='auto'` infers task type from `y`; set it explicitly for ambiguous soft targets. |
| `SenSR(module, *, criterion, distance_x, eps, lr_lamb, lr_param, auditor_nsteps, auditor_lr, regression='auto', **kwargs)` | `aif360[inFairness]` (`skorch`, `inFairness`, `torch`) | Optional/unverified | Similar runtime to `SenSeI` but with sensitive-subspace robustness. Prepare distance objects before construction. |

## Optional metric dependency

`ot_distance` is a metric, not an estimator, but it is extra-gated:

- Signature: `ot_distance(y_true: pandas.Series, y_pred: Union[pandas.Series, pandas.DataFrame], prot_attr: pandas.Series = None, pos_label: Union[str, float] = None, scoring: str = 'Wasserstein1', num_iters: int = 100000.0, penalty: float = 1e-17, mode: str = 'binary', cost_matrix: numpy.ndarray = None, **kwargs)`
- Extra: `aif360[OptimalTransport]`, which provides POT as the import name `ot`.
- Status here: optional/unverified because POT was intentionally not installed.
- If the task only asks for sklearn group metrics, do not install POT. If the task explicitly asks for Wasserstein/optimal-transport fairness, install the extra and run a tiny binary-mode call before claiming support.

## Cross-skill routing

- `mdss_bias_score` is covered in this sub-skill as a scoring helper for a specified subset. Full `MDSS_bias_scan` and FACTS recourse workflows belong to the sibling `detectors-and-explainers` sub-skill.
- Legacy algorithm classes under `aif360.algorithms` belong to the sibling `mitigation-algorithms` sub-skill, even when they share names with sklearn wrappers.
- Legacy `BinaryLabelDataset` inputs and legacy metric-class comparisons belong to the sibling `datasets-and-metrics` sub-skill.

## Extra install decision checklist

Before installing an extra, confirm:

1. The caller needs that exact workflow and cannot use base sklearn metrics or base postprocessing.
2. The runtime can tolerate the extra's dependency family, such as TensorFlow, torch, fairlearn, R/rpy2, POT, or inFairness/skorch.
3. A tiny import and fit/score smoke can be run after installation.
4. The final handoff records the extra as verified only if the actual workflow ran successfully.

See [troubleshooting](troubleshooting.md) for missing-extra messages and remediation.
