# Vaex ML API reference

Use this as a compact public API map for Vaex ML workflows.

## DataFrame ML accessor

| API | Purpose | Important notes |
| --- | --- | --- |
| `df.ml.train_test_split(test_size=0.2, strings=True, virtual=True, verbose=True)` | Return `(train, test)` shallow DataFrames. | Ordered split; warns to shuffle unless `verbose=False`; filtered DataFrames are not supported. |
| `df.ml.state_transfer()` | Return a transformer that carries the DataFrame state. | Use after fitting/adding virtual preprocessing columns on train data; target DataFrame must have all base columns referenced by the transferred state. |

Dynamic accessor methods also exist for generated transformer names, for example
`df.ml.standard_scaler(...)`, `df.ml.minmax_scaler(...)`, `df.ml.label_encoder(...)`,
`df.ml.pca(...)`, `df.ml.kmeans(...)`, and `df.ml.sklearn_predictor(...)`. These
methods instantiate the class, fit it on `df`, and either return the transformed
DataFrame or the fitted transformer with `transform=False`. For reusable code,
explicit class imports are often clearer.

## Common transformer semantics

- Vaex ML transformers have `fit(df)`, `transform(df)`, and usually
  `fit_transform(df)`.
- `transform(df)` returns a shallow DataFrame copy with virtual columns or mapped
  columns; it does not mutate the input DataFrame in place.
- Traitlets expose constructor/state fields. Fitted attributes commonly end in
  `_` and are serialized in pipeline state.
- Prefixes control output virtual column names. Change prefixes to avoid
  collisions.

## Transformer classes

| Class | Default output naming | Key constructor/state traits | Fit/transform behavior |
| --- | --- | --- | --- |
| `vaex.ml.StandardScaler` | `standard_scaled_<feature>` | `features`, `prefix`, `with_mean`, `with_std`, fitted `mean_`, `std_` | Uses Vaex mean/std aggregations, then creates virtual standardized columns. |
| `vaex.ml.MinMaxScaler` | `minmax_scaled_<feature>` | `features`, `feature_range`, `prefix`, fitted `fmin_`, `fmax_` | Uses Vaex min/max and maps into the requested range. |
| `vaex.ml.MaxAbsScaler` | `absmax_scaled_<feature>` | `features`, `prefix`, fitted `absmax_` | Divides by maximum absolute value; zero absmax is guarded as `1`. |
| `vaex.ml.RobustScaler` | `robust_scaled_<feature>` | `features`, `with_centering`, `with_scaling`, `percentile_range`, fitted `center_`, `scale_` | Uses approximate percentiles for median and percentile-range scaling. |
| `vaex.ml.LabelEncoder` | `label_encoded_<feature>` | `features`, `prefix`, `allow_unseen`, fitted `labels_` | Maps categories to integers; unseen values raise unless `allow_unseen=True`, then map to `-1`. |
| `vaex.ml.OneHotEncoder` | `<prefix><feature>_<category>` | `features`, `prefix`, `one`, `zero`, fitted `uniques_` | Adds one virtual column per fitted category; missing values get a `missing` column. |
| `vaex.ml.MultiHotEncoder` | `<prefix><feature>_<bit_index>` | `features`, `prefix`, fitted `labels_` | Ordinal-encodes categories then emits binary-code columns. |
| `vaex.ml.FrequencyEncoder` | `frequency_encoded_<feature>` | `features`, `prefix`, `unseen`, fitted `mappings_` | Maps categories to train frequency; unseen strategy is `"nan"` or `"zero"`. |
| `vaex.ml.CycleTransformer` | `<prefix_x><feature><suffix_x>`, `<prefix_y><feature><suffix_y>` | `features`, `n`, `prefix_x`, `prefix_y`, `suffix_x`, `suffix_y` | No-op fit; creates cosine/sine cycle coordinates. |
| `vaex.ml.BayesianTargetEncoder` | `mean_encoded_<feature>` | `features`, `target`, `weight`, `prefix`, `unseen`, fitted `mappings_` | Fits smoothed target means by category. Fit only on train data. |
| `vaex.ml.WeightOfEvidenceEncoder` | `woe_encoded_<feature>` | `features`, `target`, `prefix`, `unseen`, `epsilon`, fitted `mappings_` | Fits log odds by category; target must be binary `0/1` or boolean-like. |
| `vaex.ml.GroupByTransformer` | aggregate names, with `rprefix`/`rsuffix` on collisions | `by`, `agg`, `rprefix`, `rsuffix`, fitted `df_group_` | Fits a grouped aggregate DataFrame, then maps aggregate values to compatible rows. |
| `vaex.ml.KBinsDiscretizer` | `binned_<feature>` | `features`, `n_bins`, `strategy`, `prefix`, `epsilon`, fitted `n_bins_`, `bin_edges_` | Bins continuous features. Strategies: `"uniform"`, `"quantile"`, `"kmeans"`. |
| `vaex.ml.PCA` | `PCA_<component_index>` | `features`, `n_components`, `prefix`, `whiten`, fitted eigen/mean/explained-variance traits | Fits from covariance and means; adds virtual component columns. |
| `vaex.ml.PCAIncremental` | `PCA_<component_index>` | PCA traits plus `batch_size`, fitted `n_samples_seen_`, `noise_variance_` | Uses scikit-learn `IncrementalPCA` during fit; transform uses stored state. |
| `vaex.ml.RandomProjections` | `random_projection_<component_index>` | `features`, `n_components`, `eps`, `matrix_type`, `density`, `prefix`, `random_state`, fitted `random_matrix_` | Uses scikit-learn random projections during fit; transform uses stored matrix. |

## Pipeline

`vaex.ml.Pipeline` subclasses `list`.

| Method | Behavior |
| --- | --- |
| `Pipeline([...])` | Create a list-like ordered pipeline of transformers and optional final predictor. |
| `pipeline.transform(dataframe)` | Apply every object in order by calling `.transform(...)`; returns the final DataFrame. |
| `pipeline.predict(dataframe)` | Apply all objects except the last with `.transform(...)`, then call `.predict(...)` on the last object; returns a numpy array. |
| `pipeline.save(path)` | Serialize pipeline state to JSON or YAML selected by file extension/content support. |
| `pipeline.load(path)` | Replace current list contents with deserialized pipeline objects. |

The save path is a normal filesystem path. Its parent directory must exist.
Loaded pipelines require the same public packages/classes that were used to save
them.

## Scikit-learn wrappers

Import requirement:

```python
import vaex.ml.sklearn
from vaex.ml.sklearn import Predictor, IncrementalPredictor
```

| Class | Key traits | Memory behavior | Prediction output |
| --- | --- | --- | --- |
| `vaex.ml.sklearn.Predictor` | `model`, `features`, `target`, `prediction_name`, `prediction_type` | `fit` copies `df[features].values` and target to memory; `predict` materializes prediction array; `transform` adds a lazy virtual column. | `prediction_type` is `"predict"`, `"predict_proba"`, or `"predict_log_proba"`. |
| `vaex.ml.sklearn.IncrementalPredictor` | Predictor traits plus `batch_size`, `num_epochs`, `shuffle`, `partial_fit_kwargs` | `fit` iterates over Vaex chunks and calls `.partial_fit(...)`; `predict` materializes prediction array; `transform` is lazy. | For classifiers, pass required classes through `partial_fit_kwargs`. |

The wrapped estimator is not modified. Vaex stores the estimator object in the
wrapper state for pipeline serialization.

## KMeans

`KMeans` lives in `vaex.ml.cluster`:

```python
import vaex.ml.cluster
model = vaex.ml.cluster.KMeans(features=["x", "y"], n_clusters=3)
```

| Field | Meaning |
| --- | --- |
| `features` | Columns or expression strings used as cluster coordinates. |
| `n_clusters` | Number of clusters, default `2`. |
| `init` | `"random"` or explicit centers shaped as clusters by features. |
| `n_init` | Number of initializations; best inertia is retained. |
| `max_iter` | Maximum iterations per run. |
| `random_state` | Deterministic random initialization seed. |
| `prediction_label` | Output virtual column name, default `prediction_kmeans`. |
| fitted `cluster_centers`, `inertia` | Learned centers and inertia. |

`transform(df)` adds the virtual prediction column. KMeans is CPU-oriented here;
do not advertise GPU support.

## Optional estimator wrappers

These wrappers are optional because they require third-party packages and may
have version-specific native parameters.

| Wrapper | Import | Notes |
| --- | --- | --- |
| `XGBoostModel` | `import vaex.ml.xgboost` then `vaex.ml.xgboost.XGBoostModel` | Requires `xgboost`; wraps `xgboost.train`; supports `evals`, `early_stopping_rounds`, `evals_result`; default prediction column `xgboost_prediction`. |
| `LightGBMModel` | `import vaex.ml.lightgbm` then `vaex.ml.lightgbm.LightGBMModel` | Requires `lightgbm`; wraps `lightgbm.train`; supports validation sets/names and callbacks; default prediction column `lightgbm_prediction`. |
| `CatBoostModel` | `import vaex.ml.catboost` then `vaex.ml.catboost.CatBoostModel` | Requires `catboost`; supports `prediction_type`, optional chunked training with `batch_size`, and batch model weights; default prediction column `catboost_prediction`. |
| TensorFlow accessor/model | `import vaex.ml.tensorflow` | Optional TensorFlow extra; Keras generator/model bridge only when TensorFlow is installed. CPU-only status here is unverified for this optional path. |
| Incubator wrappers | `vaex.ml.incubator.river`, `vaex.ml.incubator.annoy`, `vaex.ml.incubator.pygbm` | Experimental integrations; inspect installed package availability before use. |
