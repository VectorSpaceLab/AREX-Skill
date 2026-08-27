# Testing and Validation

## When to read

Read this when validating a Yellowbrick workflow, adapting one of the bundled
scripts, selecting native repo tests as ground truth, or debugging visual test
failures.

## Fast validation ladder

1. **Import check**: verify the same Python can import Yellowbrick and the
   target submodule.
2. **Signature check**: inspect the class/function signature before writing a
   recipe with non-default parameters.
3. **Bundled smoke script**: run the root or sub-skill script with synthetic
   data and a temporary output directory.
4. **Native candidate**: after generated skill integration, run a focused
   Yellowbrick native test only when the required optional dependencies and
   data/cache assumptions are satisfied.
5. **Image comparison**: use native image-baseline tests only for maintainer
   changes; they are more brittle than smoke checks for ordinary use.

## Bundled scripts

- Root: `../scripts/check_yellowbrick_visualizer.py` checks import, classifier,
  regressor, and clustering basics.
- Classification: `../sub-skills/classifier-visualizers/scripts/classification_smoke.py`.
- Regression: `../sub-skills/regressor-visualizers/scripts/regression_smoke.py`.
- Feature/target: `../sub-skills/feature-target-visualizers/scripts/feature_target_smoke.py`.
- Cluster/model selection: `../sub-skills/cluster-model-selection/scripts/model_selection_smoke.py`.
- Text/datasets: `../sub-skills/text-and-datasets/scripts/text_smoke.py` and
  `../sub-skills/text-and-datasets/scripts/check_dataset_cache.py`.
- Contrib/extensions: `../sub-skills/contrib-and-extensions/scripts/contrib_smoke.py`.

Each script is intended to be safe by default: no network, no credentials, no
long training, no destructive cache cleanup, and no dependency on the original
source checkout.

## Native test candidates

Use native tests as ground-truth candidates only after the runtime skill is
integrated. Good focused candidates include:

| Capability | Candidate family | Notes |
|---|---|---|
| Classifier diagnostics | `tests/test_classifier/test_confusion_matrix.py`, `test_rocauc.py`, `test_prcurve.py`, `test_threshold.py` | Needs compatible scikit-learn and Matplotlib test stack. |
| Regression diagnostics | `tests/test_regressor/test_residuals.py`, `test_prediction_error.py`, `test_alphas.py` | Some image tests are sensitive to font/backends. |
| Feature/target plots | `tests/test_features/test_rankd.py`, `test_pca.py`, `tests/test_target/test_feature_correlation.py` | Manifold tests can be slower; bound algorithms. |
| Clustering/model selection | `tests/test_cluster/test_elbow.py`, `test_silhouette.py`, `tests/test_model_selection/test_validation_curve.py`, `test_learning_curve.py` | Reduce CV folds/ranges for smoke-style verification. |
| Datasets/text | `tests/test_datasets/test_path.py`, `tests/test_text/test_freqdist.py`, selected pre-tagged `test_postag.py` | Avoid network downloads unless a cache is prepared. |
| Contrib | `tests/test_contrib/test_scatter.py`, `test_wrapper.py`, selected missing-value and statsmodels tests | Optional pandas/statsmodels may be required. |

## Visual image tests

Yellowbrick's native test suite includes image comparison helpers and baseline
images. These are useful for maintaining Yellowbrick itself, but ordinary agent
workflows should usually assert that a plot can be generated and saved rather
than comparing pixels.

If maintaining the repo, the native `tests/images.py` helper can move generated
actual images into baseline locations. Do not run baseline rewrite helpers
against a checkout unless the user explicitly asks for maintainer work and
approves file mutations.

## Interpreting warnings

- Missing-font warnings: usually non-fatal when a non-empty PNG is created.
- No elbow/knee detected: valid outcome for some data; report it and consider
  `locate_elbow=False` or another metric/range.
- Optional dependency skipped: do not mark the core skill failed; record the
  optional path as unverified.
- Deprecation or future warnings: capture the dependency versions and decide
  whether the task needs a compatibility pin.
