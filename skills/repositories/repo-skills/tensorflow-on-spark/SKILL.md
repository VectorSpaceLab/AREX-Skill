---
name: tensorflow-on-spark
description: "Operate TensorFlowOnSpark workflows that combine TensorFlow
  training, inference, TFRecords, and Spark clusters or Spark ML pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlowOnSpark

Use this repo skill when a task involves the `tensorflowonspark` package, Yahoo TensorFlowOnSpark, distributed TensorFlow on Apache Spark, `TFCluster`, `TFNode.DataFeed`, Spark ML `TFEstimator` / `TFModel`, TFRecord DataFrame conversion, or converting TensorFlow examples to `spark-submit` workflows.

TensorFlowOnSpark lets a Spark application start TensorFlow functions on executors, coordinate node reservations, feed Spark RDD or DataFrame data into TensorFlow workers, and shut the cluster down after training or inference. Most practical tasks need both Python-package checks and Spark runtime checks.

## Install and first checks

For a normal Python environment, install the public package and the runtime dependencies needed by the workflow:

```bash
pip install tensorflowonspark
# Add TensorFlow, PySpark, NumPy/SciPy/HDF5, and Spark/Java according to your cluster policy.
# For current TensorFlow 2.x CPU-only inspection, a package such as tensorflow-cpu can be sufficient.
```

For a repository development checkout, use an editable install only in a private development environment. TensorFlowOnSpark 2.2.5 uses legacy packaging and `pkg_resources`; if modern packaging tools reject its metadata or remove `pkg_resources`, apply that repair in the development environment rather than baking local paths into runtime instructions.

1. Confirm the package imports:

   ```bash
   python - <<'PY'
   import tensorflowonspark
   from tensorflowonspark import TFCluster, TFNode, TFParallel, dfutil
   from tensorflowonspark.pipeline import TFEstimator, TFModel
   print(tensorflowonspark.__version__)
   PY
   ```

2. Confirm Spark and Java before running native Spark jobs:

   ```bash
   python scripts/check_environment.py --json
   ```

3. For Spark-fed training/inference, confirm the Spark application has one task per executor, enough executor slots for the TensorFlow cluster, `spark.python.worker.reuse` for background mode, and the TensorFlow Hadoop jar on the Spark classpath when TFRecords are used.

## Route by task

| User task | Read |
|---|---|
| Start, stop, or debug a `TFCluster.run(...)` job; reservation waits; TensorBoard URL; TF_CONFIG; GPU allocation; `TFParallel.run(...)` | [cluster-lifecycle](sub-skills/cluster-lifecycle/SKILL.md) |
| Write a `map_fun(args, ctx)` using `InputMode.SPARK`; feed RDD/DStream rows; return inference results; handle `DataFeed` timeouts or early termination | [datafeed-inputmode](sub-skills/datafeed-inputmode/SKILL.md) |
| Train or infer with Spark ML DataFrames using `TFEstimator` or `TFModel`; map DataFrame columns to TensorFlow tensors; load SavedModels | [spark-ml-pipelines](sub-skills/spark-ml-pipelines/SKILL.md) |
| Save/load TFRecords as Spark DataFrames; reason about `tf.train.Example` schemas; handle `binary_features`; prepare MNIST-shaped rows | [dataframes-tfrecords](sub-skills/dataframes-tfrecords/SKILL.md) |
| Convert TensorFlow/Keras/Estimator examples to TensorFlowOnSpark; build `spark-submit` command plans for MNIST, ResNet, segmentation, serving, or batch inference | [examples-conversion](sub-skills/examples-conversion/SKILL.md) |

## Shared references and scripts

- [Repository provenance](references/repo-provenance.md) records the source commit, package version, evidence paths, and refresh baseline.
- [API map](references/api-map.md) shows which sub-skill owns each public module and workflow family.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install/import, Java/Spark, TensorFlow/PySpark, Hadoop jar, Python metadata, and GPU issues.
- [check_environment.py](scripts/check_environment.py) is a safe diagnostic helper; it does not start training, download datasets, mutate clusters, or allocate GPUs.

## Operating rules

- Do not run long training examples, TF Serving Docker containers, cloud installers, or dataset downloads unless the user explicitly asks and the runtime is suitable.
- Do not assume Spark local mode is equivalent to TensorFlowOnSpark's distributed executor behavior. For cluster semantics, prefer Spark Standalone, YARN, Kubernetes, or `local-cluster[...]` style tests that isolate executor processes.
- For `InputMode.SPARK`, the TensorFlow function must consume rows from `TFNode.DataFeed`; Spark actions are still required to trigger lazy RDD inference.
- For Spark ML Pipelines, the DataFrame API is Spark-fed (`InputMode.SPARK`); route TensorFlow-native file-reading workflows to `examples-conversion` or `cluster-lifecycle` instead.
- For TFRecords, keep records flat enough for Spark SQL types and supply `binary_features` for raw bytes.
- Treat GPU use as optional unless the user explicitly requires it. CPU can validate many workflows, but it does not prove CUDA allocation, driver compatibility, or GPU TensorFlow execution.

## Common validation signals

- `TFCluster.run(...)` returns a cluster object after every executor reserves a node.
- `cluster.train(...)`, `cluster.inference(...)`, and `cluster.shutdown(...)` finish without late worker exceptions.
- Spark ML `TFEstimator.fit(...)` writes the expected checkpoint or SavedModel artifact, and `TFModel.transform(...)` returns a DataFrame with the requested output columns.
- TFRecord conversion preserves simple scalar/array fields and treats string versus binary features as intended.
- Render-only helper scripts output reviewable commands/templates without running Spark, Docker, downloads, or destructive cleanup.
