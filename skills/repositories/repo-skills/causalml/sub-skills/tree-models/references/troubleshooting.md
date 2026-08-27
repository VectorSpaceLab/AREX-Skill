# Troubleshooting

## Cython / scikit-learn rebuild failures

If importing the tree package fails after upgrading `scikit-learn`, `numpy`, or `scipy`, assume the compiled extensions are stale and rebuild the package against the current environment.

Typical symptoms:

- a signature mismatch when importing the tree modules
- a `TypeError` mentioning `DEFAULT_SEED` or a similar sklearn internal symbol
- an import error that disappears after reinstalling from source

What usually fixes it:

1. remove stale build artifacts or old wheel leftovers
2. reinstall or rebuild the package in the active environment
3. retry a simple import of the tree stack before continuing

## Graphviz / pydotplus

`uplift_tree_plot(...)` returns a `pydotplus` graph, but turning that graph into PNG or PDF output needs the Graphviz runtime as well.

If rendering fails:

- confirm Python `pydotplus` is installed
- confirm the Graphviz binary is available on `PATH`
- retry the render call after both pieces are present

`uplift_tree_string(...)` is text-only and does not need Graphviz.

## OpenMP and native library errors

The tree models themselves are pure Python wrappers over compiled kernel code, but workflows around them often touch native packages such as `xgboost` or `lightgbm`.

On macOS, a missing OpenMP runtime can show up as a native library load error. Install the platform OpenMP runtime and retry the import.

## API gotchas

- `CausalRandomForestRegressor` has no `fit_predict`; call `fit(...)` and then `predict(...)`.
- `CausalRandomForestRegressor.calculate_error(...)` only works for a single treatment contrast.
- `UpliftTreeClassifier.fit(...)` accepts `X_val`, `treatment_val`, and `y_val` for compatibility, but the kernel tree ignores them.
- `UpliftRandomForestClassifier.fit(...)` also ignores validation-set early stopping arguments.
- `prune_fraction` may be `None` on uplift trees, but `estimation_sample_size` must always be a strict fraction in `(0, 1)`.
- `criterion="causal_mse"` requires `min_impurity_decrease=-inf`.
- `ccp_alpha="cv"` requires `honesty=True`.

## Persistence errors

Tree files are class-specific. If a saved tree or forest is loaded with the wrong class, the load call raises a class-mismatch error.

Use the same class that created the file, or load through the generic learner loader when you truly do not know the model type.
