# MNIST Keras and Estimator workflow plans

Use this reference to adapt the repository's MNIST Keras and Estimator tutorials without depending on repository-local paths. Replace placeholders with the user's converted scripts, data locations, and output directories.

## Common variables

Use concrete values in production plans. These names are placeholders only.

```bash
SPARK_SUBMIT=<spark-submit-executable>
MASTER=<spark-master-or-yarn>
SPARK_WORKER_INSTANCES=<number-of-tensorflow-workers>
CORES_PER_WORKER=<cores-reserved-per-worker>
TOTAL_CORES=<SPARK_WORKER_INSTANCES-times-CORES_PER_WORKER>
MNIST_TF_SCRIPT=<converted-mnist-tensorflow-mode-script.py>
MNIST_SPARK_SCRIPT=<converted-mnist-spark-mode-script.py>
MNIST_PIPELINE_SCRIPT=<converted-mnist-pipeline-script.py>
MNIST_INFERENCE_SCRIPT=<converted-mnist-batch-inference-script.py>
MNIST_CSV_TRAIN=<executor-visible-mnist-csv-train-dir>
MNIST_CSV_TEST=<executor-visible-mnist-csv-test-dir>
MNIST_TFR_TEST=<executor-visible-mnist-tfrecord-test-dir>
MODEL_DIR=<executor-visible-checkpoint-dir>
EXPORT_DIR=<executor-visible-savedmodel-base-or-version-dir>
PREDICTIONS_DIR=<executor-visible-predictions-output-dir>
TFOS_HADOOP_JAR=<tensorflow-hadoop-jar-if-using-tfrecord-dataframes>
```

Do not include cleanup commands in generated plans. Prefer new output directories for each run, or ask the user to clean old artifacts explicitly outside the skill.

## Local standalone cluster assumptions

The repository examples start a Spark Standalone master and workers before running `spark-submit`. In a reusable skill, do not start or stop Spark automatically. Ask the user which cluster is already available and record:

- Spark master URL or `yarn`.
- Worker count and cores per worker.
- Whether workers are separate processes. TensorFlowOnSpark integration tests require a local Spark Standalone cluster or a real distributed cluster; Spark local thread mode is not equivalent.
- Whether all workers can import TensorFlow, TensorFlowOnSpark, PySpark, and any tutorial dependencies.
- Whether all data and output paths are visible from executors.

## Train MNIST via `InputMode.TENSORFLOW`

Use this when the Keras or Estimator script reads MNIST through TensorFlow-native APIs. The Keras tutorial uses TensorFlow Datasets; Estimator uses TensorFlow input functions. Each worker can load or cache data unless the code explicitly shards.

```bash
${SPARK_SUBMIT} \
  --master ${MASTER} \
  --conf spark.cores.max=${TOTAL_CORES} \
  --conf spark.task.cpus=${CORES_PER_WORKER} \
  ${MNIST_TF_SCRIPT} \
  --cluster_size ${SPARK_WORKER_INSTANCES} \
  --model_dir ${MODEL_DIR} \
  --export_dir ${EXPORT_DIR}
```

Expected application code shape:

- Spark driver calls `TFCluster.run(..., input_mode=TFCluster.InputMode.TENSORFLOW, master_node="chief", log_dir=args.model_dir)`.
- Keras worker builds `MultiWorkerMirroredStrategy`, trains a `tf.keras.Model`, and exports a SavedModel from the chief.
- Estimator worker trains an Estimator and exports a SavedModel with a serving input receiver.
- Driver calls `cluster.shutdown()` after `TFCluster.run`.

Validation signals:

- Spark starts the expected number of TensorFlow workers.
- Training logs show all workers joining before synchronous training begins.
- The checkpoint directory and SavedModel export directory are populated.
- `saved_model_cli show` reports the expected serving signature before inference.

## Train MNIST via `InputMode.SPARK`

Use this when Spark distributes MNIST rows. The repository pattern converts rows into `(image, label)` pairs where image is a 784-value vector and label is a scalar.

```bash
${SPARK_SUBMIT} \
  --master ${MASTER} \
  --conf spark.cores.max=${TOTAL_CORES} \
  --conf spark.task.cpus=${CORES_PER_WORKER} \
  ${MNIST_SPARK_SCRIPT} \
  --cluster_size ${SPARK_WORKER_INSTANCES} \
  --images_labels ${MNIST_CSV_TRAIN} \
  --model_dir ${MODEL_DIR} \
  --export_dir ${EXPORT_DIR}
```

Expected application code shape:

- Spark driver creates `images_labels = sc.textFile(path).map(parse)`.
- Driver calls `TFCluster.run(..., input_mode=TFCluster.InputMode.SPARK, master_node="chief")`.
- Driver feeds rows with `cluster.train(images_labels, args.epochs)` and then calls `cluster.shutdown()`.
- Worker `main_fun` creates `TFNode.DataFeed(ctx.mgr, False)`, reshapes each image to `(28, 28, 1)`, batches, trains, exports from chief, and calls `tf_feed.terminate()` after planned steps.

Important limitations:

- The MNIST Spark-fed training examples use a single input RDD. Validation/test data is not fed as a second RDD.
- Synchronous strategy workers must all have enough data. The repository Keras pattern uses a conservative per-worker step count to reduce uneven-partition stalls.
- Use the datafeed-inputmode sub-skill for exact queue behavior and inference output mapping.

Validation signals:

- Logs show Spark reading the expected input partitions.
- TensorFlow workers report consistent step progress.
- SavedModel export appears only after workers complete.
- No worker waits indefinitely for more input rows.

## Prepare MNIST row data

The repository includes a data setup utility that can create CSV and TFRecord outputs, but it may download datasets and uses Spark/Hadoop utilities. In this generated skill, treat data preparation as caller-managed.

When the user already has MNIST-like CSV rows, require this layout:

- One record per line.
- First field is the label.
- Remaining 784 fields are pixel values.
- Training and test directories are executor-visible directories containing part files.

When the user has TFRecords, route schema and TensorFlow Hadoop jar details to the dataframes-tfrecords sub-skill.

## SavedModel inspection after MNIST training

Ask the user for a versioned SavedModel directory or resolve it outside this skill. Then inspect and run a tiny example with explicit tensor names.

```bash
saved_model_cli show \
  --dir ${EXPORT_DIR} \
  --all

saved_model_cli run \
  --dir ${EXPORT_DIR} \
  --tag_set serve \
  --signature_def serving_default \
  --input_exp '<input_tensor_name>=[<one-prepared-example>]'
```

For the repository Keras and Estimator MNIST examples, the common input tensor name is `conv2d_input`; the common output tensor name in pipeline inference is `dense_1`. Always confirm names with `saved_model_cli show` because names can change when the model architecture changes.

## Spark batch inference from a SavedModel

Use this when a SavedModel already exists and each executor can independently load the model. The repository MNIST batch inference examples use `TFParallel.run`, shard TFRecord files across workers, load the SavedModel signature, and write one predictions part file per worker.

```bash
${SPARK_SUBMIT} \
  --master ${MASTER} \
  --conf spark.cores.max=${TOTAL_CORES} \
  --conf spark.task.cpus=${CORES_PER_WORKER} \
  ${MNIST_INFERENCE_SCRIPT} \
  --cluster_size ${SPARK_WORKER_INSTANCES} \
  --images_labels ${MNIST_TFR_TEST} \
  --export_dir ${EXPORT_DIR} \
  --output ${PREDICTIONS_DIR}
```

Checklist:

- `EXPORT_DIR` should point to the versioned SavedModel directory consumed by `tf.saved_model.load`.
- The model must fit in each executor's memory.
- Input files must be visible to executors.
- Output path should be new or intentionally overwrite-safe.
- Use cluster-lifecycle for `TFParallel.run` internals.

## Spark ML Pipeline training and inference

Use this when the user wants DataFrame-based `fit` and `transform` workflows. The repository examples support CSV and simple TFRecord inputs. Pipeline behavior belongs to the spark-ml-pipelines sub-skill; this section only captures launch shape.

### Pipeline train

```bash
${SPARK_SUBMIT} \
  --master ${MASTER} \
  --conf spark.cores.max=${TOTAL_CORES} \
  --conf spark.task.cpus=${CORES_PER_WORKER} \
  --conf spark.executorEnv.JAVA_HOME=${JAVA_HOME} \
  --jars ${TFOS_HADOOP_JAR} \
  ${MNIST_PIPELINE_SCRIPT} \
  --cluster_size ${SPARK_WORKER_INSTANCES} \
  --images_labels ${MNIST_CSV_TRAIN} \
  --format csv \
  --mode train \
  --model_dir ${MODEL_DIR} \
  --export_dir ${EXPORT_DIR}
```

### Pipeline inference

```bash
${SPARK_SUBMIT} \
  --master ${MASTER} \
  --conf spark.cores.max=${TOTAL_CORES} \
  --conf spark.task.cpus=${CORES_PER_WORKER} \
  --conf spark.executorEnv.JAVA_HOME=${JAVA_HOME} \
  --jars ${TFOS_HADOOP_JAR} \
  ${MNIST_PIPELINE_SCRIPT} \
  --cluster_size ${SPARK_WORKER_INSTANCES} \
  --images_labels ${MNIST_CSV_TEST} \
  --format csv \
  --mode inference \
  --export_dir ${EXPORT_DIR} \
  --output ${PREDICTIONS_DIR}
```

Switch `--format csv` to `--format tfr` only when the TensorFlow Hadoop jar and TFRecord schema assumptions are satisfied.

Validation signals:

- DataFrame preview shows `image` and `label` columns before training.
- Training creates model/export outputs.
- Inference creates a `prediction` column and writes prediction output.
- Tensor names in `setInputMapping` and `setOutputMapping` match the SavedModel signature.

## Estimator streaming training pattern

The Estimator tutorial includes a Spark Streaming variant of `InputMode.SPARK` training. Treat it as an advanced reference pattern because it runs continuously and has no final SavedModel export.

Use only when the user explicitly wants streaming:

- Confirm the stream source and staging directory are safe and executor-visible.
- Avoid rendering file copy, move, kill, or cleanup commands; ask the user to manage stream arrival and job termination explicitly.
- Plan a graceful stop through the reservation-control helper owned by cluster-lifecycle if the user wants controlled shutdown.
- Warn that ongoing streaming training is not equivalent to the static SavedModel-producing examples.

## Using the render helper

Example for a Spark-fed Keras or Estimator MNIST training plan:

```bash
python scripts/render_spark_submit_plan.py \
  --workflow mnist-spark-train \
  --spark-submit ${SPARK_SUBMIT} \
  --master ${MASTER} \
  --app-script ${MNIST_SPARK_SCRIPT} \
  --cluster-size ${SPARK_WORKER_INSTANCES} \
  --cores-per-worker ${CORES_PER_WORKER} \
  --images-labels ${MNIST_CSV_TRAIN} \
  --model-dir ${MODEL_DIR} \
  --export-dir ${EXPORT_DIR}
```
