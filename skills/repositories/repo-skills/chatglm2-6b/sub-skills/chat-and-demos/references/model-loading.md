# Model Loading and Backend Choices

## When to read

Read this before choosing a model identifier, local checkpoint, backend, or
quantization mode for a ChatGLM2-6B generation task.

## Model source and revision

The documented public source is `THUDM/chatglm2-6b`. A local directory can be
used instead when downloads are slow or a deployment must be reproducible.
`trust_remote_code=True` is required because the ChatGLM model implementation
is supplied through the Transformers model repository. If compatibility with
the documented implementation matters, pin the model revision (the README
mentions `v1.0`) rather than relying on a moving default.

The tokenizer and model source must refer to the same base model. A P-Tuning
prefix checkpoint is not a replacement for the base model: load the base model
and then attach the prefix state, as described in the `ptuning` route.

## Backend and memory matrix

| Mode | Typical model call | Evidence-backed constraint | Use when |
| --- | --- | --- | --- |
| CUDA FP16/BF16 | `AutoModel.from_pretrained(...).cuda().eval()` | README reports roughly 13 GB for FP16/BF16 and recommends PyTorch 2.0+ for scaled-dot-product attention. | Default official demos and high-throughput local use. |
| CUDA INT4/INT8 | load a quantization-capable model or call the documented `quantize(bits)` API before `.cuda()` | INT4 reduces memory but can affect quality; kernels are CUDA-oriented. | GPU memory is limited and the selected model implementation supports the quantization path. |
| CPU | `.float().eval()` | README estimates about 32 GB RAM for the unquantized model and slower generation. | No GPU, offline CPU service, or a compatibility check. |
| CPU quantized | `.quantize(4).float()` where supported | Linux/Windows need OpenMP/compiler support; Mac CUDA kernels are not available. | CPU has enough RAM and the quantization implementation supports the platform. |
| Apple MPS | `.to("mps").eval()` from a local model path | README documents Apple Silicon/AMD Mac use with a compatible PyTorch nightly and local weights. | macOS MPS deployment; do not copy the Linux CUDA command unchanged. |
| Multi-GPU | `utils.load_model_on_gpus(path, num_gpus=N)` | `accelerate` dispatches a layer map; first-device placement is intentional to avoid input/embedding device mismatch. | Each GPU is too small for the whole model or a larger context is needed. |

These memory values are planning estimates, not guarantees. Context length,
KV cache, batch size, PyTorch version, and quantization implementation change
actual usage. Measure with a short prompt before committing to a long context.

## Conversation API

- `model.chat(tokenizer, query, history=[])` returns a response string and a
  list of `[query, response]` pairs.
- `model.stream_chat(tokenizer, query, history=history, ...)` yields partial
  response updates. Preserve the returned history; when a demo requests
  `return_past_key_values=True`, preserve the third value as well.
- Common generation controls in the repo are `max_length`, `top_p`, and
  `temperature`. Keep `max_length` within the selected model/context budget.

## Multi-GPU map

The bundled `inspect_device_map.py` mirrors the repository's safe arithmetic
without loading weights. It assumes 28 transformer layers and reserves two
units before assigning layers across `num_gpus`. `load_model_on_gpus` uses
`accelerate.dispatch_model` for two or more GPUs; a custom `device_map` can be
passed when the automatic split is unsuitable. Inspect the real model module
names before customizing the map for a newer remote-code revision.
