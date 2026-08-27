# Compatibility

Use this reference before installing packages or writing model-loading code. Quantization failures are often caused by optional dependencies, backend kernels, unsupported devices, or conflicts with placement/distributed features.

## Package Boundaries

Base package facts:

- Distribution and import name: `transformers`.
- Inspected version: `5.13.0.dev0`.
- Minimal import can succeed without PyTorch, but model classes, tensor execution, training, and many quantizers require optional dependencies.
- `pipeline(...)` accepts `device`, `device_map`, `dtype="auto"`, `model_kwargs`, and custom pipeline options, but quantized model loading is usually clearer through explicit `AutoModel...from_pretrained(...)` first.

Common packages:

| Workflow | Typical packages | Notes |
|---|---|---|
| `device_map`, offload, large-model dispatch | `accelerate`, `torch` | Required for most `device_map="auto"` examples |
| bitsandbytes 4/8-bit | `bitsandbytes`, `accelerate`, `torch` | Backend wheels differ by CUDA/CPU/XPU/HPU support |
| GPTQ | `gptqmodel`, `optimum`, `accelerate`, `torch` | AutoGPTQ is not the current recommended backend |
| AWQ | `autoawq`, `torch` | Installing AutoAWQ may constrain or downgrade Transformers versions |
| PEFT/QLoRA | `peft`, `torch`, quant backend | Integrated PEFT path expects modern `peft` |
| torchao | `torchao`, compatible `torch` | Use config objects, not removed string aliases |
| DeepSpeed | `deepspeed`, `accelerate`, `torch` | Hardware/build-specific; route training config to training sub-skill |
| FSDP/tensor parallel | `torch`, `accelerate` | Requires distributed launch and compatible models |
| Kernels | `flash-attn`, `liger-kernel`, hub kernel package, backend-specific wheels | Check architecture and dtype support |

## Hardware Matrix Heuristics

| Host/backend | Recommended first choices | Avoid or verify carefully |
|---|---|---|
| CPU-only | GGUF/GGML for supported model files, torchao CPU paths, some GPTQ/HQQ/Quanto methods | Assuming CUDA-focused `bitsandbytes` speedups; GPU-only FP8 kernels |
| NVIDIA CUDA | bitsandbytes, GPTQ, AWQ, torchao, FP8, FlashAttention/Marlin when supported | Old GPUs for `LLM.int8()`/NF4; mismatched CUDA wheel versions |
| AMD ROCm | Some AWQ/GPTQ/Quark paths and PyTorch-native options | CUDA-only kernels, Marlin assumptions, unsupported bitsandbytes builds |
| Apple Silicon/MPS/Metal | GGUF/GGML, Metal-specific quantization, some GPTQ/Quanto/torchao paths | CUDA-only examples, FlashAttention/Marlin, generic `device_map="auto"` expectations |
| Intel XPU | bitsandbytes XPU, torchao, selected quantizers | CUDA-only backend flags and kernels |
| Gaudi/HPU | bitsandbytes HPU where supported, Habana-aware training stacks | CUDA-only kernels and examples |
| Multi-GPU | Tensor parallel, FSDP, DeepSpeed, Accelerate dispatch | Combining `device_map` and `tp_plan`; backend modules that cannot shard |

Treat these as planning heuristics. Actual support depends on package version, wheel build, model architecture, checkpoint metadata, and driver/runtime versions.

## Method Compatibility Highlights

- `bitsandbytes`: supports 4/8-bit workflows and QLoRA; hardware support includes NVIDIA CUDA, Intel XPU, Intel Gaudi, and CPU in current docs, but individual features have minimum hardware requirements. Speedups are not guaranteed.
- `GPTQConfig`: calibration needs a tokenizer and dataset. GPT-QModel is the maintained backend. Some kernels, such as Marlin, are specific to 4-bit CUDA inference and may not support all checkpoint variants.
- `AwqConfig`: loading pre-quantized AWQ checkpoints is common. Fused AWQ modules are architecture-specific and cannot be freely combined with all attention optimizations.
- `TorchAoConfig`: torchao requires compatible PyTorch/torchao versions. In current docs, the string-based API was removed; pass torchao quantization config objects.
- GGUF/GGML: use for GGUF artifacts and llama.cpp-style workflows; do not treat it as a normal PyTorch checkpoint quantizer.
- HQQ/Quanto/SINQ/AQLM/SpQR/VPTQ/HIGGS/Quark/FP8 methods: verify method docs, backend package, hardware, and serialization support before recommending production use.

## Placement And Offload Rules

- `device_map="auto"` requires Accelerate and places whole modules on devices.
- `tp_plan="auto"` shards tensors across devices. Do not combine `tp_plan` and `device_map` unless a specific backend explicitly supports the combination.
- `max_memory` can constrain automatic placement; include CPU memory only when offload is acceptable.
- `llm_int8_enable_fp32_cpu_offload=True` offloads selected bitsandbytes 8-bit modules to CPU as fp32 weights.
- Disk offload support is method-specific. GPTQ docs note that disk offloading is not supported for calibration memory pressure; use `max_memory` instead.
- Custom `device_map` values must match model module names; bad keys silently fail late or leave modules on unexpected devices.

## `dtype` And Compute Dtype

- `dtype="auto"` loads non-quantized modules according to checkpoint config when possible.
- For bitsandbytes 4-bit, distinguish storage quantization from `bnb_4bit_compute_dtype`; common compute dtypes include `float16` and `bfloat16` when hardware supports them.
- AWQ examples may default non-quantized weights to fp16 for performance; override `dtype` intentionally.
- FP8 and torchao methods need hardware support for the chosen dtype or emulation path.
- Mismatched dtype can appear as kernel dispatch failures, NaNs, slow CPU fallback, or incorrect memory estimates.

## PEFT And Training Constraints

- 8-bit and 4-bit training usually means training extra adapter parameters, not updating every quantized base weight.
- PEFT adapter checkpoints are small and may contain only adapter weights plus `adapter_config.json`; keep base model identity explicit.
- FSDP/DeepSpeed checkpointing should avoid saving frozen quantized base weights when adapter-only saving is intended.
- If full fine-tuning is required, consider whether quantization-aware training or torchao-specific training support is actually available.

## `torch.compile` Constraints

- `torch.compile` can improve torchao/HQQ/some kernel paths, but it can also fail on custom quantized modules.
- Static cache or compile options can recompile when batch size, sequence length, or `max_new_tokens` changes.
- In serving or continuous batching, disable compile first when debugging correctness.
- Do not combine compile, fused quantized kernels, and attention replacement all at once; add one optimization at a time.

## Serialization And Hub Push

Before promising save/reload or Hub push, verify the method supports it.

- bitsandbytes 4/8-bit serialization requires compatible recent versions.
- GPTQ can save quantized models and tokenizers; move the model to CPU or a single device first when required after `device_map` loading.
- AWQ and pre-quantized methods rely on checkpoint metadata such as `quantization_config.quant_method`.
- HQQ and some experimental methods may have limited or no quantized-weight serialization.
- GGUF serialization/conversion is a different artifact workflow from normal `save_pretrained`.

## Safe Fallbacks

If the requested method is not compatible:

- CUDA unavailable: propose GGUF CPU, torchao CPU, smaller fp16/bf16 model, or remote/GPU execution instead of forcing bitsandbytes CUDA examples.
- Backend package missing: return an install command and a no-download smoke check before model loading.
- Checkpoint metadata mismatch: load without overriding `quantization_config`, inspect saved config metadata, or choose a checkpoint built for the method.
- Distributed conflict: choose either `device_map` or tensor parallel first; do not combine them by default.
- Compile/kernel failure: disable compile/fused kernels and validate baseline quantized loading before re-enabling optimizations.
