# Operationalization Reference

## Purpose

Read this for Recommenders deployment and cloud-operation patterns. These workflows are useful but not safe to run automatically because they may need credentials, cluster ids, cloud resources, DBFS uploads, package installation on remote clusters, or load tests.

## Databricks installation pattern

The repository includes a Databricks installation script as evidence. Its operational shape is:

1. Authenticate with a Databricks CLI profile.
2. Identify or create a running cluster.
3. Upload or install Recommenders package artifacts and optional libraries.
4. Optionally install Spark/MMLSpark and operationalization dependencies.
5. Optionally upload connector JARs to DBFS.

Do not run this path unless the user provides:

- Databricks workspace/profile configuration.
- Target cluster id or explicit permission to create a cluster.
- DBFS destination.
- Whether overwrites are allowed.
- Whether operationalization extras and external JARs may be installed.

## AzureML patterns

Recommenders examples show AzureML usage for:

- Training SAR or Surprise/Wide&Deep style models on remote compute.
- HyperDrive parameter search.
- AzureML Designer components for SAR train/score and metrics.

Before execution, require:

- AzureML workspace authentication.
- Compute target and budget/stop conditions.
- Data store paths for train/validation/test artifacts.
- Explicit metric list and model parameter search space.
- Approval for remote jobs and generated artifacts.

## AKS and load testing

Operationalization examples include AKS scoring and Locust-style load testing. Treat these as deployment tasks that require:

- Existing service endpoint or deployment manifests.
- Credentials and network access.
- Rate limits and stop conditions.
- A small sample scoring payload.

Use `qps_to_replicas`, `replicas_to_qps`, and `nodes_to_replicas` only as arithmetic estimates. They do not replace a real load test.

## Cosmos DB / real-time recommendation API pattern

The real-time ALS operationalization pattern stores precomputed recommendations and serves them through an API. Validate:

- Offline recommender output schema.
- User/item id serialization.
- Cosmos DB collection/database names and credentials.
- Cold-start fallback behavior.
- Scoring latency target.

## Safe response when credentials are missing

If a user asks to operationalize but has not provided credentials or target resource ids, produce a prerequisite checklist and dry-run plan. Do not run cloud commands or install libraries into a remote cluster.

## Optional extras mapping

| Surface | Extra/dependency class | Execution gate |
|---|---|---|
| Spark ALS/Spark metrics | `[spark]`, Java/JDK, PySpark | Spark session smoke |
| GPU/deep learning | `[gpu]`, TensorFlow/PyTorch, CUDA runtime | framework device smoke |
| NNI tuning | `[experimental]` NNI | local NNI service/trial smoke |
| Surprise/LightFM/VW/xLearn | `[experimental]` plus possible native binaries | import/build/tool smoke |
| Databricks | databricks-cli, workspace profile, cluster | authenticated read-only cluster status first |
| AzureML | AzureML SDK, workspace/compute/data stores | authenticated workspace/compute probe first |
