---
name: examples-conversion
description: "Convert TensorFlow, Keras, Estimator, and tutorial examples into
  TensorFlowOnSpark spark-submit workflow plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# examples-conversion

Use this operating sub-skill when a user wants to convert or adapt an existing TensorFlow, Keras, Estimator, ResNet, segmentation, or MNIST tutorial into a TensorFlowOnSpark workflow that can be launched with `spark-submit`.

This sub-skill is a router and checklist. Put low-level API details in the owning sub-skills; use this sub-skill to decide the workflow shape, Spark command, deployment assumptions, and validation signals.

## Route by user intent

| User intent | Use this file |
|---|---|
| Decide how to wrap existing TensorFlow code for TensorFlowOnSpark | [references/conversion-patterns.md](references/conversion-patterns.md) |
| Build Keras or Estimator MNIST train, inference, pipeline, or streaming command plans | [references/mnist-workflows.md](references/mnist-workflows.md) |
| Plan SavedModel inspection, TF Serving, Spark batch inference, local standalone, or YARN deployment | [references/deployment-and-serving.md](references/deployment-and-serving.md) |
| Diagnose failed conversions, missing Spark/JVM/classpath, stalled jobs, input-mode mistakes, SavedModel issues, or serving hazards | [references/troubleshooting.md](references/troubleshooting.md) |
| Render a dry-run command plan from caller-supplied paths | [scripts/render_spark_submit_plan.py](scripts/render_spark_submit_plan.py) |

## Boundary and handoff rules

- For `TFCluster.run`, reservation, TensorBoard, executor count, GPU/resource, shutdown, or `TFParallel.run` internals, route to the cluster-lifecycle sub-skill.
- For `InputMode.SPARK` queue semantics, `TFNode.DataFeed`, one-output-per-input inference, `next_batch`, `batch_results`, `terminate`, or feed timeouts, route to the datafeed-inputmode sub-skill.
- For Spark ML `TFEstimator`, `TFModel`, input/output mappings, and DataFrame transform details, route to the spark-ml-pipelines sub-skill.
- For Spark DataFrame to TFRecord conversion, `dfutil`, TensorFlow Hadoop jar/classpath, and MNIST row reshaping utilities, route to the dataframes-tfrecords sub-skill.
- Treat downloads, Docker, host Spark installation, and EC2/cloud deployment scripts as reference-only. Do not execute them from this skill.

## Default conversion procedure

1. Identify whether the original TensorFlow program already reads its own data (`InputMode.TENSORFLOW`) or should consume a Spark RDD/DataFrame (`InputMode.SPARK`).
2. Wrap the TensorFlow entrypoint as `main_fun(args, ctx)` or `main_fun(argv, ctx)` and create a small Spark driver that calls `TFCluster.run`.
3. Render a `spark-submit` command with explicit `--master`, executor/core settings, application script path, cluster size, data/model/export paths, and optional `--py-files` or `--jars`.
4. Check that every worker can see the data path, model/export path, Python dependencies, and optional TensorFlow Hadoop jar.
5. Validate by observing cluster startup, TensorFlow workers connecting, output checkpoint/export directories appearing, and either predictions or SavedModel signatures matching the expected tensors.

## Safe helper usage

The bundled helper only prints a plan. It does not start Spark, run Docker, download data, remove files, or mutate the host.

```bash
python scripts/render_spark_submit_plan.py --help
```

Use caller-provided concrete paths whenever possible. If reusing shell variables in the printed plan, review quoting before running the rendered command manually.
