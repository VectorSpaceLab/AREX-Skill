# DataFeed and `InputMode.SPARK` API reference

This reference summarizes the API surface needed to feed Spark RDD or DStream data into TensorFlow worker code through `TFNode.DataFeed`.

## Imports and mode selection

```python
from tensorflowonspark import TFCluster, TFNode

TFCluster.InputMode.TENSORFLOW  # 0: TensorFlow code reads its own data
TFCluster.InputMode.SPARK       # 1: Spark feeds data through DataFeed queues
```

`TFCluster.train()` and `TFCluster.inference()` both assert that the cluster was created with `input_mode=TFCluster.InputMode.SPARK`.

Cluster construction details are owned by the `cluster-lifecycle` sub-skill, but the minimum driver-side mode pattern is:

```python
cluster = TFCluster.run(
    sc,
    main_fun,
    tf_args=args,
    num_executors=args.cluster_size,
    num_ps=0,
    input_mode=TFCluster.InputMode.SPARK,
)
```

## `TFCluster.train`

Signature:

```python
TFCluster.TFCluster.train(self, dataRDD, num_epochs=0, feed_timeout=600, qname="input")
```

Purpose:

- Feeds Spark RDD partitions, or DStream batches, into the TensorFlow workers.
- Leaves interpretation of each row to the user's TensorFlow `map_fun`.
- For static RDD input, repeats the RDD by unioning it `num_epochs` times. If `num_epochs` is `0`, TensorFlowOnSpark uses a fallback repeat count of `10`.
- For DStream input, registers a per-RDD partition feeder.

Arguments:

| Argument | Meaning |
|---|---|
| `dataRDD` | Spark RDD or DStream whose records should be consumed by `DataFeed.next_batch()`. |
| `num_epochs` | Static RDD repeat count. Must be non-negative. Ignored for streaming DStreams. |
| `feed_timeout` | Seconds a Spark feeder task waits for the TensorFlow worker to consume queued input before raising `Timeout while feeding partition`. Default `600`. |
| `qname` | Input queue name. Default `input`; must exist in the cluster queue list. |

## `TFCluster.inference`

Signature:

```python
TFCluster.TFCluster.inference(self, dataRDD, feed_timeout=600, qname="input")
```

Purpose:

- Feeds Spark RDD partitions into TensorFlow workers and returns a lazy Spark RDD of inference results.
- Requires the TensorFlow `map_fun` to consume input rows with `DataFeed.next_batch()` and publish one result per input row with `DataFeed.batch_results()`.

Important behavior:

- The returned RDD is lazy; no data is fed until a Spark action is invoked.
- For every partition, TensorFlowOnSpark queues all input rows, queues an internal `EndPartition` marker, waits for the input queue to drain, then reads exactly the partition's input count from the output queue.
- A missing output item can hang the Spark task while it waits on the output queue.

## `TFCluster.shutdown`

Signature:

```python
TFCluster.TFCluster.shutdown(self, ssc=None, grace_secs=0, timeout=259200)
```

Use after `cluster.train(...)` or after the action on `cluster.inference(...)` completes.

Relevant `InputMode.SPARK` details:

- Sends `None` into worker input queues so `DataFeed.next_batch()` can observe end-of-feed.
- Checks the error queue during shutdown and raises late TensorFlow worker exceptions.
- `grace_secs` gives a chief worker time to finish post-feed work such as exporting a model before shutdown checks late exceptions.
- `ssc` should be supplied for Spark Streaming jobs so shutdown coordinates with the `StreamingContext`.

## `TFNode.DataFeed`

Constructor signature:

```python
TFNode.DataFeed(
    mgr,
    train_mode=True,
    qname_in="input",
    qname_out="output",
    input_mapping=None,
)
```

Arguments:

| Argument | Meaning |
|---|---|
| `mgr` | The manager from `ctx.mgr` inside `map_fun(args, ctx)`. |
| `train_mode` | Use default `True` for training. Use `False` for `cluster.inference()` so partition boundaries can flush partial inference batches. |
| `qname_in` | Input queue name, usually `input`. |
| `qname_out` | Output queue name, usually `output`; used by inference. |
| `input_mapping` | Optional mapping from source field/column names to TensorFlow tensor names. When provided, `next_batch()` returns a tensor-name dictionary. |

### `next_batch`

Signature:

```python
DataFeed.next_batch(self, batch_size)
```

Behavior:

- Blocks on the input queue until it consumes input rows, an internal partition marker, or a shutdown marker.
- Returns at most `batch_size` items.
- Can return fewer than `batch_size` items, especially at an inference partition boundary.
- With no `input_mapping`, returns a list of input rows.
- With `input_mapping`, returns a dictionary keyed by TensorFlow tensor name, where each value is a list of batch values.
- When it consumes shutdown `None`, marks the feed done so `should_stop()` becomes true.

Mapped return example:

```python
input_mapping = {"feature_col": "x:0", "weight_col": "w:0"}
tf_feed = TFNode.DataFeed(ctx.mgr, train_mode=False, input_mapping=input_mapping)
batch = tf_feed.next_batch(128)
features = batch["x:0"]
weights = batch["w:0"]
```

Implementation detail to respect: mapping items are sorted by source key before assigning row tuple positions to tensor names.

### `should_stop`

Signature:

```python
DataFeed.should_stop(self)
```

Returns true after `next_batch()` observes end-of-feed. Use it as the outer loop guard:

```python
while not tf_feed.should_stop():
    batch = tf_feed.next_batch(args.batch_size)
    if len(batch) == 0:
        continue
    ...
```

### `batch_results`

Signature:

```python
DataFeed.batch_results(self, results)
```

Pushes output rows to the Spark output RDD created by `TFCluster.inference()`.

Contract:

- Call only for inference-style feeds where Spark is waiting for output rows.
- For each non-empty batch, pass exactly one result per input row previously returned by `next_batch()`.
- Results should be plain Python or NumPy values that Spark can serialize.

### `terminate`

Signature:

```python
DataFeed.terminate(self)
```

Purpose:

- Signals early termination when TensorFlow training completes before Spark has fed all planned input.
- Sets manager state to `terminating` and drains remaining items from the local input queue.
- Spark feeder tasks that observe the terminating state skip later partitions and request cluster stop coordination.

Limits:

- It does not cancel Spark's RDD operation; extra partitions may still be scanned and ignored.
- Size `num_epochs`, partitions, and training step limits to avoid excessive trailing input.

## Queue markers and propagation

| Marker / queue | Where it is used | User-visible effect |
|---|---|---|
| `EndPartition` | Inserted internally by the inference feeder after each partition. | Lets `DataFeed.next_batch()` return a partial batch for that partition in `train_mode=False`. |
| `None` | Inserted during shutdown into input queues. | Marks end-of-feed; `should_stop()` becomes true after `next_batch()` consumes it. |
| `error` queue | Background TensorFlow worker wrapper writes tracebacks here. | Feeder and shutdown tasks raise `Exception in worker:\n...` when they observe queued errors. |
| `feed_timeout` | Spark feeder wait loop around input queue draining. | Raises `Timeout while feeding partition` if the worker does not consume queued input in time. |

## Common assertions from the API

- `TFCluster.train() requires InputMode.SPARK`
- `TFCluster.inference() requires InputMode.SPARK`
- `Unknown queue: <qname>`
- `num_epochs cannot be negative`
- `Timeout while feeding partition`
- `Queue '<qname>' not found on this node, check for exceptions on other nodes.`
- `Exception in worker:\n<traceback>`
