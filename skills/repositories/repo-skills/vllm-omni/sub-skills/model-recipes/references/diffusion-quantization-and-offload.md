# Diffusion controls, quantization, cache, and offload

Use this reference when adapting image/video/audio/world-model recipes. Most
controls are model-capability gated; a flag that works for Qwen-Image may be
invalid for LTX, MiniMax-H3, or Cosmos3.

## Start from the goal

| Goal | First control to consider | Then consider | Watch for |
| --- | --- | --- | --- |
| Conservative correctness | BF16 baseline, `max_num_seqs=1`, no cache/quantization | Explicit attention backend only to avoid a known failure | Cold-start and model-download time are not steady-state latency. |
| Single-request latency | Attention backend, CUDA graphs/eager choice, cache backend | FP8/ModelOpt checkpoint, VAE tiling, regional compile | Lossy attention/cache/quantization require same-seed quality comparison. |
| Concurrent throughput | Request batching or step continuous batching | Data parallelism, DLO multi-concurrency, server warmup | Requests batch only when shapes, steps, guidance, output count, and LoRA settings are compatible. |
| Memory fit | CPU offload, layerwise offload, distributed layerwise offload, HSDP | Quantized checkpoint or online quantization | Some offload paths reject online quantization or tensor parallelism. |
| Long/high-res video | Sequence parallelism, VAE patch parallelism, HSDP/offload | Attention backend and cache | VAE decode and host transfers may dominate, not just DiT attention. |
| Model-specific adaptation | Use family recipe fields and `extra_args` | Stage placement/deploy config via sibling skill | Do not copy one family's extra fields into another. |

## Execution modes and batching

| Mode | Config surface | Fits | Notes |
| --- | --- | --- | --- |
| Serial request execution | `--max-num-seqs 1` | Debugging, first validation, models without batching support | Most conservative. |
| Request-level batching | `--max-num-seqs N` plus optional `--request-batch-max-wait-ms` | Compatible independent image/video requests | Send separate concurrent requests; do not pack multiple prompts into one prompt field. |
| Single-request step execution | `--step-execution --max-num-seqs 1` | Step-aware pipelines and streaming preparation | Lets the scheduler advance/cancel between denoise steps. |
| Step continuous batching | `--step-execution --max-num-seqs N` | Throughput for pipelines that explicitly support batched steps | Experimental; start with `N=1` then raise. Some Hunyuan paths require `TORCH_SDPA` for multi-request step batching. |
| Diffusion streaming output | `--diffusion-streaming-output` | Models that can emit intermediate outputs | Requires step execution; if omitted, the server enables step mode and rejects unsupported pipelines at init. |

Limitations:

- Diffusion cache backends are unsupported in step mode.
- FIFO scheduling can let an incompatible request block later compatible ones.
- Different LoRA adapters or scales form separate batches.
- If startup says a pipeline lacks request batching or step hooks, reduce to
  `max_num_seqs=1` or disable step execution.

## Attention backend choices

Use `--diffusion-attention-backend VALUE` for a global choice or a structured
`--diffusion-attention-config` for default/per-role overrides.

| Backend | Best route | Notes |
| --- | --- | --- |
| Platform default | First baseline on supported hardware | The runtime chooses from installed kernels and device capability. Read startup logs to confirm the selected backend. |
| `TORCH_SDPA` | Conservative correctness and Hunyuan multi-request step batching | Always available, slower on some mask-heavy DiTs. |
| `FLASH_ATTN` | CUDA pre-Blackwell, ROCm/AITER routes, or when cuDNN/TRTLLM paths are unsuitable | Requires matching attention package. On Blackwell, FA4 requires a CUDA-specific optional package. |
| `CUDNN_ATTN` | Blackwell mask-heavy DiTs such as HunyuanVideo/Qwen-Image patterns | Pinning cuDNN can avoid slower dispatcher choices. Avoid for LTX-2 under problematic compile traces; select another backend if it fails. |
| `FLASHINFER_ATTN` | Blackwell fallback or mixed-dtype attention experiments | Requires FlashInfer and compatible version for advanced quantized configurations. |
| `TRTLLM_ATTN` | Datacenter Blackwell, compatible packed/mask-free `head_dim=128` pipelines | Enables Skip-Softmax and TRTLLM SAGE attention quantization. Raises rather than silently degrading when requirements are unmet. |
| `SAGE_ATTN` / `SAGE_ATTN_3` | Lossy speedup exploration after BF16/reference validation | Quantized attention can be visually close but must be validated per model/resolution/seed. |
| `RAINFUSION_ATTN` | Ascend NPU block-sparse video attention | Requires MindIE-SD; incompatible with ring sequence parallelism. Tune dense early steps before increasing sparsity. |

Structured attention config is useful when a model has different self/cross or
model-specific roles. Start with a default backend, then override cross-attention
or special roles only when the model needs it.

## Parallelism and memory controls

| Control | Surface | Use when | Compatibility notes |
| --- | --- | --- | --- |
| Tensor parallelism | `--tensor-parallel-size N` or diffusion parallel config | Shard compute/weights for AR or DiT stages that support TP | HSDP rejects TP; some DLO AllGather paths reject TP. |
| Sequence/Ulysses/Ring parallelism | `--usp N`, `ulysses_degree`, `ring_degree`, `sequence_parallel_size` | Long video/image token sequences | Backend support is model-specific; Ring can conflict with block-sparse attention on NPU. |
| CFG parallelism | `--cfg-parallel-size N` | Classifier-free guidance workloads | Do not enable for CFG-distilled models that require size 1. |
| VAE patch parallelism | `--vae-patch-parallel-size N`, VAE tiling/slicing flags | High-resolution image/video decode memory or latency | Some pipelines auto-enable tiling when patch parallelism is requested. |
| HSDP | `--use-hsdp --hsdp-shard-size N` | Multi-GPU memory reduction for large diffusion transformers | Cannot combine with tensor parallelism. HSDP dimensions must match world size. |
| Model-level CPU offload | `--enable-cpu-offload` | Single-GPU memory fit where encoder/DiT components can be mutually excluded | Adds transfer latency. For split models, only one component stays GPU-resident at a time. |
| Layerwise offload | `--enable-layerwise-offload` | Large video DiTs where per-block compute can hide weight transfers | Single-GPU route; model must expose block topology. Layerwise takes priority if both CPU and layerwise offload are enabled. |
| Distributed layerwise offload | `--enable-distributed-layerwise-offload`, optional data parallel size and AllGather mode | Multi-device memory fit and DP multi-concurrency | AllGather mode rejects online quantization, TP, and HSDP. Concurrent requests need explicit matching inference-step counts. |
| Text-encoder TP | model/family-specific flag such as text encoder TP | Large multimodal/video models with heavy encoders | Only for families that document the separate text-encoder stage/component. |

## LoRA routes

| Backend | Use | Configuration | Notes |
| --- | --- | --- | --- |
| PEFT LoRA | Request-time adapter selection and model customization | `lora_path`, `lora_backend="peft"`, request `LoRARequest`, optional `lora_scale` | Adapters are model-specific and must be readable by the server. Different adapters/scales reduce batching compatibility. |
| Distill LoRA | Few-step distilled diffusion or video recipes | `lora_backend="distill"` and one or more concrete LoRA files at startup | Fuses weights into the base model; requests do not pass adapter IDs. Wan dual-transformer variants may require ordered high-noise then low-noise files. |
| Baked converted checkpoint | External conversion plus local Diffusers-style model directory | Serve the assembled checkpoint as the model path | Use when runtime LoRA loading is not the desired deployment shape; conversion can be large and should not be attempted without explicit local assets. |

## Quantization scope and method selection

Quantization is stage/component scoped. Do not assume a flag quantizes every
submodule.

| Model type | Default quantization target | Usually stays BF16/base | Notes |
| --- | --- | --- | --- |
| Diffusion image/video model | Diffusion transformer/DiT | tokenizer, scheduler, text encoder, VAE unless a method guide says otherwise | Qwen-Image, Z-Image, Wan, Hunyuan, Cosmos, MiniMax-style DiTs each need method validation. |
| Multi-stage omni/TTS | Thinker or AR language-model stage when checkpoint config supports it | audio encoder, vision encoder, Talker/TTS, Code2Wav | Prefer checkpoint-declared ModelOpt/AutoRound for Qwen3-Omni; do not claim generic Talker quantization. |
| Multi-stage diffusion | Intended stage-specific transformer/DiT | other stages and VAE unless validated | Route the quantization config to the correct stage rather than applying it globally. |

| Method | Typical use | Backend notes | Common pitfalls |
| --- | --- | --- | --- |
| Online FP8 W8A8 | CUDA DiT memory/latency reduction, some world/video pipelines | Strongest on NVIDIA; ROCm/XPU status is method/model-specific; NPU unsupported for this FP8 path | Sensitive layers may need skips. On MiniMax-H3, online FP8 is incompatible with layerwise offload. |
| Int8 W8A8 | Diffusion transformer reduction where validated | CUDA and NPU have stronger coverage than many other backends | Validate quality; not a generic omni/TTS route. |
| BitsAndBytes W4 | CUDA weight-only memory reduction, especially Z-Image-like DiTs | CUDA only, compute capability gated, optional package required | Multi-GPU TP for diffusion is not generally validated. |
| ModelOpt | Pre-quantized FP8/NVFP4/mixed checkpoints | NVIDIA-focused; CUTLASS backend may be required for validated ModelOpt checkpoint paths | Do not pass online `--quantization fp8` for a checkpoint that already declares ModelOpt quantization. |
| AutoRound | Pre-quantized W4A16 checkpoints | CUDA and Intel-supported routes; checkpoint-driven | The checkpoint config must declare compatible AutoRound fields and stage names. |
| MXFP8 / MXFP4 | NPU and selected XPU/Wan-style routes | Ascend-focused for production; offline dual-scale may be better quality than online single-scale | TI2V and model variants have separate support status; validate before using. |
| msModelSlim | Ascend pre-quantized checkpoints | NPU-specific | Requires method-specific checkpoint preparation; not a CUDA shortcut. |
| Diffusion FP8 KV cache | NPU diffusion Flash Attention tensors | Dedicated diffusion flags, not vLLM AR `kv-cache-dtype` | Only eligible NPU FA backends; skip sensitive steps/layers if quality regresses. |

Quality validation for quantization:

1. Use the same prompt, seed, resolution, frames, guidance, and inference steps
   as the BF16/reference run.
2. Compare both decoded artifacts and latency/peak memory.
3. Use method-specific ignored layers or skip-step/layer selectors only after a
   visible or metric regression points to a sensitive area.
4. Keep checkpoint-declared quantization and online quantization paths separate.

## Cache acceleration

| Backend | Use | Key knobs | Avoid when |
| --- | --- | --- | --- |
| TeaCache | Production speedup with modest quality tradeoff for supported diffusion transformers | `cache_backend="tea_cache"`, `rel_l1_thresh`, optional coefficients | Very short runs, maximum-quality outputs, unsupported architectures. |
| Cache-DiT | More aggressive DiT acceleration with DBCache/TaylorSeer/SCM knobs | `cache_backend="cache_dit"`, `Fn_compute_blocks`, warmup, residual threshold, SCM policy, TaylorSeer | Step execution, non-DiT models, few-step distilled models when TaylorSeer is enabled. |
| Request-scoped quality | MiniMax-H3-style per-request quality switch | `quality="lossless"` or `"high"` in sampling/request params | Treat as model-specific; do not apply to unrelated families. |

Cache guidance:

- Start with default cache config, then tune one knob at a time.
- Lower thresholds or slower SCM policies recover quality; higher thresholds or
  faster SCM policies trade quality for speed.
- Cache hit rate and quality vary by prompt, resolution, steps, model, and
  backend. Benchmark on the user's actual shape.

## Compatibility traps

- **Cache + step execution:** diffusion cache backends are unsupported in step
  mode.
- **HSDP + TP:** HSDP cannot be used with tensor parallelism.
- **DLO AllGather + online quantization:** rejected because mmap/offload paths
  cannot combine with online weight conversion.
- **DLO AllGather + TP/HSDP:** rejected or not end-to-end validated, depending
  on mode.
- **MiniMax-H3 FP8 + layerwise offload:** incompatible; use another memory path
  or disable FP8.
- **NPU RainFusion + ring SP:** incompatible; prefer Ulysses-only sequence
  parallelism.
- **LTX + cuDNN attention under compile:** select `FLASHINFER_ATTN` or
  `TORCH_SDPA` if symbolic-dimension compile failures occur.
- **Different LoRA requests:** different adapters/scales break batching
  compatibility.
- **Omni/TTS quantization:** Thinker/AR checkpoint quantization does not imply
  Talker, Code2Wav, vocoder, VAE, or audio encoder quantization.
