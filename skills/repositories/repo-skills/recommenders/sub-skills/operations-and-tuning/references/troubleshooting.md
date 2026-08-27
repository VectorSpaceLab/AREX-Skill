# Operations and Tuning Troubleshooting

## Optional extra missing

Symptoms:
- `ModuleNotFoundError: torch`, `tensorflow`, `pyspark`, `nni`, `surprise`, `lightfm`, or `vowpalwabbit`.

Fix:
1. Identify the exact workflow family.
2. Install only the needed extra or package in a private environment.
3. Run a tiny import/backend smoke.
4. Do not install `[all]` unless the user accepts broad optional dependencies.

## GPU visible but model cannot run

Symptoms:
- `nvidia-smi` works but TensorFlow/PyTorch imports fail or report no devices.

Fix:
- Verify the framework package, CUDA wheel/runtime, driver compatibility, and device allocation.
- A visible GPU is not enough; the selected framework must allocate a tiny tensor/session.

## Spark/JDK failures

Symptoms:
- Java gateway exits, missing `pyspark`, unresolved Spark classes, Spark evaluation import failures.

Fix:
- Install `recommenders[spark]`, verify Java/JDK, and start a small Spark session before running Spark splitters, ALS, or Spark metrics.

## NNI service or trial failures

Symptoms:
- NNI helpers cannot find experiment status, metrics are missing, or trials never stop.

Fix:
- Confirm NNI installation, experiment id, tuner config, search space, trial command, metric file, timeout, and stop criteria.
- For planning-only tasks, generate the search space and do not launch NNI.

## AzureML failures

Symptoms:
- Missing workspace, compute target, datastore path, or run context.

Fix:
- Require authenticated workspace details and data artifacts before remote execution.
- In local planning, describe script arguments and metrics without submitting jobs.

## Databricks failures

Symptoms:
- Cluster not found, cluster terminated, missing CLI profile, DBFS upload failure, library install pending/fails.

Fix:
- Run authenticated read-only cluster/profile checks before any install.
- Ask whether cluster creation, overwrite, and external JAR installation are allowed.
- Do not upload or install when the target cluster is ambiguous.

## Long benchmark runs

Symptoms:
- Notebook or benchmark exceeds expected runtime or downloads large data.

Fix:
- Switch to a smoke fixture or smaller model subset.
- Record skipped models/backends and why.
- Set max runtime and stop conditions before retrying.

## K8s sizing misuse

Symptoms:
- Replica estimates are treated as production capacity guarantees.

Fix:
- Treat `qps_to_replicas`, `replicas_to_qps`, and `nodes_to_replicas` as arithmetic planning helpers only.
- Confirm actual processing time, target utilization, autoscaling policy, and load-test evidence.
