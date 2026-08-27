# Mixtures and Classifiers Troubleshooting

## Component setup

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Constructor rejects `distributions` | Passed a class, array, or invalid object instead of a list/tuple of distribution-like objects. | Instantiate each component first, for example `[Normal(covariance_type='diag'), Normal(covariance_type='diag')]`. |
| EM starts with poor or unstable assignments | Uninitialized components were initialized poorly. | Try `init='first-k'` for deterministic debugging, set `random_state`, or seed components with explicit parameters. |
| Submodular initialization fails | `apricot-select`/`numba` dependency problem or unsupported environment. | Use `init='first-k'` or `init='random'` first; repair the dependency only if submodular initialization is required. |
| Parameters do not change after fitting | Model or component is frozen, or `inertia` is too high. | Confirm `frozen=False` and use lower inertia. |

## Priors and posterior assignments

- Constructor `priors` must be a length-`k` vector that sums to 1.
- Inference/training `priors` must be shaped `(n, k)` for mixture/classifier data.
- Rows containing values outside `[0, 1]` or not summing to 1 raise validation errors.
- One-hot prior rows force assignments; soft prior rows bias assignments but do not act as supervised labels.

## `BayesClassifier` labels

- `BayesClassifier.fit(X, y)` requires labels `y`; use `GeneralMixtureModel` for unlabeled data.
- Labels must be integer class ids from `0` through `k-1`.
- If class names are strings, map them to integer ids before fitting and store the inverse map next to the model.
- If one class has no examples, its component may remain poorly initialized; add data or initialize the component from known parameters.

## Data and weight shape issues

- `X` should be 2D `(n, d)`.
- `sample_weight` should be nonnegative and compatible with `(n,)`, `(n, 1)`, or `(n, d)` depending on the path.
- Keep `check_data=True` until shapes, weights, and priors pass on a tiny subset.

## Interpreting results

- Mixture component labels are arbitrary. Do not compare raw component ids across independent fits without matching components by parameters or posterior behavior.
- Exact random samples after `torch.manual_seed(...)` can differ across PyTorch versions, devices, or distribution-kernel changes. Use seeded samples for local reproducibility, but avoid cross-version golden tests that assert exact sampled tensors.
- `predict_proba` returns posterior probabilities by component/class, not feature probabilities.
- Use `log_probability` for model comparison when underflow is possible.

## Legacy API confusion

If old examples mention `GaussianMixtureModel`, `NaiveBayes`, or `NormalDistribution`, translate to v1.x concepts: `GeneralMixtureModel`, `BayesClassifier`, and `Normal`. `NaiveBayes` was removed because `BayesClassifier` with simple independent distributions covers the same practical role.
