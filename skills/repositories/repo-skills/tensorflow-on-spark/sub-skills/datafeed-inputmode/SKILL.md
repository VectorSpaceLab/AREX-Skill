---
name: datafeed-inputmode
description: "InputMode.SPARK data feeding, inference, and DataFeed queue
  semantics for TensorFlowOnSpark map_fun code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datafeed-inputmode

Use this sub-skill when the user is writing or debugging TensorFlowOnSpark `InputMode.SPARK` code where Spark RDD or DStream rows are fed into a TensorFlow `map_fun(args, ctx)` through `TFNode.DataFeed`.

## Owns

- `TFCluster.train(dataRDD, num_epochs=..., feed_timeout=..., qname='input')` data feeding for Spark RDDs and DStreams.
- `TFCluster.inference(dataRDD, feed_timeout=..., qname='input')` and its lazy output RDD.
- `TFNode.DataFeed(ctx.mgr, ...)` inside user `map_fun` code:
  - `next_batch(batch_size)`
  - `should_stop()`
  - `batch_results(results)`
  - `terminate()`
- Queue semantics for `EndPartition`, end-of-feed `None`, default `input`/`output`/`error` queues, `feed_timeout`, and worker exception propagation.
- Safe patterns for one-output-per-input inference, mapped input tensors, early termination, and Spark Streaming feed waits.

## Route elsewhere

- Spark ML `TFEstimator` / `TFModel` DataFrame workflows: use the `spark-ml-pipelines` sub-skill.
- DataFrame to TFRecord conversion, TFRecord schemas, and Hadoop TFRecord jar setup: use the `dataframes-tfrecords` sub-skill.
- Cluster construction, Spark executor sizing, reservations, TensorBoard, TF_CONFIG, GPU allocation, or independent `TFParallel.run`: use the `cluster-lifecycle` sub-skill.

## Operating path

1. Confirm the cluster was started with `input_mode=TFCluster.InputMode.SPARK`.
2. Decide whether the Spark data is used for training or inference:
   - Training: create `TFNode.DataFeed(ctx.mgr)` in `map_fun`, consume `next_batch()`, and call `cluster.train(...)` on the driver.
   - Inference: create `TFNode.DataFeed(ctx.mgr, train_mode=False)`, return exactly one result for every input row via `batch_results()`, and call a Spark action on the RDD returned by `cluster.inference(...)`.
3. Size `num_epochs`, partition count, and training step limits so each worker gets enough data but does not leave excessive trailing partitions.
4. Set `feed_timeout` for how long Spark feeder tasks should wait for the TensorFlow worker to consume queued input; use longer values for streaming or slow model steps only after verifying the worker is actively calling `next_batch()`.
5. Always call `cluster.shutdown(...)` after `cluster.train(...)` or after the inference output RDD action completes. Use `grace_secs` if the TensorFlow code may export or raise a late exception after data feeding.

## References and helper

- [DataFeed patterns](references/datafeed-patterns.md) — training, inference, streaming, `EndPartition`, early stop, and tensor mapping patterns.
- [API reference](references/api-reference.md) — signatures and queue semantics for the owned API surface.
- [Troubleshooting](references/troubleshooting.md) — hangs, timeouts, output-count mismatches, late exceptions, streaming waits, and stop conditions.
- [`scripts/render_datafeed_template.py`](scripts/render_datafeed_template.py) — render safe code templates without importing or running Spark or TensorFlow.

## Fast validation signal

For inference, the key invariant is: for every batch returned by `next_batch()`, `batch_results()` must receive the same number of results before the next partition can finish. For training, the key invariant is: the TensorFlow code must keep calling `next_batch()` until it has legitimately completed, then call `terminate()` if it exits before Spark has fed all planned input.
