# Vaex ML troubleshooting

## Import and dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'vaex.ml'` | `vaex-ml` is not installed, or only `vaex-core` is installed. | Install the Vaex metapackage or `vaex-ml` in the active environment. Verify with `python -c "import vaex, vaex.ml"`. |
| `AttributeError: module 'vaex.ml' has no attribute 'sklearn'` or wrapper not registered | `vaex.ml.sklearn` was not explicitly imported. | Add `import vaex.ml.sklearn` and then import `Predictor` or `IncrementalPredictor` from `vaex.ml.sklearn`. |
| `AttributeError: module 'vaex.ml' has no attribute 'KMeans'` | `KMeans` lives in `vaex.ml.cluster`. | Use `import vaex.ml.cluster` and `vaex.ml.cluster.KMeans(...)`. |
| Optional wrapper import fails for XGBoost, LightGBM, CatBoost, TensorFlow, River, ANNOY, or PyGBM | Optional third-party package is missing or incompatible. | Install only the needed optional package; keep the workflow guarded so missing optional extras do not block core Vaex ML usage. |

## Train/test split pitfalls

- `df.ml.train_test_split(...)` is ordered and shallow. It warns by default:
  `Make sure the DataFrame is shuffled`. Shuffle first if the dataset is sorted
  by target, time, class, source, or any leakage-prone order.
- For large data, prefer writing a shuffled dataset once and reopening it rather
  than relying on in-memory shuffling.
- Filtered DataFrames are not supported by this splitter. Split before applying
  filters, or materialize/export the filtered subset and reopen it as a new
  DataFrame.
- Split before fitting target-aware encoders and predictive models. Fitting a
  target encoder on the full DataFrame leaks test-set target information.

## State transfer failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Transferred state references missing columns | The target DataFrame lacks base columns used by train virtual columns/functions. | Apply state transfer only to DataFrames with the same base schema, or recreate/rename base columns first. |
| Expected split active range is not reproduced | `df.ml.state_transfer()` intentionally excludes the original active range. | Use train/test DataFrames for ranges; use state transfer for virtual columns, functions, selections, and transformation state. |
| Prediction column missing after applying state | State transfer was captured before the model or transformer added its virtual column. | Capture `state_transfer = transformed_train.ml.state_transfer()` after all required virtual columns are present, or use a `Pipeline` ordered with state transfer before the predictor. |
| Loading state/pipeline fails in another environment | The serialized state needs classes or optional packages not installed there. | Install the same public package families used to create the state, then load again. |

## Scikit-learn wrapper memory issues

- `Predictor.fit(df)` evaluates `df[features].values`; that is a dense in-memory
  copy of the selected features. `Predictor.predict(df)` materializes the full
  prediction array.
- `Predictor.transform(df)` adds a lazy virtual prediction column, but evaluating
  that column still calls the wrapped estimator over requested chunks.
- Use fewer features, smaller training samples, or `IncrementalPredictor` when
  the selected matrix does not fit memory.
- `IncrementalPredictor.fit(df)` copies one batch at a time. Tune `batch_size` to
  fit memory and set `num_epochs` deliberately.
- Classifiers with `.partial_fit(...)` often require known classes. Pass them
  with `partial_fit_kwargs={"classes": [...]}`.
- If `prediction_type="predict_proba"`, expect a 2-D prediction column/array for
  multiclass classifiers.

## Encoder and transformer surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Label encoder raises on test data | Test data has unseen categories and `allow_unseen=False`. | Fit on train only, then choose `allow_unseen=True` if unseen categories are expected; unseen values map to `-1`. |
| Frequency or target encoder returns missing/NaN values | Unseen categories use `unseen="nan"` by default. | Set `unseen="zero"` if zero is a valid fallback for the model. |
| One-hot transformation creates too many columns | High-cardinality categorical feature. | Use frequency, target, label, or multihot encoding instead. |
| WeightOfEvidenceEncoder raises about target values | Target is not binary `0/1` or boolean-like. | Cast or derive a binary target before fitting WOE. |
| GroupByTransformer output has missing values | Production/test data has keys absent from the fitted train group table. | Decide a missing-value strategy after transform, or broaden training data if appropriate. |
| Output column names collide | Default prefix/suffix creates an existing column name. | Set `prefix`, `rprefix`, or `rsuffix` explicitly. |
| `KBinsDiscretizer` warns that bins were removed | Requested bins have nearly zero width. | Decrease `n_bins`, inspect feature distribution, or choose another strategy. |

## PCA, random projection, and KMeans issues

- `PCA` requires at least two features and cannot retain more components than the
  number of features.
- `PCAIncremental` and `RandomProjections` require scikit-learn during `fit`.
  Their saved state can transform later without refitting if the Vaex state is
  loaded successfully.
- `RandomProjections` requires `0 < eps < 1` when `n_components` is inferred and
  `0 < density <= 1` for sparse density if provided.
- `KMeans` first use may spend time compiling Numba functions. Keep small smoke
  tests tiny and use a deterministic `random_state`.
- `KMeans` is imported from `vaex.ml.cluster`; this sub-skill does not verify or
  claim a GPU implementation.

## Pipeline serialization and file paths

- `Pipeline.save(path)` writes JSON or YAML to a normal local path. The parent
  directory must already exist.
- `Pipeline.load(path)` mutates the `Pipeline` instance by replacing its list
  contents. Load into a new empty `vaex.ml.Pipeline()` when you want to avoid
  mixing old and new stages.
- Load only trusted pipeline files. Scikit-learn and optional estimator wrappers
  can serialize model state, including pickled estimator objects or native model
  bytes.
- If a loaded pipeline fails to transform, inspect whether the target DataFrame
  has every base column used by the saved virtual expressions and whether all
  optional estimator packages are installed.

## Optional estimator notes

- XGBoost, LightGBM, and CatBoost wrappers copy selected features to the native
  library data structures during fit/predict. They are not proof that the full
  dataset can train without memory pressure.
- Native library parameter names and defaults change over time. Validate a tiny
  model with the user's installed package versions before launching a long run.
- CatBoost batch training uses `batch_size` and may require matching
  `batch_weights`. Validate the number of produced batch models before relying
  on summed models.
- TensorFlow integration is optional. If `import vaex.ml.tensorflow` or
  `df.ml.tensorflow` fails, install a compatible TensorFlow extra or keep the
  workflow on verified Vaex/scikit-learn wrappers. Do not claim GPU support from
  this skill.

## Scope boundary reminders

- Generic virtual-column expressions, joins, grouped aggregations, and analytic
  feature exploration belong in [../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md) unless the operation is captured in a reusable
  Vaex ML transformer.
- DataFrame laziness, active ranges, materialization, `evaluate`, `values`, and
  memory-mapped dataset behavior belong in [../../dataframe-core/SKILL.md](../../dataframe-core/SKILL.md) when the issue is not ML-specific.
