# API Reference — sampling algorithms

This file is a compact catalog of the public sampler classes and helper
functions that matter most for day-to-day routing.

## Core signatures confirmed in the private inspection environment

| Symbol | Signature / key arguments | Notes |
|---|---|---|
| `FunctionSampler` | `FunctionSampler(func=None, accept_sparse=True, kw_args=None, validate=True)` | Wrap custom resampling logic. |
| `RandomOverSampler` | `RandomOverSampler(sampling_strategy='auto', random_state=None, shrinkage=None)` | Duplicate-based over-sampling; `shrinkage` only for numeric data. |
| `ADASYN` | `ADASYN(sampling_strategy='auto', random_state=None, n_neighbors=5)` | Adaptive synthetic over-sampling. |
| `SMOTE` | `SMOTE(sampling_strategy='auto', random_state=None, k_neighbors=5)` | Synthetic minority over-sampling. |
| `SMOTENC` | `SMOTENC(categorical_features, *, categorical_encoder=None, sampling_strategy='auto', random_state=None, k_neighbors=5)` | Mixed numeric/categorical data. |
| `SMOTEN` | `SMOTEN(categorical_encoder=None, *, sampling_strategy='auto', random_state=None, k_neighbors=5)` | All-categorical data. |
| `BorderlineSMOTE` | `BorderlineSMOTE(..., kind='borderline-1')` | Border-focused synthetic sampling. |
| `KMeansSMOTE` | `KMeansSMOTE(..., k_neighbors=2, kmeans_estimator=None, cluster_balance_threshold='auto', density_exponent='auto')` | Cluster-aware SMOTE variant. |
| `SVMSMOTE` | `SVMSMOTE(..., svm_estimator=None, out_step=0.5)` | SVM-guided synthetic sampling. |
| `RandomUnderSampler` | `RandomUnderSampler(sampling_strategy='auto', random_state=None, replacement=False)` | Simple under-sampling. |
| `TomekLinks` | `TomekLinks(sampling_strategy='auto', n_jobs=None)` | Cleaning with Tomek links. |
| `EditedNearestNeighbours` | `EditedNearestNeighbours(..., kind_sel='all', n_jobs=None)` | Nearest-neighbour cleaning. |
| `RepeatedEditedNearestNeighbours` | `RepeatedEditedNearestNeighbours(..., max_iter=100, kind_sel='all', n_jobs=None)` | Iterated ENN cleaning. |
| `AllKNN` | `AllKNN(..., allow_minority=False, n_jobs=None)` | Repeated ENN-style cleaning. |
| `OneSidedSelection` | `OneSidedSelection(..., n_seeds_S=1, n_jobs=None)` | Controlled under-sampling. |
| `CondensedNearestNeighbour` | `CondensedNearestNeighbour(..., n_seeds_S=1, n_jobs=None)` | Prototype selection. |
| `NeighbourhoodCleaningRule` | `NeighbourhoodCleaningRule(..., threshold_cleaning=0.5, n_jobs=None)` | Cleaning rule. |
| `NearMiss` | `NearMiss(..., version=1, n_neighbors=3, n_neighbors_ver3=3, n_jobs=None)` | Distance-based under-sampling. |
| `ClusterCentroids` | `ClusterCentroids(..., estimator=None, voting='auto')` | Prototype generation. |
| `InstanceHardnessThreshold` | `InstanceHardnessThreshold(..., estimator=None, cv=5, n_jobs=None)` | Hardness-based under-sampling. |
| `SMOTEENN` | `SMOTEENN(..., smote=None, enn=None, n_jobs=None)` | SMOTE + ENN. |
| `SMOTETomek` | `SMOTETomek(..., smote=None, tomek=None, n_jobs=None)` | SMOTE + TomekLinks. |
| `check_sampling_strategy` | helper | Validate sampling-policy inputs. |
| `check_target_type` | helper | Normalize label targets. |
| `check_neighbors_object` | helper | Validate neighbor-like objects. |

## Choice notes

- `SMOTENC` and `SMOTEN` are the main categorical branches.
- `FunctionSampler` is the safest way to preserve custom logic without inventing
  a new estimator class.
- `SMOTEENN` and `SMOTETomek` are convenience wrappers, not fundamentally new
  algorithm families.
- Use the helper checks when a workflow depends on user-supplied strategy or
  neighbor objects.

## The smallest reliable smoke

The bundled `sampler_smoke.py` script should confirm:

- over-sampling count growth,
- under-sampling count reduction,
- one combine sampler,
- custom callable sampling via `FunctionSampler`, and
- at least one categorical-feature path when available.
