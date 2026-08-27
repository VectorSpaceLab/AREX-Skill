# Repository provenance

This repo skill was generated from the Amazon SageMaker Python SDK v3 source.

## Source snapshot

- Repository: `aws/sagemaker-python-sdk`
- Public source URL: `https://github.com/aws/sagemaker-python-sdk`
- Commit: `b6eb059fcacd782f179892e80e1a046bd239226d`
- Branch: `master`
- Exact tag: none recorded at the generation commit
- Working tree state during generation: dirty because production artifacts under `skills/` were untracked

## Package versions

- Root meta package `sagemaker`: `3.20.0` from `VERSION`
- `sagemaker-core`: `2.20.0`
- `sagemaker-train`: `1.20.0`
- `sagemaker-serve`: `1.20.0`
- `sagemaker-mlops`: `1.20.0`

The inspection environment installed the four local subpackages in editable mode
for API/signature checks. The root meta distribution was not installed as a
separate distribution during inspection; use the root `VERSION` file above as
this skill's v3 meta-package baseline.

## Evidence paths used

- Root guidance: `AGENTS.md`, `llms.txt`, `README.rst`, `migration.md`
- Docs: `docs/index.rst`, `docs/installation.rst`, `docs/quickstart.rst`,
  `docs/sagemaker_core/index.rst`, `docs/training/index.rst`,
  `docs/model_customization/`, `docs/inference/index.rst`, `docs/ml_ops/`
- Core package: `sagemaker-core/README.rst`, `sagemaker-core/pyproject.toml`,
  `sagemaker-core/src/sagemaker/core/`, `sagemaker-core/src/sagemaker/core/lineage/`,
  representative unit tests under `sagemaker-core/tests/unit/`
- Train package: `sagemaker-train/pyproject.toml`,
  `sagemaker-train/src/sagemaker/train/`, `sagemaker-train/src/sagemaker/ai_registry/`,
  representative unit/integration tests under `sagemaker-train/tests/`
- Serve package: `sagemaker-serve/pyproject.toml`,
  `sagemaker-serve/src/sagemaker/serve/`, representative unit/integration tests
  under `sagemaker-serve/tests/`
- MLOps package: `sagemaker-mlops/README.md`, `sagemaker-mlops/pyproject.toml`,
  `sagemaker-mlops/src/sagemaker/mlops/`, representative unit/integration tests
  under `sagemaker-mlops/tests/`
- Examples: `v3-examples/training-examples/`, `v3-examples/inference-examples/`,
  `v3-examples/model-customization-examples/`, `v3-examples/ml-ops-examples/`

## Refresh signals

Refresh this skill when any of the following change:

- The root v3 policy, package names, or v2 migration mappings.
- `ModelTrainer`, `ModelBuilder`, specialized trainer, evaluator, or Pipeline
  constructor/method signatures.
- Import behavior for `sagemaker.serve` / `sagemaker.mlops` and region handling.
- Public examples under `v3-examples/`, especially model customization,
  local-serving, HPO, or MLOps examples.
- Package dependencies such as `torch`, `mlflow`, `pyiceberg`, `s3fs`, or
  Feature Store / local pipeline optional dependencies.
