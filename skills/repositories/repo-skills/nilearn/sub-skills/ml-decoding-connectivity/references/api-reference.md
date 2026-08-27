# API Reference

This reference summarizes the ML/connectivity APIs most often needed by agents.
Use it with the installed Nilearn source-checkout/dev version and scikit-learn
shape conventions.

## Decoding Estimators

| API | Use for | Key parameters | Input to `fit` | Main fitted outputs |
| --- | --- | --- | --- | --- |
| `nilearn.decoding.Decoder` | Classification from 3D/4D Niimg-like samples or surface samples. | `estimator='svc'`, `mask=None`, `cv=10`, `param_grid=None`, `screening_percentile=20`, `screening_n_features=None`, `scoring='roc_auc'`, `standardize=True`, `mask_strategy='background'`, `n_jobs=1`, `estimator_args=None`. | `X`: list/4D image/surface samples; `y`: one label per sample; optional `groups` in `fit`. | `mask_img_`/masker state, selected estimator(s), `classes_`, `cv_scores_`, `coef_`/weight images where supported. |
| `nilearn.decoding.DecoderRegressor` | Regression from images/surfaces. | Same as `Decoder`, with `estimator='svr'` and `scoring='r2'`. | `X` image-like samples, `y` continuous target with matching length. | Cross-validated scores and model coefficients where estimator supports them. |
| `nilearn.decoding.SearchLight` | Local sphere-based classification/regression score maps. | `mask_img=None`, `process_mask_img=None`, `radius=2.0`, `estimator='svc'`, `n_jobs=1`, `scoring=None`, `cv=None`, `random_state=0`, `estimator_args=None`. | `imgs`: 4D image/list of 3D images; `y`: one target per image. | `scores_` array over voxels in the process mask, `mask_img_`, estimator metadata. |
| `nilearn.decoding.SpaceNetClassifier` | Spatially structured sparse classification. | `penalty='graph-net'`, `loss='logistic'`, `l1_ratios=0.5`, `alphas=None`, `n_alphas=10`, `max_iter=200`, `cv=8`, `screening_percentile=20`, `n_jobs=1`. | Image-like samples and class labels. | `coef_`, selected regularization, masked coefficient images, CV scores. |
| `nilearn.decoding.SpaceNetRegressor` | Spatially structured sparse regression. | Same SpaceNet controls, without `loss`; default penalty is `graph-net`. | Image-like samples and continuous target. | `coef_`, selected regularization, coefficient images, CV scores. |
| `nilearn.decoding.FREMClassifier` | Fast ensembling of regularized models with feature clustering. | `estimator='svc'`, `cv=30`, `clustering_percentile=10`, `screening_percentile=20`, `scoring='roc_auc'`, `n_jobs=1`. | Image-like samples and class labels. | Ensemble coefficients/scores and classifier outputs. |
| `nilearn.decoding.FREMRegressor` | FREM-style regression. | `estimator='svr'`, `cv=30`, `clustering_percentile=10`, `screening_percentile=20`, `scoring='r2'`, `n_jobs=1`. | Image-like samples and continuous target. | Ensemble coefficients/scores and predictions. |

Notes:

- `Decoder`/`DecoderRegressor` are high-level wrappers; use raw scikit-learn
  estimators only after extracting features with a masker or connectome step.
- `screening_percentile` is a univariate feature screen. Treat it as part of
  model selection inside CV, not as a precomputed mask learned on all samples.
- `SpaceNet` and `SearchLight` can be slow; prototype with small masks, fewer
  folds, low `n_jobs`, and reduced iteration counts before scaling.

## Connectivity and Covariance

| API | Use for | Key parameters | Input | Output / fitted state |
| --- | --- | --- | --- | --- |
| `nilearn.connectome.ConnectivityMeasure` | Subject-level covariance/correlation/precision/partial-correlation/tangent matrices. | `cov_estimator=None`, `kind='covariance'`, `vectorize=False`, `discard_diagonal=False`, `standardize=True`, `verbose=0`. | Iterable of 2D arrays, one per subject, each `(n_timepoints, n_regions)` with the same number of regions. | `fit_transform` returns `(n_subjects, n_regions, n_regions)` or vectorized lower triangles; `mean_`, `cov_estimator_`, `n_features_in_`, and `whitening_` for tangent. |
| `nilearn.connectome.GroupSparseCovariance` | Sparse precision matrices sharing a sparsity pattern across subjects. | `alpha=0.1`, `tol=0.001`, `max_iter=10`, `memory=None`, `memory_level=0`. | List of subject arrays shaped `(n_samples, n_features)`. | `covariances_`, `precisions_`, empirical covariances. |
| `nilearn.connectome.GroupSparseCovarianceCV` | Cross-validated alpha for shared sparse precision estimation. | `alphas=4`, `n_refinements=4`, `cv=None`, `tol_cv=0.01`, `max_iter_cv=50`, `n_jobs=1`, `early_stopping=True`. | Same as `GroupSparseCovariance`. | Selected `alpha_`, covariance/precision estimates, CV diagnostics. |
| `nilearn.connectome.sym_matrix_to_vec` / `vec_to_sym_matrix` | Manual vectorization and inverse vectorization of symmetric matrices. | `discard_diagonal=False` for vectorization. | Symmetric matrix/matrices or vectorized lower triangles. | Feature vectors or reconstructed symmetric matrices. |

`ConnectivityMeasure(kind='tangent', vectorize=True, discard_diagonal=True)` is
the common choice for group-level machine-learning features. Fit it only on the
training subjects in each CV split, then transform held-out subjects with the
fitted measure to avoid leakage through the group mean.

## Decomposition and Region Learning

| API | Use for | Key parameters | Input | Output / fitted state |
| --- | --- | --- | --- | --- |
| `nilearn.decomposition.CanICA` | Canonical ICA maps from multi-subject functional data. | `n_components=20`, `smoothing_fwhm=6`, `do_cca=True`, `threshold='auto'`, `n_init=10`, `mask_strategy='epi'`, `n_jobs=1`. | List of 4D Niimg-like runs/subjects, optional confounds. | `components_`, `components_img_`, `mask_img_`, masker state; `transform` returns loadings/time courses. |
| `nilearn.decomposition.DictLearning` | Stable sparse maps initialized from CanICA or supplied dictionary. | `n_components=20`, `n_epochs=1`, `alpha=10`, `reduction_ratio='auto'`, `dict_init=None`, `batch_size=20`, `method='cd'`, `mask_strategy='epi'`. | List of 4D images, optional confounds. | `components_init_`, `components_`, `components_img_`, masker state. |
| `nilearn.regions.Parcellations` | Data-driven parcels by k-means, ward, complete linkage, or related methods. | `method=None`, `n_parcels=50`, `smoothing_fwhm=4.0`, `standardize=False`, `scaling=False`, `n_iter=10`, `n_jobs=1`. | 4D images or lists of images. | `labels_img_`/maps, transformed region signals, inverse-transformed images. |

Decomposition and parcellation produce maps or labels; route detailed signal
extraction with labels/maps maskers to `maskers-regions` before estimating a
connectome.

## Mass-Univariate Statistics

| API | Use for | Key parameters | Input | Output |
| --- | --- | --- | --- | --- |
| `nilearn.mass_univariate.permuted_ols` | Voxel/featurewise OLS with permutation p-values and optional cluster/TFCE inference. | `tested_vars`, `target_vars`, `confounding_vars=None`, `model_intercept=True`, `n_perm=10000`, `two_sided_test=True`, `random_state=None`, `n_jobs=1`, `masker=None`, `tfce=False`, `threshold=None`, `output_type='dict'`. | `tested_vars`: `(n_samples, n_regressors)`; `target_vars`: `(n_samples, n_targets)` or image-derived matrix; optional confounds. | Dict outputs such as `t`, `logp_max_t`, `h0_max_t`; with `tfce` or `threshold`, additional corrected TFCE/cluster outputs. |

Use `n_perm` small only for code checks. Final inference needs enough
permutations for the target p-value resolution and should record the random
state.
