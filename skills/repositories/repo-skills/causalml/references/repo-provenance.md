# causalml repo provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: `causalml`
- Branch: `master`
- Source commit: `a77dfb4f1eeb72cf02e20229c3ee1413fb14ae0a`
- Package version observed from installed metadata: `0.17.0`
- Dirty-state note at construction time: the source tree was clean except for generated `skills/` output.
- Generated skill id: `causalml`

This repo skill is self-contained. The paths below record evidence used for refresh/staleness review; runtime instructions should use the bundled skill references and scripts rather than reading the source checkout.

## Evidence paths used

### Package source

- `causalml/__init__.py`
- `causalml/dataset/`
- `causalml/features.py`
- `causalml/feature_selection/`
- `causalml/propensity.py`
- `causalml/match.py`
- `causalml/metrics/`
- `causalml/optimize/`
- `causalml/inference/_arg_order.py`
- `causalml/inference/serialization.py`
- `causalml/inference/meta/`
- `causalml/inference/iv/`
- `causalml/inference/tree/`
- `causalml/inference/tf/`
- `causalml/inference/torch/`
- `causalml/inference/jax/`
- `causalml/exceptions.py`

### Docs and packaging

- `README.md`
- `pyproject.toml`
- `setup.py`
- `setup.cfg`
- `docs/installation.rst`
- `docs/quickstart.rst`
- `docs/methodology.rst`
- `docs/validation.rst`
- `docs/interpretation.rst`
- `docs/migration.rst`
- `docs/causalml.rst`
- `docs/examples.rst`
- `docs/references.rst`
- `docs/issue-859-resolution.md`

### Test/example evidence

- `tests/test_datasets.py`
- `tests/test_features.py`
- `tests/test_feature_selection.py`
- `tests/test_propensity.py`
- `tests/test_match.py`
- `tests/test_meta_learners.py`
- `tests/test_fit_arg_order.py`
- `tests/test_polars_support.py`
- `tests/test_ivlearner.py`
- `tests/test_serialization.py`
- `tests/test_serialization_extended.py`
- `tests/test_causal_trees.py`
- `tests/test_uplift_trees.py`
- `tests/test_visualize.py`
- `tests/test_metrics.py`
- `tests/test_rate.py`
- `tests/test_sensitivity.py`
- `tests/test_value_optimization.py`
- `tests/test_dragonnet.py`
- `tests/test_cevae.py`
- `tests/test_jax_dragonnet.py`
- `tests/test_jax_cevae.py`
- `docs/examples/*.ipynb` as reference-only workflow evidence

## Installed-package inspection facts

The construction pass used a private Python 3.11 inspection environment with the package installed editable from the source snapshot. `pip check` passed. Live imports and signatures were used to confirm these current-version facts:

- `TMLELearner` exposes `estimate_ate`; it does not expose public `fit`, `predict`, or `fit_predict` methods.
- The current IV class is `IVRegressor`; `BaseIVRegressor` is not a public class.
- Current DRIV classes include `BaseDRIVLearner`, `BaseDRIVRegressor`, and `XGBDRIVRegressor`; `BaseDRIVClassifier` is not public.
- Classical learners, tree models, IV, and DRIV families use the shared `save`/`load`/`load_learner` persistence mixin; no top-level `save_model`/`load_model` functions were found for these classical estimators.
- `CausalRandomForestRegressor` has `fit` and `predict` but no `fit_predict`.
- `UpliftTreeClassifier` and `UpliftRandomForestClassifier` expose `fit`, `predict`, `save`, and `load`; the tree additionally exposes `fill` and `prune`.
- TensorFlow and JAX DragonNet expose `fit`, `predict`, `fit_predict`, `predict_tau`, and `predict_propensity`.
- Torch/Pyro CEVAE exposes `fit`, `predict`, and `fit_predict`; it has no CausalML wrapper-level `save`/`load` methods.
- JAX CEVAE exposes `fit`, `predict`, `fit_predict`, `save(path)`, and `load(path, feature_dim)`.
- `PolicyLearner` and `CounterfactualUnitSelector` expose `fit` and `predict`; `PolicyLearner` also exposes `predict_proba`.
- `CounterfactualValueEstimator` exposes `predict_best` and `predict_counterfactuals`.
- `SensitivityRandomFeature`, `FeatureEffectExplainer`, `make_uplift_regression`, and `causalml.inference.nn` were not public APIs in this snapshot.

## Runtime verification facts used during construction

- Core CPU smoke passed for synthetic data, meta-learner fitting, causal tree fitting, propensity matching, policy learning, and feature selection.
- Optional TensorFlow DragonNet tiny CPU fit/predict smoke passed.
- Optional Torch/Pyro CEVAE tiny CPU smoke passed with `num_layers=2`; a reduced `num_layers=1` configuration triggered a Pyro indexing error and is documented as a troubleshooting caveat.
- Optional JAX DragonNet tiny CPU fit/predict smoke passed with expected CPU fallback when a CUDA-enabled JAX build was absent.
- Optional JAX CEVAE tiny CPU fit/predict smoke passed with expected CPU fallback.
- No CUDA, ROCm, MPS, or vendor accelerator behavior was verified or claimed.

## Selected skill coverage

The runtime skill is organized into these operating sub-skills:

- `data-preparation`: synthetic data, feature encoding, propensity, matching, table-one balance checks, and bundled CSV matching helper.
- `causal-estimation`: classical meta-learners, TMLE, IV/DRIV, API contracts, Polars/DataFrame handling, and persistence.
- `tree-models`: causal trees/forests, uplift trees/forests, plotting, persistence, and compiled tree troubleshooting.
- `deep-models`: optional TensorFlow, Torch/Pyro, and JAX neural wrappers for DragonNet and CEVAE.
- `analysis-and-decision`: metrics, validation, sensitivity, feature selection/interpretation, policy/value optimization, and probability-of-causation bounds.

## Refresh triggers

Refresh this skill when any of the following changes:

- Source commit, release version, or dependency extras change.
- Public estimator signatures or class exports change.
- Optional backend packages or save/load formats change.
- Cython tree build/import behavior changes.
- Docs remove stale API references or add new public workflow families.
- Tests add new model families, metrics, scripts, or recommended end-to-end examples.
