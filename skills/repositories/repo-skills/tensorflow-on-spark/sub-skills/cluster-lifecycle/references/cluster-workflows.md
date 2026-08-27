# Cluster workflows

Use this reference when you need the order of operations for TensorFlowOnSpark cluster startup, reservation, shutdown, TensorBoard, TF_CONFIG, GPU selection, or independent `TFParallel.run` jobs. The API reference lists signatures; this file shows the practical launch and teardown flow.

## Before you launch

1. Run `scripts/tfos_cluster_env_check.py --help` and then the relevant checks for your task.
2. Confirm whether you need a shared `TFCluster` job or an independent `TFParallel.run` job.
3. Confirm the execution mode:
   - `TFCluster.InputMode.TENSORFLOW` when the TensorFlow code reads its own data or manages its own input pipeline.
   - `TFCluster.InputMode.SPARK` when Spark feeds data into the TensorFlow nodes.
4. Decide whether the job needs TensorBoard, a master/chief node, evaluator node, driver-side PS nodes, or `release_port=False`.
5. Decide whether the job should request GPUs, rely on Spark resource assignment, or run on CPU.

## 1) Shared cluster in `TENSORFLOW` mode

This is the most direct `TFCluster` route when the TensorFlow code owns its own input pipeline.

```python
cluster = TFCluster.run(
    sc,
    map_fun,
    tf_args=args,
    num_executors=num_executors,
    num_ps=num_ps,
    tensorboard=True,
    input_mode=TFCluster.InputMode.TENSORFLOW,
    log_dir=log_dir,
    driver_ps_nodes=False,
    master_node='chief',
    eval_node=False,
    release_port=True,
)

# map_fun receives ctx and can use ctx.start_cluster_server() in legacy TF1 code
# or can use modern TF 2.x APIs that build on the provided TF_CONFIG.

cluster.shutdown(grace_secs=0)
```

### Decision points

- Use `master_node='chief'` or `master_node='master'` when your TensorFlow code expects a chief/master role in `TF_CONFIG`.
- Use `eval_node=True` only in `TENSORFLOW` mode.
- Use `driver_ps_nodes=True` only when you want PS tasks on the driver and can afford the changed executor count.
- Set `release_port=False` when the map function needs to bind its own gRPC server. In that case, call `ctx.release_port()` immediately before the bind.

### Validation signals

- Logs show the reservation server started and every executor registered.
- `TFCluster.run(...)` returns a cluster object.
- If TensorBoard was enabled, `cluster.tensorboard_url()` returns a URL.
- `shutdown()` finishes without a late worker exception.

## 2) Shared cluster in `SPARK` mode

Use this route when Spark feeds partitions into the TensorFlow nodes.

```python
cluster = TFCluster.run(
    sc,
    map_fun,
    tf_args=args,
    num_executors=num_executors,
    num_ps=0,
    input_mode=TFCluster.InputMode.SPARK,
)

cluster.train(train_rdd, num_epochs=1, feed_timeout=600)
# or
result_rdd = cluster.inference(eval_rdd, feed_timeout=600)
result_rdd.count()
cluster.shutdown(grace_secs=5)
```

### Decision points

- `train(...)` is for feeding Spark data into the cluster in a training loop.
- `inference(...)` returns a lazy result RDD; remember to run an action.
- `feed_timeout` should reflect how long the TF side may take to consume a partition.
- Keep the queue and batch semantics in the sibling data-feed workflow; this file only covers cluster lifecycle.

### Validation signals

- The Spark job reaches the data-feeding stage only after all nodes have registered.
- `shutdown(...)` handles late exceptions and stops the reservation server.
- The job does not deadlock because one node never registered or one executor was duplicated.

## 3) TensorBoard and custom ports

TensorBoard starts on the first eligible worker/chief node when `tensorboard=True`.

- Set `log_dir` to a stable directory when you want persisted event files.
- Use `TENSORBOARD_PORT` to pin the port when the environment requires it.
- `cluster.tensorboard_url()` returns the first URL that advertised a TensorBoard port, or `None` when none was started.
- `TFOS_SERVER_HOST` and `TFOS_SERVER_PORT` control where the reservation server binds.

If you are choosing your own TF gRPC port inside `map_fun`, reserve the port with `release_port=False` and then call `ctx.release_port()` right before the server bind.

## 4) Independent jobs with `TFParallel.run`

Use `TFParallel.run(...)` when each executor should run an isolated TensorFlow job rather than participate in one shared cluster.

```python
TFParallel.run(
    sc,
    map_fun,
    tf_args=args,
    num_executors=num_executors,
    use_barrier=True,
)
```

### Decision points

- Leave `use_barrier=True` when you need Spark to wait for all executors to be ready together.
- Set `use_barrier=False` only when the job does not need barrier semantics and you are intentionally using plain `mapPartitions`.
- If `tf_args` includes `num_gpus`, that value limits the GPU count used by the per-node environment setup; otherwise the helper defaults to one GPU when GPUs are visible.
- `util.single_node_env(...)` sets `CUDA_VISIBLE_DEVICES` and clears it when GPUs are unavailable.

### Validation signals

- Each executor sees a stable `ctx.executor_id` / `ctx.worker_num`.
- Barrier mode waits for all tasks instead of allowing early completion.
- No reservation server or cluster shutdown state is involved.

## 5) Requesting a streaming stop

When a Spark Streaming job is controlled by a reservation server, use the bundled helper to request shutdown from the driver side.

```bash
python scripts/request_streaming_stop.py --host <reservation-host> --port <reservation-port> --execute
```

Use the dry-run form first if you only want to confirm the address. The script does not send the control message until `--execute` is present.

## 6) GPU and resource selection

TensorFlowOnSpark tries to use Spark 3 resource assignment first when it is available. If Spark does not provide a GPU resource list, the code falls back to `nvidia-smi`-based allocation.

- `gpu_info.is_gpu_available()` is a fast visibility check.
- `gpu_info.get_gpus(...)` may retry while waiting for free devices, so do not use it as a fast health probe.
- `util.single_node_env(...)` is the simpler per-executor environment helper used by `TFParallel.run(...)`.
- If no GPUs are available, `CUDA_VISIBLE_DEVICES` is cleared and CPU execution is valid.

## A simple decision pattern

- Shared cluster, TensorFlow owns data: `TFCluster.run(..., input_mode=TENSORFLOW)`.
- Shared cluster, Spark feeds data: `TFCluster.run(..., input_mode=SPARK)` plus `train(...)` or `inference(...)`.
- Independent executor jobs: `TFParallel.run(...)`.
- Streaming job must stop: `request_streaming_stop.py` or `reservation.Client.request_stop()`.
- Custom server port: `release_port=False` and then `ctx.release_port()`.
