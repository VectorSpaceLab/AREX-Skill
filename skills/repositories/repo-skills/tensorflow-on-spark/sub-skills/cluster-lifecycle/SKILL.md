---
name: cluster-lifecycle
description: "Guide TensorFlowOnSpark cluster startup, reservation, shutdown,
  TensorBoard, TF_CONFIG, GPU/resource selection, and independent TFParallel.run
  jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cluster-lifecycle

Use this route when the task is about starting or stopping a TensorFlowOnSpark cluster, reserving executors, debugging reservation waits, interpreting TF_CONFIG or TensorBoard setup, choosing GPUs or Spark resources, or running independent `TFParallel.run` jobs.

## In scope

- `TFCluster.run(...)` and the returned `TFCluster` object's `train`, `inference`, `shutdown`, and `tensorboard_url` methods.
- `TFSparkNode.TFNodeContext` and the context methods used by map functions.
- `reservation.Server` and `reservation.Client`, including the reservation handshake that coordinates executor startup.
- `TFParallel.run(...)` for independent, one-process-per-executor jobs.
- `gpu_info.*` and `util.single_node_env(...)` for GPU discovery, CUDA selection, and host/runtime setup.

## Out of scope

- Data-feed queue semantics, `EndPartition`, and batch/output handling.
- Spark ML `TFEstimator` / `TFModel` workflows.
- TFRecord/DataFrame conversion.
- Long example migrations and example-to-example conversions.

## Read first

- [API reference](references/api-reference.md) for signatures, object relationships, and internal flow.
- [Cluster workflows](references/cluster-workflows.md) for startup, shutdown, TensorBoard, TF_CONFIG, GPU, and `TFParallel.run` recipes.
- [Troubleshooting](references/troubleshooting.md) for reservation waits, duplicate executor ids, Windows/background limits, Spark config, and GPU failures.

## Use the bundled scripts

- [tfos_cluster_env_check.py](scripts/tfos_cluster_env_check.py) to check Python/package, Spark/Java, GPU visibility, and background-mode prerequisites before cluster work.
- [request_streaming_stop.py](scripts/request_streaming_stop.py) to request a reservation-server stop for a streaming job; it is dry-run by default and only sends the control message when `--execute` is supplied.

## Typical routing cues

- “cluster hangs waiting for reservations”
- “duplicate executor id”
- “TensorBoard URL missing”
- “TF_CONFIG not set”
- “GPU allocation failed”
- “background mode on Windows”
- “`spark.python.worker.reuse`”
- “run several independent TensorFlow jobs on Spark executors”

## Common decisions

1. Decide whether this is a shared `TFCluster` job or an independent `TFParallel.run` job.
2. Decide the execution mode: `InputMode.TENSORFLOW` or `InputMode.SPARK`.
3. Decide whether you need TensorBoard, `driver_ps_nodes`, `master_node`, `eval_node`, or `release_port=False`.
4. If your `map_fun` starts its own TF gRPC server, reserve the port with `release_port=False` and call `ctx.release_port()` before binding the server.
5. Decide whether the job should request GPUs, rely on Spark resource assignment, or fall back to CPU.
6. If a streaming job must stop from the driver side, use the bundled stop helper rather than guessing the reservation protocol.

## Validation signals

- Reservation logs show every executor registered and `TFCluster.run(...)` returns a cluster object.
- `cluster.tensorboard_url()` is non-`None` only when TensorBoard was enabled and a node advertised a port.
- `shutdown()` completes without late exceptions and stops the reservation server.
- `TFParallel.run(...)` returns after all executors complete, with no shared reservation state.

If the task is really about queue semantics, DataFeed batching, or model/dataframe pipelines, route it to the sibling workflow that owns those behaviors instead of expanding this one.
