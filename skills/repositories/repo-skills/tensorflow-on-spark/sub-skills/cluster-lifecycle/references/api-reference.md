# API reference

This sub-skill covers the TensorFlowOnSpark lifecycle surface: cluster startup, reservation, shutdown, TensorBoard, TF_CONFIG, GPU selection, and independent `TFParallel.run` jobs. Queue semantics and Spark ML/DataFrame APIs are intentionally out of scope here.

## Object flow

- `TFCluster.run(...)` creates the reservation server, starts executor-side node code, waits for reservations, and returns a `TFCluster` object.
- `TFSparkNode.run(...)` is the executor-side launcher used under the hood by `TFCluster.run(...)`.
- `TFSparkNode.TFNodeContext` is the context object passed to the user map function.
- `reservation.Client` talks to `reservation.Server` during startup and streaming stop.
- `TFParallel.run(...)` launches independent TensorFlow jobs on executors without a shared reservation server.

## Public cluster orchestration

| API | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `TFCluster.InputMode` | `TENSORFLOW = 0`, `SPARK = 1` | Selects direct TensorFlow input or Spark-fed data. | `TFCluster.train(...)` and `TFCluster.inference(...)` require `SPARK`; `TFCluster.run(...)` defaults to `TENSORFLOW`. |
| `TFCluster.run` | `TFCluster.run(sc, map_fun, tf_args, num_executors, num_ps, tensorboard=False, input_mode=TFCluster.InputMode.TENSORFLOW, log_dir=None, driver_ps_nodes=False, master_node=None, reservation_timeout=600, queues=['input', 'output', 'error'], eval_node=False, release_port=True)` | Starts the distributed TensorFlow cluster on Spark executors. | `num_executors` must match the Spark executor count used for the job. `driver_ps_nodes` and `eval_node` are only valid in `TENSORFLOW` mode. `release_port=False` means user code must call `ctx.release_port()` before starting its own TF server. |
| `TFCluster.TFCluster.train` | `train(self, dataRDD, num_epochs=0, feed_timeout=600, qname='input')` | Feeds Spark RDD partitions into a cluster started in `SPARK` mode. | The data-feed contract itself is owned by the sibling workflow; this route only covers the cluster and executor lifecycle. |
| `TFCluster.TFCluster.inference` | `inference(self, dataRDD, feed_timeout=600, qname='input')` | Feeds Spark RDD partitions into a cluster started in `SPARK` mode and returns an RDD of results. | The output RDD is lazy until an action runs. |
| `TFCluster.TFCluster.shutdown` | `shutdown(self, ssc=None, grace_secs=0, timeout=259200)` | Stops the distributed TensorFlow cluster. | In `SPARK` mode, call this after `train` or `inference`. In `TENSORFLOW` mode, it waits for the TF workers to complete. `ssc` is for Spark Streaming jobs. |
| `TFCluster.TFCluster.tensorboard_url` | `tensorboard_url(self)` | Returns the first TensorBoard URL or `None`. | Only non-`None` when a worker/chief started TensorBoard and exposed a port. |

## Executor context and low-level node execution

| API | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `TFSparkNode.TFNodeContext` | `__init__(executor_id=0, job_name='', task_index=0, cluster_spec={}, defaultFS='file://', working_dir='.', mgr=None, tmp_socket=None)` | Holds executor metadata passed to user `map_fun`. | `worker_num` is a backward-compatible alias for `executor_id`. `num_workers` counts master/chief/worker tasks in the cluster spec. |
| `TFSparkNode.TFNodeContext.absolute_path` | `absolute_path(path)` | Convenience wrapper for `TFNode.hdfs_path`. | Uses the context's `defaultFS` and `working_dir`. |
| `TFSparkNode.TFNodeContext.start_cluster_server` | `start_cluster_server(num_gpus=1, rdma=False)` | Convenience wrapper for the legacy TF1 cluster server helper. | Deprecated for TF 2.x+, but still useful when maintaining older code. |
| `TFSparkNode.TFNodeContext.export_saved_model` | `export_saved_model(sess, export_dir, tag_set, signatures)` | Convenience wrapper for the saved-model export helper. | The exported API is legacy TF1 style. |
| `TFSparkNode.TFNodeContext.get_data_feed` | `get_data_feed(train_mode=True, qname_in='input', qname_out='output', input_mapping=None)` | Creates the `TFNode.DataFeed` helper. | The queue semantics are out of scope for this sub-skill. |
| `TFSparkNode.TFNodeContext.release_port` | `release_port()` | Closes the temporary socket reserved for the TF gRPC server. | Use this when `release_port=False` was passed to `TFCluster.run(...)`. |
| `TFSparkNode.run` | `run(fn, tf_args, cluster_meta, tensorboard, log_dir, queues, background)` | Wraps user `map_fun` execution on Spark executors. | Creates `TFManager` state, reserves GPUs, exports `TF_CONFIG` when needed, and launches background processes for `SPARK` mode or PS/evaluator nodes. |
| `TFSparkNode.train` | `train(cluster_info, cluster_meta, feed_timeout=600, qname='input')` | Executor-side Spark-fed training hook. | Returns a `mapPartitions` function. |
| `TFSparkNode.inference` | `inference(cluster_info, feed_timeout=600, qname='input')` | Executor-side Spark-fed inference hook. | Returns a `mapPartitions` function that emits inference results. |
| `TFSparkNode.shutdown` | `shutdown(cluster_info, grace_secs=0, queues=['input'])` | Executor-side shutdown hook. | Stops queues and checks for late errors before setting manager state to stopped. |

## Reservation protocol

| API | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `reservation.Reservations` | `Reservations(required)` | Thread-safe store for node reservations. | Backing store used by the reservation server. |
| `reservation.Server` | `Server(count)` | Socket server that collects reservations during cluster startup. | `count` must be greater than zero. |
| `reservation.Server.start` | `start(self)` | Starts a background listener and returns `(host, port)`. | The host defaults to the machine IP unless `TFOS_SERVER_HOST` is set. The port may come from `TFOS_SERVER_PORT` or an available port. |
| `reservation.Server.await_reservations` | `await_reservations(self, sc, status={}, timeout=600)` | Blocks until all nodes have registered. | Used by `TFCluster.run(...)` to wait for every executor. |
| `reservation.Server.stop` | `stop(self)` | Marks the server done. | The streaming stop helper uses the client-side stop request to reach this state. |
| `reservation.Client` | `Client(server_addr)` | Connects to the reservation server. | `server_addr` is `(host, port)`. |
| `reservation.Client.register` | `register(self, reservation)` | Registers a node reservation with the server. | Used by executor-side startup. |
| `reservation.Client.get_reservations` | `get_reservations(self)` | Fetches the current reservation list. | Useful for debugging cluster composition. |
| `reservation.Client.await_reservations` | `await_reservations(self)` | Polls until all reservations complete. | Returns the final cluster info list. |
| `reservation.Client.request_stop` | `request_stop(self)` | Requests that the server stop. | This is the control path used by the streaming stop helper. |

### Reservation environment variables

- `TFOS_SERVER_HOST`: overrides the host that the reservation server binds to.
- `TFOS_SERVER_PORT`: overrides the bind port or port range. Accepts a single port or a range such as `9997-9999`.

## Independent executor jobs

| API | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `TFParallel.run` | `run(sc, map_fn, tf_args, num_executors, use_barrier=True)` | Runs independent TensorFlow jobs on Spark executors. | Does not create a shared reservation server. Use this when each executor runs its own isolated job. |
| `util.single_node_env` | `single_node_env(num_gpus=1, worker_index=-1, nodes=[])` | Sets up CUDA and Hadoop compatibility environment variables. | Used by `TFParallel.run(...)`. If GPUs are unavailable, it falls back to CPU by clearing `CUDA_VISIBLE_DEVICES`. |
| `gpu_info.is_gpu_available` | `is_gpu_available()` | Checks whether GPUs are visible through `nvidia-smi`. | Fast probe only. |
| `gpu_info.get_gpus` | `get_gpus(num_gpu=1, worker_index=-1, format='string')` | Selects free GPUs using `nvidia-smi`. | May retry while waiting for free GPUs. Do not call it in a quick health check unless GPU allocation is intentional. |
| `util.get_ip_address` | `get_ip_address()` | Returns the host IP address. | Used in reservation and executor startup logic. |
| `util.write_executor_id` | `write_executor_id(num)` | Writes the executor id to a local file. | Used by executor-side startup to correlate retries. |
| `util.read_executor_id` | `read_executor_id()` | Reads the executor id from the local file. | Raises a detailed error when the file is missing. |
| `util.find_in_path` | `find_in_path(path, file)` | Searches a path string for a file. | Used to locate TensorBoard and related executables. |

## Key relationships to remember

- `TFCluster.run(...)` computes the cluster template, starts `reservation.Server`, and dispatches `TFSparkNode.run(...)` across executors.
- `TFSparkNode.run(...)` creates `TFNodeContext`, initializes a `TFManager`, sets `TF_CONFIG` when a master/chief node exists, and chooses GPU or CPU execution.
- `TFParallel.run(...)` only sets up per-executor environment and then calls the user `map_fn`.
- The reservation client/server pair is the control plane for startup and for the streaming stop helper.
