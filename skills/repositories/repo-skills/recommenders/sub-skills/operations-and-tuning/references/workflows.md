# Tuning Workflows

## Purpose

Use this reference to plan Recommenders hyperparameter exploration without immediately launching long notebook, cloud, or service jobs.

## Local parameter grids

The lightweight utility is:

```python
from recommenders.tuning.parameter_sweep import generate_param_grid

grid = generate_param_grid({
    "similarity_type": ["jaccard", "cosine"],
    "time_decay_coefficient": [7, 30],
})
```

Use local grids when:

- The model can run on a small fixture or sampled dataset.
- The user needs a reproducible list of configurations.
- Cloud credentials or external services are not yet available.

Keep grids bounded. A dictionary with five parameters and ten values each is a 100,000-run plan, not a smoke test.

## NNI-style tuning

Recommenders includes NNI helper utilities and training scripts for selected model examples. Use this path only when:

1. `nni` is installed from the experimental dependency path.
2. The training script and data files exist in the user's working project.
3. The user accepts that an NNI service/trial process may be launched.
4. Metrics to optimize are unambiguous.

If those requirements are missing, provide a search-space and command plan rather than starting the service.

## AzureML HyperDrive pattern

The repository demonstrates HyperDrive-style training for Surprise SVD and Wide&Deep. Treat those as patterns:

- Prepare train/validation data artifacts first.
- Define rating and ranking metrics explicitly.
- Pass data path, column, and model hyperparameters as script arguments.
- Log metrics to AzureML only when an AzureML run context is available.

Do not assume AzureML is available from a base Recommenders install. The workflow needs workspace credentials, compute, data stores, optional dependencies, and user approval for remote jobs.

## Service sizing helpers

For simple Kubernetes throughput arithmetic:

```python
from recommenders.utils.k8s_utils import qps_to_replicas, replicas_to_qps, nodes_to_replicas

replicas = qps_to_replicas(target_qps=100, processing_time=0.05, max_qp_replica=10, target_utilization=0.7)
```

Use these helpers for estimates, not capacity guarantees. Real deployment sizing still needs load-test evidence.

## Environment readiness workflow

1. Run the bundled environment report helper.
2. Confirm which optional family is required: Spark, GPU/deep learning, experimental package, Databricks/AzureML/AKS.
3. Install only the relevant extra in a suitable private environment.
4. Run a tiny backend smoke before full notebook or benchmark execution.
5. Preserve any unavailable backend as an explicit limitation.

## Safe tuning report template

```text
Objective metric: <metric and k/threshold>
Data: <dataset/sample/split>
Model: <family and required backend>
Search space: <bounded parameter grid>
Execution mode: local smoke | NNI | AzureML | benchmark notebook
Required extras/services: <base/spark/gpu/experimental/cloud>
Stop conditions: <max trials/time/cost>
Skipped paths: <why>
```
