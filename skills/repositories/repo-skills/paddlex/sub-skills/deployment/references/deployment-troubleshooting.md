# Deployment troubleshooting

## Plugin is missing

Symptoms:

- `paddlex --serve` fails on import/dependency errors.
- `paddlex --paddle2onnx` cannot import conversion tools.
- HPI flags are accepted but backend initialization fails.
- GenAI client/server imports fail.

Actions:

1. Install only the required plugin:
   - `paddlex --install serving`
   - `paddlex --install paddle2onnx`
   - `paddlex --install hpi-cpu` or `hpi-gpu`
   - `paddlex --install genai-client`
   - `paddlex --install genai-vllm-server` or `genai-sglang-server`
2. Verify `paddlex --help` after installation.
3. Do not combine unrelated plugin installs while debugging one workflow.

## GPU / TensorRT / HPI mismatch

Actions:

- Verify the installed PaddlePaddle build is GPU-enabled when using `gpu:*` or GPU HPI.
- Match the HPI plugin to the target backend and device.
- Check CUDA/cuDNN/TensorRT compatibility rather than assuming physical GPU visibility is enough.
- Clear model/backend cache after changing TensorRT versions, dynamic shapes, selected backends, or precision settings.
- Reduce batch size or disable individual submodule HPI when memory errors occur.

## Engine and HPI precedence problems

Common cause: the same run sets `engine`, YAML engine fields, `use_hpip`, and nested `hpi_config` in conflicting ways.

Actions:

1. Start with CPU or plain Paddle inference to confirm the pipeline itself.
2. Enable HPI with the smallest config.
3. Add backend-specific config only after the basic HPI path runs.
4. Keep CLI/API overrides for run-specific settings and persistent backend config in YAML.

## Serving does not start

Checklist:

- Is the `serving` plugin installed?
- Is the selected pipeline runnable locally before serving?
- Is the host/port free and reachable?
- Did auto device selection choose a GPU unavailable to the runtime?
- For high-stability serving, is the OS/Linux Docker/Triton stack prepared?
- If returning URLs for files, is object storage configured as required by the server package?

## Paddle2ONNX fails

Checklist:

- Input path is an exported Paddle inference model directory, not a training checkpoint.
- `paddle2onnx` plugin is installed.
- Opset version is supported by downstream runtime; default is often 7.
- Model-specific preprocessing/config/scaler files are copied with the ONNX output when needed.
- If ONNX conversion is part of HPI, verify both Paddle2ONNX and the HPI backend.

## GenAI client/server fails

Checklist:

- Client has a valid `server_url` when using a server-backed backend.
- API keys or credentials are present only for workflows that require them.
- Server plugin matches backend (`vllm`, `sglang`, FastDeploy, etc.).
- Model directory and chat template are available.
- Backend supports the host hardware and memory budget.
- PaddleOCR-VL / document VLM routes may need large downloads and GPU resources; keep them optional unless explicitly prepared.

## Vendor accelerator or on-device failure

Do not generalize CPU/GPU evidence to NPU/XPU/MLU/DCU/GCU or Android. These routes require vendor-specific PaddlePaddle builds, device strings, SDKs, drivers, compilers, and sometimes model conversion constraints. Record them as unverified until the matching hardware/toolchain is available.
