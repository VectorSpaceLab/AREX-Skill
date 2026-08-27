# Troubleshooting

## ImportError or Rust extension failures

**Symptoms**

- `import river` fails.
- A compiled module under `river._river_rust` cannot be imported.
- The package works in one environment but not in another.

**Recovery**

- Reinstall River for the active Python version and platform.
- Make sure the build or wheel you are using matches the interpreter and architecture.
- If you are building from source, make sure the native toolchain required by the package is present.
- Do not mix artifacts from different Python versions or architectures.

## Missing pandas for mini-batch APIs

**Symptoms**

- `learn_many`, `predict_many`, `predict_proba_many`, or `transform_many` are unavailable or skipped.
- Batch-specific checks do not run.

**Recovery**

- Install the optional pandas support so the batch-oriented paths are available.
- If you only need the single-sample API, keep using `learn_one` and `predict_one`.
- If batch support is not present, the harness skips the batch-specific checks by design.

## `check_estimator` failures

**Symptoms**

- A new estimator fails on cloning, repr, or parameter inspection.
- A check name points to `check_init_has_default_params_for_tests` or `check_get_params_matches_signature`.
- A classifier loses labels it has already seen.
- A model mutates the caller's input sample.
- A batch or anomaly check fails because the needed dataset is not available in the environment.

**Recovery**

- If construction needs required parameters, add `_unit_test_params` so tests can instantiate the class safely.
- Keep constructor defaults immutable. Prefer `None`, numbers, strings, tuples, booleans, or types over lists and dicts.
- Store constructor arguments on same-named attributes so `_get_params()` can recover them.
- Make `clone()` independent of the original object and its nested mutable state.
- Put truly mutable fields in `_mutable_attributes`; everything else should stay immutable or be replaced by cloning.
- If a batch method is deliberately not equivalent to the single-sample version, add that check name to `_unit_test_skips()`.
- If an anomaly check tries to load an unavailable dataset, use the bundled manual anomaly smoke or make sure the dataset is already available.

## Wrong target types or sample shapes

**Symptoms**

- A classifier rejects a label that should be valid.
- A regressor or anomaly detector is passed the wrong kind of target.
- A drift detector is given a dictionary when it expects a scalar value.

**Recovery**

- Use dictionaries for feature samples.
- Keep classifier labels to `bool`, `str`, or `int`.
- Keep regression targets numeric.
- Pass a scalar to drift detectors and a feature dict to clusterers and anomaly detectors.
- If a wrapper changes the expected input shape, wrap it in the family that matches the wrapped estimator.

## Unfitted, `None`, or empty predictions

**Symptoms**

- A classifier returns `None` before any learning.
- `predict_proba_one` returns `{}` before any labels are seen.
- A prediction method keeps returning an empty or default value after learning.

**Recovery**

- Treat `None` or an empty probability map as a valid cold-start pattern only when it is deliberate.
- The canonical example is `dummy.NoChangeClassifier`, which returns `None` and `{}` before the first label.
- After learning, a classifier should emit probabilities for labels it has seen, and those probabilities should sum to 1.
- If the output stays empty after training, check that `learn_one` is actually updating state and that `predict_proba_one` includes seen labels.
- If you need a deterministic baseline, seed the model or use a dummy estimator that is meant to stay simple.
