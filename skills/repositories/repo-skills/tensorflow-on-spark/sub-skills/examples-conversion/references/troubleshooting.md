# Troubleshooting example conversions and spark-submit workflows

Use this reference when a converted TensorFlowOnSpark example fails to launch, stalls, writes no model, or produces invalid serving/inference results.

## Fast triage checklist

Ask for these facts first:

- Workflow type: `InputMode.TENSORFLOW`, `InputMode.SPARK`, Spark ML pipeline, SavedModel CLI, TF Serving, or Spark batch inference.
- Spark master/deploy mode and executor count.
- `spark.task.cpus`, total cores, and cluster size passed to the application.
- Whether workers are separate processes.
- Data path, output path, and whether executors can see them.
- Application script path, extra Python dependencies, `--py-files`, and optional `--jars`.
- First error line from driver logs and one worker log.

## Symptom table

| Symptom | Likely cause | Recovery steps | Stop condition |
|---|---|---|---|
| `spark-submit` command not found | Spark is not installed or executable path is wrong. | Ask for the site Spark executable path; run `<spark-submit> --version`; update the rendered plan. | Stop if no authorized Spark runtime exists. |
| Java error or `JAVA_HOME` missing | Spark requires a compatible JVM. | Ask the user to provide Java/JDK; confirm `java -version`; for pipeline jobs, pass executor Java env if required. | Stop if installing Java would require host mutation not authorized by the user. |
| Job works in Spark local mode but TensorFlowOnSpark cluster hangs | Executors are local threads, not separate worker processes. | Use Spark Standalone or a real distributed cluster; match worker instances to cluster size. | Stop if the user cannot provide separate worker processes. |
| Reservations or TensorFlow workers time out | Executor count, task CPUs, or cluster size does not allow all TF nodes to start. | Check `spark.cores.max`, `spark.task.cpus`, worker instances, dynamic allocation, and requested `cluster_size`/`num_ps`; route internals to cluster-lifecycle. | Stop if the cluster cannot allocate the requested nodes. |
| `InputMode.TENSORFLOW` job never reads Spark data | Wrong input-mode expectation. | Explain that TensorFlow reads data directly in this mode; use `InputMode.SPARK` only when Spark should feed rows. | Stop if the user's data is only an RDD and no Spark-fed worker code exists. |
| `InputMode.SPARK` job has no validation data | Single-RDD design of the example. | Use one training RDD; validate after export, or design a custom multi-phase job. | Stop if the user requires simultaneous separate train/validation feeds without code changes. |
| Synchronous Keras training stalls near end of Spark-fed epoch | Uneven RDD partitions or a worker ran out of rows. | Reduce planned steps per worker, balance partitions, increase data, and call data-feed termination when done; route feed details to datafeed-inputmode. | Stop if worker logs show a persistent data-feed timeout with no available rows. |
| Pipeline job rejects `InputMode.TENSORFLOW` | Spark ML pipeline API is DataFrame/Spark-fed. | Use Spark ML `TFEstimator`/`TFModel` with input mappings, or switch to a raw `TFCluster.run` TensorFlow-mode script. | Stop if the user requires TensorFlow-native data reads inside Spark ML `TFEstimator`. |
| TFRecord DataFrame job cannot find Hadoop input format class | TensorFlow Hadoop jar missing from Spark classpath. | Add the jar with `--jars` or site classpath; route schema/classpath details to dataframes-tfrecords. | Stop if the jar is unavailable and TFRecord DataFrame utilities are required. |
| SavedModel directory exists but `saved_model_cli` shows no expected signature | Wrong path, version base instead of versioned directory, or model exported with different signature. | Ask for the versioned SavedModel directory; run `saved_model_cli show --all`; update tensor names and signature key. | Stop if no SavedModel signatures exist for serving/inference. |
| SavedModel inference says input tensor not found | Tensor name changed from the tutorial model. | Inspect signatures; replace `conv2d_input` or other tutorial names with actual input names. | Stop if the user cannot provide a sample matching the signature. |
| Batch inference executor OOM | Each executor loads its own SavedModel. | Reduce model size, increase executor memory, reduce concurrent workers, or use a serving architecture. | Stop if model cannot fit in executor memory. |
| ResNet conversion import error for model modules | TensorFlow model dependency not packaged for executors. | Use `--py-files`, installed packages, or cluster image packaging; confirm imports on workers. | Stop if third-party model code or data cannot be made available. |
| Segmentation example fails while loading tutorial dataset | Dataset package/version/cache issue or unauthorized first-use download. | Pre-stage dataset/cache, verify TensorFlow Datasets compatibility, or switch to caller-provided data. | Stop if dataset acquisition requires unauthorized network access. |
| TF Serving request fails | Serving model name, URL, signature, or request shape mismatch. | Check serving metadata, model version status, tensor names, JSON shape, and service logs. | Stop before Docker/service lifecycle changes unless explicitly authorized. |

## Command rendering mistakes

The helper prints commands but does not execute them. If a rendered command is wrong:

1. Re-run the helper with explicit concrete paths rather than shell variables.
2. Check whether the chosen workflow expects `--images_labels`, `--model_dir`, `--export_dir`, `--output`, `--jars`, or `--py-files`.
3. Confirm `--cluster_size` equals the number of TensorFlow worker nodes, not necessarily every Spark executor in a larger cluster.
4. For ResNet-style wrappers, separate TensorFlowOnSpark driver flags from remaining TensorFlow model flags.
5. For pipeline jobs, provide `--mode train` or `--mode inference` and the correct input format.

## Input-mode mismatch diagnostics

Ask the user what code reads data:

- If TensorFlow code uses `tf.data.Dataset`, TensorFlow Datasets, HDFS paths, or a custom file reader, start with `InputMode.TENSORFLOW`.
- If Spark code creates an RDD and the worker uses `TFNode.DataFeed`, use `InputMode.SPARK`.
- If Spark code creates a DataFrame and uses `TFEstimator` or `TFModel`, use Spark ML pipeline workflow.
- If no training code is needed and a SavedModel exists, use Spark batch inference with `TFParallel.run` or use a serving system.

Common correction:

```text
Do not add `--images_labels` to a TensorFlow-native script unless that script actually reads it. Do not expect Spark rows to reach a TensorFlow-native `tf.data` pipeline. Conversely, do not call `cluster.train(rdd, ...)` unless the worker function creates and consumes `TFNode.DataFeed`.
```

## Output path and cleanup issues

The repository tutorials remove old artifacts before examples. This sub-skill does not render destructive cleanup commands. Safer alternatives:

- Use a fresh checkpoint directory for every training run.
- Use a fresh SavedModel export base or versioned directory.
- Use a fresh predictions output directory for every batch inference run.
- Ask the user to explicitly clean or archive old outputs outside the skill if needed.

## Validation commands

Use read-only or non-destructive checks:

```bash
<spark-submit-executable> --version
java -version
python - <<'PY'
import tensorflow
import tensorflowonspark
import pyspark
print('imports-ok')
PY
saved_model_cli show --dir <versioned-savedmodel-dir> --all
```

For outputs, prefer listing or metadata inspection over deletion or overwrite.

## When to route elsewhere

- Reservation, shutdown, TensorBoard, GPU allocation, executor lifecycle: cluster-lifecycle.
- DataFeed batching, early termination, one-output-per-input inference: datafeed-inputmode.
- Spark ML parameter mappings, `TFEstimator`, `TFModel`, DataFrame transforms: spark-ml-pipelines.
- TFRecord schemas, binary/string hints, TensorFlow Hadoop jar mechanics: dataframes-tfrecords.
