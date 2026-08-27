# Waymax-RL troubleshooting

## Start with the boundary

Waymax-RL is an all-GPU workflow. If the machine cannot provide a CUDA-enabled JAX runtime, the correct fix is to prepare a suitable GPU environment or use a different PARL workflow. There is no equivalent CPU fallback for validating Waymax-RL training throughput or correctness.

This skill production run did not runtime-verify the workflow. Treat the checks below as triage steps to run in the user's environment.

## Symptom triage

### `jax` imports but only CPU devices are listed

Likely causes:

- CPU-only JAX wheel is installed.
- CUDA driver/runtime version does not match the JAX CUDA package.
- The process is running without access to the GPU.

Actions:

1. Install the CUDA-enabled JAX package for the local CUDA version.
2. Confirm `jax.devices()` includes a device with `platform == "gpu"`.
3. Do not proceed with `env_config.backend: cpu`; that changes the workflow and defeats the all-GPU design.

### `Unknown backend gpu`, XLA backend errors, or JIT failures

Likely causes:

- JAX cannot initialize the GPU backend.
- CUDA libraries are missing from the runtime environment.
- A GPU was visible to another framework but not to JAX.

Actions:

1. Re-run the minimal JAX GPU device check in the active environment.
2. Confirm that the same environment is used for training.
3. Reduce `num_actors` only after the backend exists; reducing actors will not fix a missing GPU backend.

### `ImportError: waymax` or incompatible Waymax symbols

Likely causes:

- Waymax is not installed in the active environment.
- The wrong Waymax revision is installed.
- Editable install was run in a different environment.

Actions:

1. Install Waymax from a checkout at commit `71c2be9` unless the user has chosen and tested another revision.
2. Verify imports in the same environment that will launch Waymax-RL.
3. Avoid mixing an unpinned current Waymax checkout with this workflow unless you are prepared to update wrappers and configs.

### TensorFlow conflicts with JAX or grabs GPU memory

Observed facts:

- The initialization code imports TensorFlow and attempts to set GPU memory growth.
- The installation notes advise uninstalling GPU TensorFlow to avoid conflicts.
- The requirements list uses `tensorflow-cpu==2.20`.

Actions:

1. Remove GPU TensorFlow packages such as `tensorflow` or `tensorflow-gpu` if they initialize CUDA or compete with JAX.
2. Allow `tensorflow-cpu` only if required by the bundled initialization path.
3. Keep `XLA_PYTHON_CLIENT_PREALLOCATE=false` so JAX does not preallocate all device memory up front.

### The config still contains `/your_data_path/...`

Likely cause:

- The default placeholder TFRecord path was never replaced.

Actions:

1. Edit `params.config.env_config.data_cfg.data_path` to a real TFRecord file or directory.
2. Run the bundled validator; placeholder paths are reported and treated as not launch-ready.
3. If using a directory with `data_type: tfrecord`, keep only intended TFRecord shards in that directory because the observed wrapper does not filter directory entries by TFRecord suffix before random selection.

### `OSError(<data_path>)` during environment construction

Likely causes:

- The path does not exist in the training process.
- The path is valid on the host but not inside the container/session.
- The path is a placeholder or a stale mount.

Actions:

1. Check the path from inside the same shell/session that launches training.
2. Prefer a single known-good TFRecord file for the first smoke run.
3. If using a directory, verify permissions and contents.

### TFRecord parsing, shape, or `max_num_objects` errors

Likely causes:

- Data is not Waymo Open Dataset TFRecord content compatible with the Waymax WOD training config.
- `max_num_objects` is too small for selected scenarios.
- `num_actors` creates a batch too large for memory or for available data throughput.

Actions:

1. Smoke-test with one known-good TFRecord file.
2. Reduce `num_actors` and `max_num_objects` for debugging.
3. Keep `data_type: tfrecord` unless a separate implementation path has been tested.

### GPU out-of-memory before or during rollout

Likely causes:

- Default `num_actors: 512`, `horizon_length: 90`, and `max_num_objects: 128` exceed available memory.
- JAX/PyTorch/TensorFlow are competing for memory.
- `mixed_precision` behavior differs from expectation.

Actions:

1. Ensure `XLA_PYTHON_CLIENT_PREALLOCATE=false` is active.
2. Reduce `num_actors` first, then `horizon_length`, then `max_num_objects`.
3. Disable `mixed_precision` for diagnosis if precision mode is suspected.
4. Confirm GPU TensorFlow is not installed or initializing CUDA.

### `multi_gpu: true` does not use multiple GPUs or crashes

Likely causes:

- The default workflow was authored with `multi_gpu: false`.
- rl-games multi-GPU setup and JAX device placement need additional runtime validation.
- Data batch and process launch details are underspecified.

Actions:

1. Keep `multi_gpu: false` for first validation.
2. Verify JAX sees all expected GPUs.
3. Treat multi-GPU enablement as a separate experiment; do not assume flipping the flag is sufficient.

### Colab works differently from local

Likely causes:

- Colab images often provide preinstalled CUDA-compatible packages and a visible GPU.
- Local machines need explicit driver, CUDA, package, and data-path preparation.
- Colab paths are ephemeral and do not transfer to local configs.

Actions:

1. Recreate the installation sequence in the local environment rather than copying only the config.
2. Replace all notebook-specific or temporary data paths.
3. Re-run static config validation and JAX GPU checks locally.

### Confusion with `xparl` distributed training

`xparl` is useful for PARL's CPU/GPU worker distribution and remote actor patterns, but it is not the mechanism that makes Waymax-RL efficient. Waymax-RL is designed to keep simulation and training on the GPU path. Use xparl guidance only when the task explicitly asks for PARL cluster mechanics or for a contrast with the all-GPU Waymax loop.
