# Troubleshooting

## Cross-cutting failures

### `ModuleNotFoundError` during import or CLI startup

**Symptoms**
- `python -m lightx2v.infer --help` fails before printing help.
- `python -m lightx2v.server --help` fails while importing runtime modules.
- `python -c 'import lightx2v'` fails on missing optional modules.

**Likely causes**
- Missing runtime dependency such as `torch`, `torchvision`, `fastapi`, `uvicorn`, `requests`, `httpx`, `decord`, `av`, `redis`, `pyzmq`, or `qtorch`.
- A backend-specific optional package is unavailable for the requested workflow.
- The installed environment has a broken `numpy`/video-backend combination.

**Recovery**
- Install the missing package named in the traceback.
- Re-run the import or `--help` check after the fix.
- For real generation, use the CUDA-capable install path documented by the repo rather than a CPU-only smoke test.

### `python -m pip check` reports conflicts

**Symptoms**
- `pip check` complains about `numpy`, `opencv-python`, `torch`, `torchvision`, or a pinned package version.

**Likely causes**
- A wheel was installed that pulled in a newer dependency than this repository tolerates.
- A pinned package was replaced during repair.

**Recovery**
- Reinstall the compatible versions, then re-run `pip check` and the import smoke.
- Keep the GPU runtime intact; do not treat a CPU-only import as proof that a CUDA path is usable.

### `numpy` or `decord` looks corrupted

**Symptoms**
- `import numpy` resolves to a namespace package with no `__version__` or core numeric attributes.
- `decord` reports that the build is unsupported on the platform.
- Video-oriented import paths fail even though the package appears to be installed.

**Likely causes**
- A mismatched `numpy`/`decord` build was installed into the environment.
- The interpreter version and the available `decord` wheel/build do not agree.

**Recovery**
- Reinstall a consistent `numpy` and `decord` pair that matches the interpreter.
- Re-run the package import smoke after the repair.
- If the workflow does not need video decoding, note the limitation rather than masking it with a CPU-only success claim.

### `lightx2v_train.train` fails to import `lightx2v_train.data`

**Symptoms**
- `python -m lightx2v_train.train --help` fails with `ModuleNotFoundError: No module named 'lightx2v_train.data'`.

**Likely causes**
- The training package exists in source form, but its import/package layout is not exposed cleanly in the installed environment.

**Recovery**
- Treat the training package as a separate maintenance surface until the import path is repaired.
- Do not use the training entry point as runtime proof for the rest of LightX2V.

## Inference and model-preparation failures

### `model_cls` / `task` combination is invalid

**Symptoms**
- `lightx2v.infer` exits early with a `ValueError` about a model/task mismatch.
- `sensenova_vision` or `omni_vision_task` refuses to start.

**Likely causes**
- The CLI arguments do not match the model-family contract.
- An optional subtask is missing or present in the wrong mode.

**Recovery**
- Check the model-family table in the inference reference.
- Keep `model_cls`, `task`, and any family-specific subtask fields aligned.

### Model path or config path is missing

**Symptoms**
- `validate_config_paths` or the runner initializer complains about missing files.
- The checkpoint layout does not match the expected family structure.

**Likely causes**
- `model_path` points to a directory with the wrong layout.
- A family-specific file such as `config.json`, `transformer/config.json`, or a branch-specific checkpoint is absent.

**Recovery**
- Re-check the family-specific directory layout.
- Use the bundled model-family reference to confirm the expected files before trying again.

### Optional attention or quantization backend is missing

**Symptoms**
- Errors mention `flash_attn`, `sageattn`, `qtorch`, or a failed CUDA extension build.

**Likely causes**
- The selected family or conversion path needs an optional backend that is not installed.
- A CUDA toolkit component such as `CUDA_HOME` or `nvcc` is missing.

**Recovery**
- Install the missing backend only for the workflow that needs it.
- If the workflow can run without the optional accelerator, switch to the supported non-quantized or non-accelerated path.

## Serving failures

### Server startup fails on a missing backend

**Symptoms**
- `python -m lightx2v.server` fails while importing model runners or service modules.
- Tracebacks mention `decord`, `av`, `redis`, `pyzmq`, `httpx`, `fastapi`, or another service dependency.

**Likely causes**
- The selected service path needs a dependency that is not present in the environment.
- A model family used by the server expects an optional backend.

**Recovery**
- Install the missing dependency.
- If the workflow is image-only or video-only, keep the same service surface but note the missing backend in the handoff.

### `/v1/tasks/image/sync` or OpenAI-compatible image calls fail

**Symptoms**
- `400` for invalid sizes, invalid URLs, missing prompt, or unsupported `n != 1`.
- `409` when the client disconnects or a task is cancelled.
- `504` when sync inference exceeds the timeout.
- `502` when presigned upload fails.

**Likely causes**
- Invalid request payload.
- Missing or expired presigned URL.
- Output path or model config does not match the selected model family.

**Recovery**
- Validate the request payload first.
- Try the async `/v1/tasks/image/` route when you do not need immediate bytes.
- Verify upload credentials and URL format when presigned upload is used.

### `/v1/tasks/{task_id}/result` returns 404

**Symptoms**
- Task status is not `completed`, or the result file is missing.

**Likely causes**
- The task failed before writing an output.
- The task is still `pending`, `processing`, or `cancelled`.

**Recovery**
- Poll `/v1/tasks/{task_id}/status` first.
- Confirm the save path is inside the server's output directory.

## Disaggregated deployment failures

### `run_service`, `run_controller`, or `run_user` fail on ZMQ, RDMA, or Mooncake dependencies

**Symptoms**
- Tracebacks mention `zmq`, networking, controller ports, RDMA helpers, or Mooncake transfer logic.

**Likely causes**
- Missing `pyzmq` or a disaggregation backend dependency.
- The config points to a topology or host layout that is not available locally.

**Recovery**
- Install the missing dependency.
- Use a single-node or controller-only dry run first.
- Confirm the config JSON contains the expected disagg mode, ports, and ranks.

### Controller or worker cannot bind its ports

**Symptoms**
- Startup fails with address-in-use or failed-bind errors.
- Requests never reach the controller or the service workers.

**Likely causes**
- A previous service is still running.
- The launch script and the config disagree about the port plan.

**Recovery**
- Stop the stale process tree, then relaunch with a clean port plan.
- Re-check the planner output or the launch reference before retrying.

## Conversion and LoRA tool failures

### Full converter fails on `qtorch`

**Symptoms**
- Import-time errors mention `qtorch` or a C++ extension build.
- The failure mentions `CUDA_HOME`, `nvcc`, or `ninja`.

**Likely causes**
- The optional quantization helper imports a CUDA extension that cannot be built.
- The CUDA toolkit or build toolchain is incomplete.

**Recovery**
- Install `ninja`.
- Set `CUDA_HOME` to a valid CUDA install root if the toolkit is present.
- If you only need LoRA extraction, LoRA merging, or dummy-meta export, use the bundled lightweight helpers instead of the full conversion stack.

### LoRA merge or extract output is empty or has missing keys

**Symptoms**
- The extracted or merged model has fewer tensors than expected.
- The script reports skipped keys or incomplete LoRA pairs.

**Likely causes**
- Base and target shapes do not match.
- The source and target checkpoint naming conventions do not align.

**Recovery**
- Recheck the source and target model types.
- Use the `--diff-only` path when you only need raw deltas.
- Confirm the checkpoint layout before merging into a quantization or deployment workflow.
