# DataFeed patterns for `InputMode.SPARK`

This reference covers the TensorFlowOnSpark path where Spark feeds RDD or DStream records into a TensorFlow worker through `TFNode.DataFeed`. It is based on the package APIs and the maintained MNIST/test patterns for RDD feeding, inference, early termination, streaming, and exception handling.

## Mental model

`InputMode.SPARK` has two cooperating parts:

1. The Spark driver starts the TensorFlowOnSpark cluster with `TFCluster.run(..., input_mode=TFCluster.InputMode.SPARK, ...)`.
2. Spark partition tasks push input rows into a per-executor manager queue while the user's TensorFlow `map_fun(args, ctx)` runs in the background and consumes those rows through `TFNode.DataFeed(ctx.mgr, ...)`.

The Spark partition task waits for queued input to be consumed. `feed_timeout` is the timeout for that wait; it is not a TensorFlow op timeout and it does not limit `next_batch()` itself.

Default queues are:

- `input`: Spark input rows are pushed here and `DataFeed.next_batch()` consumes them.
- `output`: inference results are pushed here by `DataFeed.batch_results()` and read back into the output RDD.
- `error`: background TensorFlow exceptions are reported here and re-raised by Spark feeder/shutdown tasks.

## Driver pattern: RDD training

Use this when Spark owns the training data and TensorFlow consumes it from a generator or loop.

```python
from tensorflowonspark import TFCluster

cluster = TFCluster.run(
    sc,
    main_fun,
    args,
    num_executors=args.cluster_size,
    num_ps=0,
    input_mode=TFCluster.InputMode.SPARK,
    master_node="chief",
)
try:
    # num_epochs=0 defaults to a large fallback repeat count in the implementation;
    # pass an explicit value when the model has a known step/epoch target.
    cluster.train(train_rdd, num_epochs=args.epochs, feed_timeout=args.feed_timeout)
finally:
    # Use grace_secs when the chief may export a model or raise a late exception
    # after Spark has finished feeding the data.
    cluster.shutdown(grace_secs=getattr(args, "shutdown_grace_secs", 0))
```

Training feed notes:

- `cluster.train()` requires `InputMode.SPARK` and asserts that `num_epochs >= 0`.
- For non-streaming RDDs, TensorFlowOnSpark repeats the RDD by unioning it `num_epochs` times. If `num_epochs` is omitted or `0`, the implementation uses `10` as a fallback repeat count.
- For DStreams, `cluster.train()` registers a `foreachRDD(... foreachPartition(...))` feeder instead of unioning static RDDs.
- Spark generally processes the full RDD operation. If the model reaches its target early, call `tf_feed.terminate()` from the TensorFlow side so later partitions are ignored rather than queued.

## `map_fun` pattern: training generator with early stop

```python
def main_fun(args, ctx):
    import numpy as np
    import tensorflow as tf
    from tensorflowonspark import TFNode

    tf_feed = TFNode.DataFeed(ctx.mgr)  # training mode is the default

    def rdd_generator():
        while not tf_feed.should_stop():
            batch = tf_feed.next_batch(args.batch_size)
            if len(batch) == 0:
                return

            # Example row contract: each Spark row is (features, label).
            features = []
            labels = []
            for row in batch:
                image, label = row
                features.append(np.asarray(image, dtype=np.float32) / 255.0)
                labels.append(label)
            yield np.asarray(features), np.asarray(labels)

    dataset = tf.data.Dataset.from_generator(
        rdd_generator,
        output_types=(tf.float32, tf.int64),
    )

    try:
        # Replace with model.fit(...), Estimator training, or a custom loop.
        train_model(dataset, args)
    finally:
        # Call this only when the TensorFlow training loop is intentionally done.
        # It sets the manager state to terminating and drains queued input, allowing
        # Spark feeder tasks to skip later partitions. It does not cancel Spark jobs.
        tf_feed.terminate()
```

Practical training guidance:

- Keep the generator tolerant of partial final batches; `next_batch()` may return fewer than `batch_size` rows.
- If using synchronous multi-worker training, make step limits conservative enough that workers do not run out of Spark-fed data at different times. The maintained examples stop below the theoretical full-step count to avoid uneven partition deadlocks.
- For Estimator hooks or custom callbacks that finish before the RDD is consumed, call `terminate()` from the hook/callback. If a framework hook can leave a pending `next_batch()` call blocked, use the same hook to perform a small follow-up `next_batch(1)` only when needed to release local feed state.

## Driver pattern: one-output-per-input inference

`cluster.inference()` returns a lazy output RDD. The data is not fed until a Spark action runs.

```python
from tensorflowonspark import TFCluster

cluster = TFCluster.run(
    sc,
    main_fun,
    args,
    num_executors=args.cluster_size,
    num_ps=0,
    input_mode=TFCluster.InputMode.SPARK,
    master_node="chief",
)
try:
    result_rdd = cluster.inference(input_rdd, feed_timeout=args.feed_timeout)
    # Any action is valid: collect(), count(), saveAsTextFile(), write through a DataFrame, etc.
    result_rows = result_rdd.collect()
finally:
    cluster.shutdown()
```

Inference feed notes:

- Each Spark partition is queued to the worker, then TensorFlowOnSpark sends an internal `EndPartition` marker.
- After all input rows in that partition are consumed, Spark reads exactly one output item for every input item in the partition.
- If `batch_results()` returns fewer items than the input count, Spark can hang waiting for missing output. If it returns extra items, later partitions can receive misaligned results.

## `map_fun` pattern: one-output-per-input inference

```python
def main_fun(args, ctx):
    import numpy as np
    import tensorflow as tf
    from tensorflowonspark import TFNode

    model = load_or_build_model(args)
    tf_feed = TFNode.DataFeed(ctx.mgr, train_mode=False)

    while not tf_feed.should_stop():
        batch = tf_feed.next_batch(args.batch_size)
        if len(batch) == 0:
            # This can occur around partition boundaries or final shutdown.
            # The while condition will exit once end-of-feed has been observed.
            continue

        # next_batch() may return a partial batch at EndPartition.
        features = np.asarray([row[0] if isinstance(row, (tuple, list)) else row for row in batch])
        predictions = model(features, training=False)
        result_rows = to_python_rows(predictions)

        if len(result_rows) != len(batch):
            raise ValueError(
                "InputMode.SPARK inference requires one output per input: "
                "got {} results for {} input rows".format(len(result_rows), len(batch))
            )
        tf_feed.batch_results(result_rows)
```

Inference validation checklist:

- The output array passed to `batch_results()` has `len(results) == len(batch)` for every non-empty batch.
- The output rows are serializable by Spark.
- The model code handles partial batches; do not assume `len(batch) == batch_size`.
- The driver calls a Spark action on the returned RDD before `cluster.shutdown()`.

## `EndPartition` behavior

`EndPartition` is an internal marker inserted by the Spark-side inference feeder at the end of each input partition. User code should not enqueue it manually.

Observed `DataFeed.next_batch()` behavior:

- It blocks until it can read input, an end marker, or a shutdown marker from the input queue.
- It calls `task_done()` on every consumed queue item.
- It may return fewer than `batch_size` rows at a partition boundary.
- In inference mode (`train_mode=False`), when it has already collected rows and then sees `EndPartition`, it returns the partial batch so the user can produce outputs for that partition.
- Shutdown sends `None`; when `next_batch()` consumes it, `should_stop()` becomes true.

## Mapped input tensors

Most raw RDD `DataFeed` code omits `input_mapping`, so `next_batch()` returns a Python list of input rows. If each Spark row contains multiple tensors, unpack those rows explicitly.

When `DataFeed(..., input_mapping=mapping)` is used, `next_batch()` returns a dictionary:

```python
input_mapping = {
    "features_col": "serving_default_features:0",
    "weight_col": "serving_default_weights:0",
}
tf_feed = TFNode.DataFeed(ctx.mgr, train_mode=False, input_mapping=input_mapping)
batch = tf_feed.next_batch(args.batch_size)
features = batch["serving_default_features:0"]
weights = batch["serving_default_weights:0"]
```

Mapping rules:

- Mapping keys are source column/field names; mapping values are TensorFlow tensor names.
- TensorFlowOnSpark sorts the mapping by source key before assigning row positions to tensor names.
- If you use this low-level path with an RDD tuple, make the tuple order match the sorted source keys.
- Full Spark ML DataFrame estimator/model mapping belongs to the `spark-ml-pipelines` sub-skill.

## Spark Streaming pattern

Spark Streaming feeds DStream RDDs into the same queue system. Because data may arrive slowly, use a longer `feed_timeout` than for a static RDD.

```python
from pyspark.streaming import StreamingContext
from tensorflowonspark import TFCluster

ssc = StreamingContext(sc, args.batch_interval_secs)
stream = ssc.textFileStream(args.input_dir)
train_dstream = stream.map(parse_row)

cluster = TFCluster.run(
    sc,
    main_fun,
    args,
    num_executors=args.cluster_size,
    num_ps=1,
    input_mode=TFCluster.InputMode.SPARK,
    log_dir=args.model_dir,
    master_node="chief",
)
cluster.train(train_dstream, feed_timeout=args.feed_timeout)  # e.g. 86400 for slow arrivals
ssc.start()
cluster.shutdown(ssc)
```

Streaming guidance:

- Register `cluster.train(dstream, ...)` before `ssc.start()`.
- Use `cluster.shutdown(ssc)` so TensorFlowOnSpark can wait for streaming termination or stop the streaming context when the cluster server is done.
- Prefer an asynchronous training strategy for irregular streaming input; synchronous all-reduce can deadlock if workers receive uneven data.
- `terminate()` remains the TensorFlow-side early-stop signal when the model has completed.
