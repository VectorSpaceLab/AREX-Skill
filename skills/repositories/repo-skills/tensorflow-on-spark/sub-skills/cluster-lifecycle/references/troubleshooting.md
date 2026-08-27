# Troubleshooting

Start with `scripts/tfos_cluster_env_check.py --help`, then run the checks that match your symptom. For Spark-native cluster work, verify the Spark/Java/cluster prerequisites before chasing TensorFlow errors.

## Fast triage

1. Confirm whether the job is `TFCluster` or `TFParallel.run`.
2. Confirm the execution mode: `TENSORFLOW` or `SPARK`.
3. Confirm the cluster size matches the Spark executor count and that Spark tasks per executor are `1`.
4. Confirm the environment can see the Java, Spark, and GPU tools the job expects.
5. Inspect executor logs for the first uncaught exception; later errors are often just fallout.

## Symptom-to-fix matrix

| Symptom | Likely cause | Recovery / validation |
| --- | --- | --- |
| `waiting for X reservations` never ends | Spark executor count does not match the TF cluster size, one executor never started, or a previous node failed before registering. Dynamic allocation or more than one task per executor can also prevent clean reservation flow. | Re-check `MASTER`, `SPARK_WORKER_INSTANCES`, and `SPARK_CLASSPATH`; ensure Spark runs with one task per executor; disable dynamic allocation for this workflow; inspect the first executor log that failed to register; rerun `scripts/tfos_cluster_env_check.py --require-spark-native`. |
| `Duplicate cluster node id detected` | Spark retried a reservation task on the same executor or a stale reservation survived from a previous run. | Make sure the previous job called `TFCluster.shutdown()` successfully; restart the Spark workers if stale managers remain; verify that the cluster size is not smaller than the number of TF nodes you requested. |
| `No TFManager found on this node` | The executor-side manager was never started, usually because cluster sizing, task placement, or a sibling executor failure prevented the reservation flow from completing. | Check the other node logs first; confirm `num_executors` matches the actual Spark executors; confirm tasks per executor are `1`; confirm Spark dynamic allocation is off for this job. |
| `Background mode is not supported on Windows.` | `TFCluster.run(..., input_mode=SPARK)` launches user code in a background process, and the implementation does not support Windows for that mode. | Run on Linux or macOS, or choose a workflow that does not require the background SPARK path. |
| `spark.python.worker.reuse` is not enabled | Background SPARK mode relies on Python worker reuse. | Enable Spark worker reuse before launching the job. If you are not sure whether the cluster sees the setting, run the bundled environment checker and inspect the Spark launch configuration used by the job. |
| `Unable to allocate X GPU(s)`, `Failed to allocate GPU`, or startup appears to wait before any reservation completes on a GPU host | No free GPUs were visible, the request exceeds the visible GPU count, or the Spark resource assignment and `nvidia-smi` fallback disagree. When `nvidia-smi` is visible and `tf_args.num_gpus` is not set, the executor startup path can default to trying one GPU. In Kubernetes, the code may skip the fallback path because of the executor pod signal. | Set `num_gpus=0` in `tf_args` for intentional CPU runs, lower the requested GPU count, free occupied devices, or rely on Spark 3 GPU resources when available. Confirm `nvidia-smi --list-gpus` sees the expected devices. If the job can run without GPUs, make the CPU choice explicit instead of letting startup wait for GPU allocation. |
| `TensorBoard running at` never appears or `cluster.tensorboard_url()` returns `None` | TensorBoard was not enabled, the node that should host it did not qualify, or TensorBoard is not available on the Python path. | Re-run with `tensorboard=True` and a stable `log_dir`; check `TENSORBOARD_PORT` if a pinned port is required; confirm TensorBoard is installed in the same environment that runs the executor code. |
| `TensorFlow execution timed out` during shutdown | The TF code never finished or the `shutdown(timeout=...)` window is too short for the job. | Increase `timeout` or fix the upstream TF hang; inspect worker logs for the actual exception before the timeout alarm fired. |
| `TFOS_SERVER_PORT` invalid or reservation bind fails | The reservation server could not bind because the port spec is malformed or already occupied. | Use a single port or a valid range like `9997-9999`; if a port is already in use, choose a different one and rerun. |
| `release_port() invoked with no bound socket.` | `ctx.release_port()` was called after the socket had already been released, or `release_port=True` already closed it automatically. | If you passed `release_port=False`, call `ctx.release_port()` exactly once immediately before starting the TF gRPC server. |
| `Queue 'input' not found on this node` or `Queue 'output' not found on this node` | The executor-side manager state is inconsistent, usually because another node failed before the queues were fully established. | Inspect the first error on the other nodes; confirm cluster sizing and executor health before retrying. |
| `Unable to find` or `spark-submit` / `java` not found | Spark or Java is missing from the environment, or the job is pointing at the wrong Spark installation. | Confirm `java -version`, `spark-submit --version`, `SPARK_HOME`, and `SPARK_CLASSPATH`. For Spark-native jobs, confirm the tensorflow-hadoop jar is on the classpath. |

## GPU-specific notes

- `gpu_info.get_gpus(...)` retries while waiting for free devices, so a perceived hang can simply mean it is still polling for capacity.
- `util.single_node_env(...)` clears `CUDA_VISIBLE_DEVICES` when no GPU is available, which is a valid CPU fallback.
- `TFCluster` and `TFSparkNode` prefer Spark 3 GPU resources when they are available; the `nvidia-smi` fallback is only used when Spark does not provide resource addresses.

## Shutdown-specific notes

- `TFCluster.shutdown(...)` can fail late if a worker wrote an exception into the shared error queue after the main feed looked healthy.
- The bundled streaming stop helper sends the reservation-server stop request only when `--execute` is present.
- If a stop request appears to do nothing, confirm that you are talking to the same reservation server host and port that the cluster logs reported.

## When to stop debugging and re-check the setup

If the job fails before any executor logs appear, or if multiple symptom rows match at once, go back to the environment checker and verify the Spark/Java/worker-reuse assumptions before changing the TensorFlow code.
