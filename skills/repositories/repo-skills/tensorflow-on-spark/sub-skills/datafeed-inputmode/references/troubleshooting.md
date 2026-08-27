# Troubleshooting `InputMode.SPARK` DataFeed jobs

Use this guide for hangs, timeouts, output mismatches, streaming waits, and worker exceptions in TensorFlowOnSpark RDD/DStream data feeding.

## Quick triage

1. Confirm the cluster was started with `input_mode=TFCluster.InputMode.SPARK`.
2. Confirm the driver called the matching API:
   - Training: `cluster.train(train_rdd_or_dstream, ...)`
   - Inference: `result_rdd = cluster.inference(input_rdd, ...)` followed by a Spark action on `result_rdd`
3. Confirm the `map_fun(args, ctx)` creates `TFNode.DataFeed(ctx.mgr, ...)` and continuously calls `next_batch()` while work remains.
4. For inference, confirm every non-empty batch returns exactly one result per input row through `batch_results()`.
5. Call `cluster.shutdown(...)` after feeding; use `grace_secs` when post-feed export or evaluation can run after the last input batch.

## Symptoms and fixes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TFCluster.train() requires InputMode.SPARK` or `TFCluster.inference() requires InputMode.SPARK` | Cluster was started in `InputMode.TENSORFLOW` or default mode. | Restart the cluster with `input_mode=TFCluster.InputMode.SPARK`. Cluster lifecycle details belong to the `cluster-lifecycle` sub-skill. |
| `Unknown queue: input` or another queue name | `qname` does not exist in the cluster queue list, or driver/map_fun queue names differ. | Use default `qname='input'` unless you deliberately created a custom queue in `TFCluster.run(..., queues=[...])`. Keep `qname_in` and `qname` identical. |
| `Queue '<name>' not found on this node, check for exceptions on other nodes.` | The Spark feeder could not connect to the expected manager queue, often because another worker failed during startup. | Inspect the first `Exception in worker` traceback. Also check executor count and reservation/startup using the `cluster-lifecycle` sub-skill. |
| `Timeout while feeding partition` | Spark queued input rows but the TensorFlow worker did not consume them within `feed_timeout`. | Verify `map_fun` reached the `DataFeed` loop, is calling `next_batch()`, and is not blocked in model setup. Increase `feed_timeout` only after proving the worker is actively consuming but legitimately slow. |
| Static training appears to run too long | `num_epochs=0` uses the implementation fallback repeat count, or model step limits do not line up with RDD size/partitioning. | Pass an explicit `num_epochs`, set model `steps_per_epoch`/`max_steps`, and call `tf_feed.terminate()` when the training loop has intentionally completed. |
| Training finishes but Spark still scans many partitions | `terminate()` cannot cancel Spark's RDD operation; it marks queue state as terminating so later partitions are skipped/ignored. | Reduce planned input size, epoch count, or partition count. Treat `terminate()` as a cleanup/skip signal, not a job cancellation mechanism. |
| Inference action hangs after input has been consumed | `batch_results()` returned fewer rows than the partition input count, so Spark is waiting on the output queue. | For every non-empty `batch = next_batch(...)`, assert `len(results) == len(batch)` before calling `batch_results(results)`. Do not drop filtered rows silently; emit placeholders or filter input before inference. |
| Inference output rows are shifted or assigned to the wrong inputs | `batch_results()` returned extra rows, returned rows in a different order, or reused leftovers across partition boundaries. | Preserve input order within each batch. Clear per-batch buffers. Never emit more results than the current batch length. |
| Last inference batch is smaller than expected | `EndPartition` caused `next_batch()` to return a partial partition-ending batch. | Treat partial batches as normal. Run the model on `len(batch)` rows and return exactly that many results. |
| Loop spins on empty batches | Code ignores `should_stop()` or treats empty batches as model input. | Use `while not tf_feed.should_stop():` as the outer loop. If `len(batch) == 0`, `continue` for inference or `return`/`break` for a training generator, depending on your framework loop. |
| Worker exception surfaces during `cluster.inference(...).count()` or `cluster.shutdown()` | Background TensorFlow code put a traceback on the `error` queue. | Fix the first TensorFlow traceback. `feed_timeout` changes will not solve user-code exceptions. Use `shutdown(grace_secs=...)` if the exception occurs after the final input batch during export/evaluation. |
| Exception appears only after data feeding is complete | The TensorFlow worker raised during post-feed work, such as model export, evaluation, or cleanup. | Call `cluster.shutdown(grace_secs=N)` with enough time for expected chief cleanup, then inspect the propagated `Exception in worker` traceback. |
| Spark Streaming job times out before data arrives | Static-style `feed_timeout` is too short for streaming intervals or idle input directories. | Register `cluster.train(dstream, feed_timeout=...)`, start the `StreamingContext`, and use a long timeout such as hours for sparse streams. |
| Streaming synchronous training deadlocks or stalls with uneven batches | Synchronous all-reduce strategies require workers to advance together, but streaming data can arrive unevenly. | Prefer an asynchronous parameter-server-style strategy for irregular streaming input, or reshape the stream so each worker receives balanced data. |
| Mapped tensor input has swapped fields | `input_mapping` is sorted by source key before assigning tuple positions to tensor names. | Ensure row tuple order matches sorted mapping keys, or avoid low-level `input_mapping` and unpack raw rows yourself. Spark ML DataFrame mapping belongs to `spark-ml-pipelines`. |

## One-output-per-input inference guard

Add this guard before every `batch_results()` call:

```python
batch = tf_feed.next_batch(args.batch_size)
if len(batch) == 0:
    continue

results = run_prediction(batch)
if len(results) != len(batch):
    raise ValueError(
        "InputMode.SPARK inference requires one output per input; "
        "got {} results for {} inputs".format(len(results), len(batch))
    )
tf_feed.batch_results(results)
```

If the model naturally filters rows, filter the Spark input RDD before `cluster.inference()` or return explicit status rows for rejected inputs.

## Feed-timeout decision guide

Increase `feed_timeout` when:

- The TensorFlow worker is alive and repeatedly consuming input, but a model step legitimately takes longer than the default timeout.
- Streaming input is expected to arrive slowly.
- Large batches or heavyweight preprocessing make queue draining slow but observable.

Do not increase `feed_timeout` as the first fix when:

- `map_fun` fails before constructing `DataFeed`.
- The worker is blocked loading a model or waiting for unavailable external resources.
- Inference returns fewer output rows than input rows; output-queue waits are a different problem.
- The Spark cluster itself lacks enough executors or Python worker reuse for background mode; route to `cluster-lifecycle`.

## Safe shutdown patterns

Training with possible export:

```python
try:
    cluster.train(train_rdd, num_epochs=args.epochs, feed_timeout=args.feed_timeout)
finally:
    cluster.shutdown(grace_secs=args.shutdown_grace_secs)
```

Inference:

```python
try:
    result_rdd = cluster.inference(input_rdd, feed_timeout=args.feed_timeout)
    result_rdd.saveAsTextFile(args.output)
finally:
    cluster.shutdown()
```

Streaming:

```python
cluster.train(train_dstream, feed_timeout=args.feed_timeout)
ssc.start()
cluster.shutdown(ssc)
```

## Stop conditions

Stop and reroute instead of editing DataFeed code when:

- The user cannot start Spark executors, satisfy Java/Spark requirements, or reserve TensorFlow nodes: use `cluster-lifecycle`.
- The user is using Spark ML `TFEstimator`/`TFModel` APIs: use `spark-ml-pipelines`.
- The problem is TFRecord DataFrame load/save, schema inference, or Hadoop InputFormat classpath: use `dataframes-tfrecords`.
- The user wants independent SavedModel inference per executor without a TensorFlowOnSpark cluster: use the sub-skill that owns `TFParallel.run` and example conversion.
