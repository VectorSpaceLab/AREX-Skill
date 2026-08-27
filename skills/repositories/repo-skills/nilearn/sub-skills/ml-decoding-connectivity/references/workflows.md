# Workflows

These recipes are intentionally compact and leakage-aware. Replace synthetic or
placeholder inputs with outputs from `data-io-signal`, `maskers-regions`, and
`datasets-interfaces` as appropriate.

## Supervised Image Decoding

1. Confirm the unit of prediction: one 3D image/sample, one row in `y`, and
   optional `groups`/runs of the same length.
2. Choose a mask. If the mask is unknown or needs extraction from labels/maps,
   route to `maskers-regions`; if resampling or smoothing is needed, route to
   `data-io-signal`.
3. Use `Decoder` for classification or `DecoderRegressor` for continuous
   targets. Keep feature screening, scaling, and hyperparameter selection
   inside the estimator/CV process.
4. Use run-aware CV for fMRI tasks when samples from the same run/session are
   correlated. Do not randomly split adjacent volumes unless the analysis
   explicitly models temporal dependence.
5. Inspect `cv_scores_`, selected coefficients, and class balance before
   interpreting maps. Route plotting of coefficient/stat maps to
   `plotting-reporting`.

Minimal pattern:

```python
from sklearn.model_selection import LeaveOneGroupOut
from nilearn.decoding import Decoder

cv = LeaveOneGroupOut()
decoder = Decoder(
    estimator="svc",
    mask=mask_img,
    cv=cv,
    scoring="balanced_accuracy",
    screening_percentile=20,
    n_jobs=1,
)
decoder.fit(imgs, labels, groups=runs)
```

## Searchlight Maps

1. Use `SearchLight` when the scientific question is local information, not
   whole-brain prediction.
2. Provide both `mask_img` and a smaller `process_mask_img` when possible.
3. Start with `radius=2.0`, `n_jobs=1`, and a cheap CV split; increase only
   after labels, mask overlap, and runtime look correct.
4. Treat `scores_` as a score image over the process mask. Visualization belongs
   in `plotting-reporting`.

```python
from nilearn.decoding import SearchLight

searchlight = SearchLight(
    mask_img=brain_mask,
    process_mask_img=analysis_mask,
    radius=2.0,
    estimator="svc",
    scoring="balanced_accuracy",
    cv=cv,
    n_jobs=1,
)
searchlight.fit(fmri_imgs, labels)
scores = searchlight.scores_
```

## SpaceNet and FREM

Use these only when their added modeling assumptions are intended:

- `SpaceNetClassifier`/`SpaceNetRegressor` add graph-net or TV-L1 spatial
  penalties and can be much slower than `Decoder`.
- `FREMClassifier`/`FREMRegressor` use clustering plus ensembling and default
  to more CV splits than `Decoder`.
- Prototype on a small mask, low `max_iter`, or fewer folds. Then scale
  deliberately and record `screening_percentile`, `cv`, and `random_state`.

```python
from nilearn.decoding import FREMClassifier

model = FREMClassifier(
    estimator="svc",
    mask=mask_img,
    cv=cv,
    clustering_percentile=10,
    screening_percentile=20,
    n_jobs=1,
)
model.fit(imgs, labels, groups=runs)
```

## Connectivity Features from Time Series

1. Extract one time-series matrix per subject with a labels/maps/spheres masker;
   route this extraction to `maskers-regions`.
2. Each subject matrix must be 2D `(n_timepoints, n_regions)`. The number of
   regions must match across subjects; timepoints may differ.
3. For group ML, use `vectorize=True`. With tangent features, fit the
   `ConnectivityMeasure` on training subjects only inside each split.
4. Train the classifier/regressor on the resulting connectome feature rows.

Leakage-safe tangent pattern:

```python
from nilearn.connectome import ConnectivityMeasure
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
for train, test in cv.split(subject_time_series, labels):
    train_series = [subject_time_series[i] for i in train]
    test_series = [subject_time_series[i] for i in test]

    connectome = ConnectivityMeasure(
        kind="tangent", vectorize=True, discard_diagonal=True
    )
    X_train = connectome.fit_transform(train_series)
    X_test = connectome.transform(test_series)

    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    clf.fit(X_train, labels[train])
    fold_score = clf.score(X_test, labels[test])
```

Do not call `fit_transform` on all subjects before cross-validation when the
features use `kind='tangent'`, vector confound cleaning, or any group-level
reference.

## Group Tangent Space and Confounds

- `ConnectivityMeasure(..., confounds=...)` cleans confounds only when
  `vectorize=True`; it raises when `confounds` are provided with
  `vectorize=False`.
- Tangent space needs a group reference. `transform` with a single subject is
  not a valid group tangent operation; use at least the held-out group intended
  by the model evaluation.
- `inverse_transform` can reconstruct matrices from vectorized outputs, but it
  should not be used to claim original time-series recovery.

## CanICA, DictLearning, and Parcellation Handoffs

1. Use `CanICA` for independent component maps and `DictLearning` for sparse
   dictionary maps that may be more stable.
2. Use `Parcellations` when the next step needs discrete region labels or
   compressed region signals.
3. Fit unsupervised maps/parcels only on the training data if the components are
   part of a predictive model evaluation.
4. Convert fitted maps/labels to time series with the appropriate masker via
   `maskers-regions`, then continue to `ConnectivityMeasure` or scikit-learn.

```python
from nilearn.decomposition import CanICA

canica = CanICA(n_components=20, mask=mask_img, random_state=0, n_jobs=1)
canica.fit(training_imgs)
components_img = canica.components_img_
```

## Mass-Univariate Permutation Tests

1. Build a 2D target matrix: rows are samples/subjects, columns are voxels or
   features. If starting from images, route masking to `maskers-regions`.
2. Build `tested_vars` with one row per sample. Keep nuisance variables in
   `confounding_vars`, not mixed into the target matrix.
3. Use small `n_perm` only for smoke checks. For inference, choose `n_perm`
   based on desired p-value resolution and runtime.
4. Pass `masker`, `threshold`, or `tfce=True` only when cluster/TFCE inference
   is intended and the mask geometry is valid.

```python
from nilearn.mass_univariate import permuted_ols

out = permuted_ols(
    tested_vars=design[:, [0]],
    target_vars=voxel_matrix,
    confounding_vars=confounds,
    n_perm=1000,
    two_sided_test=True,
    random_state=0,
    n_jobs=1,
    output_type="dict",
)
logp = out["logp_max_t"]
```
