# Conversion patterns for TensorFlowOnSpark examples

This reference distills the repository examples into reusable conversion patterns. It is self-contained: replace every placeholder path with paths from the user's project or cluster.

## Evidence basis

The patterns are backed by the repository overview, MNIST Keras and Estimator tutorials, ResNet conversion tutorial and wrapper scripts, segmentation tutorial and wrapper script, Spark setup scripts, and the test documentation that requires Spark Standalone or a real distributed cluster rather than Spark local threads.

## First decision: data owner

Choose the input mode before writing commands.

| Data owner | TensorFlowOnSpark input mode | Use when | Command implication |
|---|---|---|---|
| TensorFlow code reads files directly | `InputMode.TENSORFLOW` | Existing TF/Keras/Estimator code already uses `tf.data`, TensorFlow Datasets, HDFS/object-store paths, or its own file readers. ResNet and segmentation examples use this mode. | Launch `TFCluster.run(..., input_mode=TFCluster.InputMode.TENSORFLOW, ...)`, then call `cluster.shutdown()`. No Spark RDD is fed. |
| Spark distributes rows to TensorFlow workers | `InputMode.SPARK` | The input is an RDD or DataFrame-derived row stream, such as MNIST CSV rows converted into `(image, label)` tuples. | Launch `TFCluster.run(..., input_mode=TFCluster.InputMode.SPARK, ...)`, then call `cluster.train(rdd, epochs)` or `cluster.inference(rdd)`, then `cluster.shutdown()`. |
| Spark ML pipeline owns rows | Spark ML `TFEstimator` or `TFModel` | The user wants a DataFrame `fit`/`transform` workflow. | Use the spark-ml-pipelines sub-skill; the DataFrame API supports Spark-fed data, not `InputMode.TENSORFLOW`. |
| Independent executor inference | `TFParallel.run` | A SavedModel already exists and every executor can independently load it for batch inference. | Use a Spark driver that calls `TFParallel.run(sc, inference_fn, args, cluster_size)`; route internals to cluster-lifecycle. |

## Minimal code changes for existing TensorFlow programs

### `InputMode.TENSORFLOW` wrapper

Use this pattern when the original program already reads its own data. TensorFlowOnSpark provides the distributed cluster metadata and usually sets the distributed environment expected by `MultiWorkerMirroredStrategy` or TF_CONFIG-aware code.

```python
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from tensorflowonspark import TFCluster


def main_fun(args, ctx):
    # Existing TensorFlow/Keras/Estimator logic goes here.
    # Create the distributed strategy inside the executor function.
    # Export/checkpoint only from the chief when the model API requires it.
    pass


sc = SparkContext(conf=SparkConf().setAppName("converted_tensorflow_job"))
cluster = TFCluster.run(
    sc,
    main_fun,
    args,
    args.cluster_size,
    num_ps=0,
    tensorboard=args.tensorboard,
    input_mode=TFCluster.InputMode.TENSORFLOW,
    master_node="chief",
    log_dir=args.model_dir,
)
cluster.shutdown()
```

Conversion notes:

- Parse TensorFlowOnSpark-specific arguments in the Spark driver, especially `--cluster_size`, `--model_dir`, `--export_dir`, `--tensorboard`, and any data paths.
- Create TensorFlow distribution strategies inside `main_fun`, not in the Spark driver.
- Ensure every executor can read data paths and write output paths. For YARN or multi-host clusters, local driver-only paths are not sufficient.
- For TF2 Keras examples, save or export from the chief when the API is not multi-worker-safe.
- For synchronous strategies, all workers must start and remain connected; a slow or missing worker prevents training from beginning.

### `InputMode.SPARK` wrapper

Use this pattern when Spark should feed input rows to TensorFlow.

```python
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from tensorflowonspark import TFCluster


def parse_row(line):
    values = [int(x) for x in line.split(",")]
    return values[1:], values[0]


def main_fun(args, ctx):
    from tensorflowonspark import TFNode

    feed = TFNode.DataFeed(ctx.mgr, False)
    # Convert batches from feed.next_batch(...) into the tensor shapes expected
    # by the model. Terminate the feed when training has reached its planned
    # steps so Spark can ignore remaining queued rows.
    pass


sc = SparkContext(conf=SparkConf().setAppName("converted_spark_feed_job"))
input_rdd = sc.textFile(args.images_labels).map(parse_row)
cluster = TFCluster.run(
    sc,
    main_fun,
    args,
    args.cluster_size,
    num_ps=0,
    tensorboard=args.tensorboard,
    input_mode=TFCluster.InputMode.SPARK,
    master_node="chief",
)
cluster.train(input_rdd, args.epochs)
cluster.shutdown()
```

Conversion notes:

- Spark-fed training examples use a single input RDD; separate validation/test RDDs are not fed by the MNIST `InputMode.SPARK` training pattern.
- The TensorFlow executor function must reshape and type-cast Spark rows into the model's tensor shapes.
- Synchronous Keras strategies can stall if partition sizes are uneven. The repository MNIST Keras pattern trains for a conservative fraction of the expected per-worker steps and then calls `terminate()` on the data feed.
- Use the datafeed-inputmode sub-skill for exact feed semantics, batching, and inference output contracts.

## Keras MNIST conversion pattern

Keras MNIST examples share these choices:

- `main_fun(args, ctx)` builds a `MultiWorkerMirroredStrategy` inside the executor.
- `--cluster_size` defaults from Spark executor instances when available.
- `InputMode.TENSORFLOW` uses TensorFlow Datasets and auto-sharding options; each worker may otherwise attempt to load or cache data.
- `InputMode.SPARK` parses Spark CSV rows into `(image, label)`, reshapes image vectors to `(28, 28, 1)`, batches records, and trains from a generator backed by `TFNode.DataFeed`.
- Export uses a SavedModel directory after training; validation should inspect the SavedModel signature before serving or batch inference.

Use Keras pattern when the user has a `tf.keras.Model` with `model.fit`, callbacks, and SavedModel export.

## Estimator MNIST conversion pattern

Estimator MNIST examples mirror the Keras launch shapes but use Estimator training/export APIs:

- `main_fun(args, ctx)` creates or configures an Estimator inside the worker.
- `InputMode.TENSORFLOW` can use TensorFlow-native input functions and export a SavedModel with a serving input receiver.
- `InputMode.SPARK` uses `TFNode.DataFeed` to produce examples for an Estimator input function.
- Streaming Estimator training replaces a static RDD with a DStream-like feed and has no final SavedModel export because training is ongoing.

Use Estimator pattern when the user already has `tf.estimator.Estimator`, input receiver functions, or TF1/TF2 compatibility code.

## ResNet conversion pattern

The repository ResNet tutorial demonstrates how to convert an existing distributed TensorFlow application that already understands `TF_CONFIG` or distribution strategies.

Recommended structure:

1. Keep most model code in a TensorFlow-only module.
2. Rename or wrap the original `main(_)` as `main_fun(argv, ctx)`.
3. Keep framework-specific flag parsing in the TensorFlow module; for absl-style flags, pass remaining arguments from the Spark driver to `main_fun`.
4. Create a small Spark driver that parses only TensorFlowOnSpark arguments, then calls:

```python
cluster = TFCluster.run(
    sc,
    resnet_main_fun,
    remaining_tensorflow_args,
    args.cluster_size,
    args.num_ps,
    args.tensorboard,
    TFCluster.InputMode.TENSORFLOW,
    master_node="chief",
)
cluster.shutdown()
```

5. Use `spark-submit --py-files` or another packaging mechanism so executors can import the TensorFlow-only module and third-party model dependencies.

Operational cautions:

- Confirm the original single-node program works before Spark conversion.
- Confirm the original program works in a manually distributed TensorFlow configuration before adding Spark when feasible.
- Make the dataset visible to executors through a distributed filesystem or per-node installation.
- Treat external model repositories and dataset downloads as caller-managed prerequisites, not actions performed by this skill.

## Segmentation tutorial conversion pattern

The segmentation example demonstrates a notebook-to-production path:

1. Remove interactive display and notebook-only code.
2. Create a single-node Python training script and confirm it writes model artifacts.
3. Add `MultiWorkerMirroredStrategy` and confirm a manual distributed TensorFlow run can connect all workers.
4. Wrap the distributed code in `main_fun(args, ctx)` and launch it with `TFCluster.run(..., InputMode.TENSORFLOW, master_node="chief")`.
5. Use `cluster.shutdown(grace_secs=30)` when workers need a short grace period after saving.

Operational cautions:

- TensorFlow Datasets or tutorial datasets may download on first use; pre-stage data and caches when running on managed clusters.
- Synchronous training does not automatically adjust global batch size or shard data; check batch-size and sharding choices for the target cluster.
- Export formats can include checkpoints, HDF5 files, and SavedModel directories; require the user to specify which one downstream inference should consume.

## Spark-submit skeleton

Render exact commands with [../scripts/render_spark_submit_plan.py](../scripts/render_spark_submit_plan.py) or build this shape manually:

```bash
<spark-submit> \
  --master <spark-master-or-yarn> \
  --conf spark.cores.max=<total-cores> \
  --conf spark.task.cpus=<cores-per-worker> \
  [--py-files <dependency-archive-or-python-file>] \
  [--jars <tensorflow-hadoop-jar>] \
  <converted-application.py> \
  --cluster_size <number-of-tensorflow-nodes> \
  --model_dir <checkpoint-output> \
  --export_dir <savedmodel-output> \
  [additional application arguments]
```

Before running, verify:

- Spark workers are separate processes, not only local threads.
- Every executor can import the converted code and all TensorFlow dependencies.
- Data and output paths are visible from executors.
- `spark.task.cpus` and cluster size match the intended one TensorFlow process per executor/task layout.
- Existing outputs will not be overwritten unexpectedly; prefer a new output path for each trial.
