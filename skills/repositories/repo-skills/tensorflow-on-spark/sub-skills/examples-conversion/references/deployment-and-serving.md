# Deployment, SavedModel, serving, and inference notes

This reference turns the repository tutorials into reusable deployment guidance without running Spark, Docker, downloads, package installers, or file deletion commands.

## Deployment modes

| Mode | Use when | Main requirements | Cautions |
|---|---|---|---|
| Local Spark Standalone | User is testing on one host with Spark master and worker daemons. | `SPARK_HOME`, Java, `spark-submit`, master URL, separate worker processes, TensorFlow dependencies on worker Python. | Spark local thread mode is not a sufficient substitute for TensorFlowOnSpark cluster behavior. |
| YARN or managed Spark | User runs on a cluster. | Executor-visible data/model paths, packaged Python dependencies, compatible TensorFlow and TensorFlowOnSpark on every executor, optional Hadoop jar. | Driver-local paths and first-use dataset downloads usually fail or overload workers. |
| SavedModel CLI | User wants to inspect or smoke-test a SavedModel. | Versioned SavedModel directory, tensor names, one prepared example. | Tensor names differ by model; inspect before running inference. |
| TF Serving | User wants online inference. | Authorized serving platform, mounted/exported model base, known model name, REST or gRPC client. | Docker and container lifecycle commands are reference-only and must be authorized by the user or platform owner. |
| Spark batch inference | User wants offline predictions across many files. | Versioned SavedModel, executor-visible input, output directory, model fits executor memory. | This is independent executor inference, not synchronized distributed training. |

## Local Spark Standalone planning

The repository setup scripts define the standard variables used by examples:

```bash
MASTER=<spark-master-url>
SPARK_WORKER_INSTANCES=<worker-process-count>
CORES_PER_WORKER=<cores-per-worker>
TOTAL_CORES=<worker-process-count-times-cores-per-worker>
```

A safe runtime plan should ask the user to provide an already running Spark cluster or to start/stop it outside this skill. Do not run local cluster lifecycle commands from the helper.

Required checks:

```bash
java -version
<spark-submit-executable> --version
python - <<'PY'
import tensorflow
import tensorflowonspark
import pyspark
print('imports-ok')
PY
```

Cluster assumptions to record:

- `spark.task.cpus` matches the cores reserved per TensorFlow worker task.
- `spark.cores.max` does not exceed the worker capacity the user intends to allocate.
- Worker Python has the same project code and dependencies as the driver.
- For TensorFlowOnSpark cluster tests and examples, worker tasks must run in separate processes.

## YARN planning

For YARN, render `--master yarn` or the site-specific master string and then add cluster-specific packaging outside this sub-skill's scope.

Ask for:

- Deploy mode (`client` or `cluster`) and how driver logs are collected.
- Distributed filesystem paths for training data, checkpoints, SavedModel exports, and prediction outputs.
- Python environment distribution method used by the site.
- Whether TensorFlow Datasets, tutorial datasets, or external model packages are pre-staged on workers.
- Whether the TensorFlow Hadoop jar is required for TFRecord DataFrame utilities.

YARN-specific cautions:

- Do not assume executor access to driver-local files.
- Do not rely on first-use downloads from every executor.
- When using TensorFlow-native input (`InputMode.TENSORFLOW`), use paths that TensorFlow workers can read directly.
- When using Spark-fed input (`InputMode.SPARK`), make Spark input partitions visible and balanced enough for synchronous training.

## SavedModel CLI workflow

Use SavedModel CLI after training and before serving or batch inference.

1. Ask for a versioned SavedModel directory. Do not infer it by listing directories inside this skill.
2. Inspect signatures:

```bash
saved_model_cli show \
  --dir <versioned-savedmodel-dir> \
  --all
```

3. Run a tiny example with explicit tensor names:

```bash
saved_model_cli run \
  --dir <versioned-savedmodel-dir> \
  --tag_set serve \
  --signature_def serving_default \
  --input_exp '<input_tensor_name>=[<prepared-example>]'
```

Repository MNIST examples commonly use `conv2d_input` as the input tensor and `dense_1` as an output tensor in pipeline inference, but always confirm with `saved_model_cli show`.

## TF Serving workflow

TF Serving is useful for online inference from a SavedModel. This skill may describe the plan but must not run Docker or service lifecycle commands.

Collect from the user:

- Model base directory containing one or more numeric SavedModel version subdirectories.
- Model name exposed by the serving system.
- Serving base URL or gRPC endpoint.
- Input tensor name and one prepared request example.
- Authorization to start, stop, or update serving infrastructure if any service operation is requested.

Safe request-shape example:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"instances": [{"<input_tensor_name>": <prepared-example>}]} ' \
  ${TF_SERVING_BASE_URL}/v1/models/${MODEL_NAME}:predict
```

Safety rules:

- Do not run broad container-stop commands. If the user explicitly authorizes container operations, target a named container or platform-managed service.
- Do not pull images or start containers without explicit authorization and environment review.
- Do not assume the model base path is safe to mount into a container; confirm permissions and secrets exposure.
- If the user only wants conversion guidance, stop at the request shape and validation checklist.

Validation signals:

- Model status reports an available version.
- Metadata exposes the expected signature.
- Prediction response contains expected output tensor keys and shapes.

## Spark batch inference workflow

The repository MNIST batch inference example loads a SavedModel independently on each executor and shards input files by worker index.

Use this when:

- Training code is unavailable or not needed for inference.
- Each executor can load the SavedModel in memory.
- Input files can be sharded by worker.
- Output can be written as one or more part files.

Command shape:

```bash
<spark-submit> \
  --master <spark-master-or-yarn> \
  --conf spark.cores.max=<total-cores> \
  --conf spark.task.cpus=<cores-per-worker> \
  <batch-inference-script.py> \
  --cluster_size <worker-count> \
  --images_labels <executor-visible-input-dir> \
  --export_dir <versioned-savedmodel-dir> \
  --output <new-predictions-output-dir>
```

Expected code shape:

- Spark driver calls `TFParallel.run(sc, inference_fn, args, args.cluster_size)`.
- Each executor loads `tf.saved_model.load(args.export_dir, tags='serve')`.
- Each executor shards input by worker number.
- Each executor writes its own output part file.

Validation signals:

- Each executor logs a model load.
- Output part count is consistent with workers that received data.
- Prediction records include labels or identifiers needed for downstream evaluation.

## Install, Docker, and EC2 material

The repository includes host-level Spark installation and cloud-oriented scripts. Treat them as evidence of required components only:

- Java/JDK.
- Spark distribution and `SPARK_HOME`.
- Spark Standalone master and worker daemons for local integration tests.
- TensorFlow Hadoop jar for TFRecord DataFrame utilities.
- Optional cloud provisioning steps outside this skill's safety boundary.

Do not run package managers, network downloads, cloud provisioning scripts, Docker pulls, Docker runs, broad container stops, or destructive cleanup from this sub-skill or its helper.
