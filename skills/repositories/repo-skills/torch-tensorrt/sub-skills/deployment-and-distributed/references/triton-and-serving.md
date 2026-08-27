# Triton and Serving

Use this for serving Torch-TensorRT artifacts with NVIDIA Triton or for building a model repository layout. Running Triton usually requires Docker/container permissions and a prepared GPU server; do not launch it unless the user asks.

## Basic model repository shape

A minimal Triton model repository looks like:

```text
model_repository/
  my_model/
    config.pbtxt
    1/
      model.py or model.plan or model.pt
```

The exact backend and filename depend on whether the user serves a Python wrapper, TorchScript/PyTorch artifact, or TensorRT plan/engine.

## Config generator

Use the bundled helper to create a starting `config.pbtxt` without requiring the original examples:

```bash
python scripts/generate_triton_config.py \
  --model-name my_model \
  --backend pytorch \
  --input input__0:FP32:1,3,224,224 \
  --output output__0:FP32:1,1000
```

For dynamic dimensions, use `-1` in the shape string and document the real Torch-TensorRT optimization profile separately.

## Choosing a Triton backend

| Artifact | Likely backend | Notes |
| --- | --- | --- |
| TorchScript `.pt`/`.ts` | PyTorch backend | Requires PyTorch/Torch-TensorRT runtime compatibility in the Triton environment. |
| Raw TensorRT `.engine`/plan | TensorRT backend | Entire graph must be TRT-supported; no PyTorch fallback. |
| Python wrapper around `.ep` | Python backend | More flexible but requires packaging Python deps and custom model code. |

## Client request pattern

The repository examples use a client that sends NumPy arrays to a named model through Triton's HTTP/gRPC client. In user-facing guidance, write a minimal task-local client using `tritonclient` only when the target server and model config are known.

## Serving checklist

- Confirm artifact format, backend, model name, version directory, input/output names, dtypes, and shapes.
- Confirm the Triton container/server has matching CUDA, TensorRT, PyTorch, Torch-TensorRT, and Python dependencies for the artifact.
- For dynamic shapes, keep Triton `dims` broad enough while relying on the compiled engine's profile for actual accepted ranges.
- Test locally with one request before adding batching/concurrency.
- Add batching only after latency correctness is established.

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Triton fails to load model | Backend/artifact mismatch or missing runtime library. | Verify artifact matrix and runtime packages in the server container. |
| Shape mismatch at request time | Triton config dims disagree with artifact input profile. | Align `config.pbtxt` names/dtypes/dims with compile inputs. |
| Raw engine fails to deserialize | TensorRT version or GPU compatibility mismatch. | Rebuild with compatible flags or on target-like hardware. |
| Python backend import fails | `torch_tensorrt` missing in model environment. | Package dependencies into the Triton Python environment or use a container with Torch-TensorRT. |
