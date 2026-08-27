# Troubleshooting serving, export, and checkpoint tools

Use this reference when ModelScope serving, vLLM handoff, exporter APIs, or
checkpoint utilities fail. Keep the safety principle: diagnose first, then run
large or destructive commands only on copies with backups.

## Server command is missing or server extras are absent

Symptoms:

- `modelscope: command not found`
- `No module named fastapi`, `uvicorn`, or `sse_starlette`
- The server wrapper prints guidance to install server and domain dependencies.

Checks:

```bash
python -c "import modelscope; print(modelscope.__version__)"
python -c "import fastapi, uvicorn; print('server deps ok')"
python - <<'PY'
from importlib import metadata
print('modelscope', metadata.version('modelscope'))
PY
```

Fix direction:

- Install the package into the active environment, then install server extras:
  `pip install 'modelscope[server]'`.
- Also install the model domain extras needed by the selected model, such as
  `modelscope[nlp]`, `modelscope[cv]`, `modelscope[audio]`,
  `modelscope[multi-modal]`, or `modelscope[science]`. Domain extras can be
  large and version-sensitive; install only what the target model needs.
- If an entry point is missing but Python import works, try invoking the module
  through the environment's Python or reinstall the package so console scripts
  are generated.

## Port and bind failures

Symptoms:

- `Address already in use`
- Service starts but is unreachable from the expected client.

Checks:

```bash
python - <<'PY'
import socket
host, port = '127.0.0.1', 8000
s = socket.socket()
try:
    s.bind((host, port))
    print(f'{host}:{port} is free')
except OSError as e:
    print(f'{host}:{port} is not free: {e}')
finally:
    s.close()
PY
```

Fix direction:

- Change `--port` or the Docker host-port mapping.
- Use `--host 127.0.0.1` for local-only serving.
- Use `--host 0.0.0.0` inside Docker when publishing with `-p HOST:CONTAINER`.
- Check firewall/security-group rules before assuming the app failed.

## Model download, cache, or credential failures

Symptoms:

- Startup hangs or fails while creating the pipeline.
- Errors mention missing model files, unauthorized access, network timeouts, or
  cache paths.

Checks:

- Confirm whether downloads are allowed for this task. If not, use a local model
  directory or pre-populated cache.
- Confirm the model id and `--revision` are valid.
- Confirm `MODELSCOPE_CACHE` points to writable storage when set.
- For private models, confirm credentials/token are configured by the user; do
  not embed credentials in commands, logs, Dockerfiles, or skill files.

Fix direction:

- Route detailed hub login/download/cache flag work to `../hub-and-cli/SKILL.md`.
- Mount a persistent cache into Docker with `-e MODELSCOPE_CACHE=/modelscope_cache
  -v "$HOST_CACHE:/modelscope_cache"`.
- Retry only after distinguishing transient network failures from missing
  credentials or invalid model/revision.

## GPU, CUDA, and VRAM failures

Symptoms:

- CUDA initialization errors.
- Out-of-memory during startup or first request.
- vLLM fails engine initialization.

Checks:

```bash
python - <<'PY'
try:
    import torch
    print('torch', torch.__version__)
    print('cuda available', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('device count', torch.cuda.device_count())
        print('device 0', torch.cuda.get_device_name(0))
except Exception as e:
    print(type(e).__name__, e)
PY
nvidia-smi || true
```

Fix direction:

- Treat CUDA/domain execution as optional unless it was verified in the target
  environment.
- Use a smaller model, lower vLLM memory/concurrency settings, shorter context,
  or CPU only for non-LLM/small-model testing.
- Align Docker image CUDA/PyTorch versions with the host driver.
- For vLLM, verify the installed vLLM version supports the model architecture.

## ModelScope server versus vLLM confusion

Symptoms:

- Client sends OpenAI-compatible requests to ModelScope `/call`.
- Client expects `/describe` on a vLLM server.
- `VLLM_USE_MODELSCOPE=True` is set but `modelscope server` behavior does not
  change.

Fix direction:

- ModelScope server exposes ModelScope's generic `/describe`, `/call`, and
  `/health` routes. Build the request body from `/describe`.
- vLLM exposes vLLM's API routes and schemas. Use its OpenAI-compatible server
  when clients expect OpenAI-style endpoints.
- `VLLM_USE_MODELSCOPE=True` is for vLLM model resolution. It is not a
  ModelScope server flag.

## Exporter not supported or wrong framework/version

Symptoms:

- `KeyError` saying export for a model type/task is not supported.
- `NotImplementedError` for ONNX/SavedModel/frozen graph.
- Import errors for `onnx`, `onnxruntime`, `tf2onnx`, `tensorflow`, `torch`, or
  domain packages.
- Validation mismatch after export.

Checks:

```python
from modelscope.exporters import Exporter
from modelscope.models import Model

model = Model.from_pretrained(MODEL_ID_OR_DIR)
exporter = Exporter.from_model(model)
print(type(exporter))
print([name for name in dir(exporter) if name.startswith('export_')])
```

Fix direction:

- Use the export method actually implemented by the model-specific exporter.
  Some TensorFlow exporters support SavedModel/frozen graph but not ONNX.
- Provide explicit dummy inputs, dynamic axes, shape, or input shape if the base
  exporter cannot infer them.
- Install validation dependencies if exact export validation matters.
- Use a fresh output directory. Do not mix old export files with a new export.
- For validation mismatch, compare preprocessing, model eval mode, device,
  dynamic axes, opset, and tolerance values before accepting the export.

## `convert_ckpt` destructive writes

Symptoms/risk:

- The utility overwrites every direct `*.pth` file in the target directory.
- It creates `*.pth.legacy` backups and `*_trainer_state.pth` files.
- It may still be unsafe if disk fills mid-run or if the directory already has
  stale backup/state files.

Safe response:

1. Do not run the converter on the only copy of a checkpoint directory.
2. Run the bundled planner:

   ```bash
   python scripts/checkpoint_conversion_plan.py --dir /path/to/checkpoint-copy
   ```

3. Inspect collisions and required additional disk estimate.
4. Make an external backup or work on a copy.
5. Run the real converter only after a human or calling workflow accepts the
   plan.

If a conversion was already run accidentally, first preserve the whole directory
state before attempting recovery. The `.legacy` copies may contain the original
files if the tool reached the copy step successfully.

## Megatron conversion failures

Symptoms:

- `RANK` or `WORLD_SIZE` conversion errors.
- Distributed initialization or tensor parallel size errors.
- Model load errors or out-of-memory.

Fix direction:

- Launch with `torchrun` or another distributed launcher that sets `RANK` and
  `WORLD_SIZE`.
- Match `--nproc_per_node`/world size to the desired tensor model parallel size.
- Use a local/cached model directory if network downloads are not allowed.
- Confirm the model is Megatron-based and supported by ModelScope's Megatron
  conversion helper.
- Use a new target directory with enough disk space.

## Weight diff/recover failures

Symptoms:

- The utility tries to download a path that was intended to be local.
- Model classes or tensor shapes differ.
- Tokenizer loading fails.
- RAM/VRAM/disk usage is much larger than expected.

Fix direction:

- Use local existing paths for both inputs when downloads are not allowed.
- Confirm raw and tuned/diff models share the same architecture and compatible
  tokenizer.
- Write to a new output directory.
- For large LLMs, estimate full model memory and disk needs before starting;
  CPU mode can still require very large RAM.
- Preserve the input models unchanged and retry only after fixing path/model
  compatibility.

## Safe escalation checklist

Before escalating from planning to execution for any large/destructive utility:

- Inputs are local and correct, or downloads are explicitly allowed.
- Output directory is new or disposable.
- External backups exist for files that may be mutated.
- Disk space estimate is sufficient.
- GPU/CPU memory requirements are plausible.
- The operation has a rollback plan.
- The caller understands that CUDA/vLLM/domain behavior is optional and not
  guaranteed unless verified in the target environment.
