---
name: data-pipeline-utilities
description: "Data generation, preprocessing, metrics, model selection, feature
  extraction, explainers, and time-series utilities for cuML workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cuML data-pipeline utilities

Use this sub-skill when a cuML workflow needs supporting utilities rather than a full model-training recipe: synthetic data, train/test or K-fold splits, preprocessing, categorical/text feature preparation, metrics, pairwise distances/kernels, model explainers, or time-series data/schema utilities.

## Route here for

- `cuml.datasets`: `make_blobs`, `make_classification`, `make_regression`, `make_arima`.
- `cuml.model_selection`: `train_test_split`, `KFold`.
- `cuml.preprocessing`: scalers, normalizers, imputers, encoders, binarizers, `TargetEncoder`, and functional helpers.
- `cuml.metrics`: classification, regression, clustering, pairwise distance, and pairwise kernel metrics.
- `cuml.feature_extraction.text`: `CountVectorizer`, `HashingVectorizer`, `TfidfVectorizer`.
- `cuml.explainer`: `KernelExplainer`, `PermutationExplainer`, `TreeExplainer` route and setup notes.
- `cuml.tsa` and `make_arima` only for utility/schema guidance; these APIs are deprecated and should be handled carefully.

## Route away

- Full estimator selection, fitting, prediction, serialization, and output-type workflows: use sibling sub-skill `python-estimators`.
- Distributed or multi-GPU Dask variants of preprocessing/text/model workflows: use sibling sub-skill `distributed-dask`.
- Zero-code-change scikit-learn acceleration via `cuml.accel`: use sibling sub-skill `sklearn-accel`.
- Source builds, C++ examples, native CI test selection, or CUDA toolchain diagnosis: use sibling sub-skill `native-build-and-cpp` or root troubleshooting.

## Operating procedure

1. Read `references/api-reference.md` to identify the exact utility surface, signatures, input containers, output conventions, and deprecations.
2. Read `references/workflows.md` for compact recipes that combine generation, splitting, preprocessing, target/text encoding, metrics, explainers, and time-series schemas.
3. Read `references/troubleshooting.md` when imports, CUDA, container types, category handling, metrics, text vectorization, SHAP, or time-series schemas fail.
4. For a fast local check, run the bundled smoke script from the generated skill tree:

   ```bash
   python sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py --help
   python sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py --case core
   ```

Keep utility runs tiny unless the downstream task explicitly asks for scale or benchmark evidence. Do not infer estimator quality from utility-only metrics; hand off full training or model debugging to the estimator sub-skill.
