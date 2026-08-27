# Model-recipes troubleshooting

Use this when model-family selection, backend routing, quantization, offload,
cache, or benchmarking fails. If the error is about exact HTTP payload shape,
route to `online-serving`; if it is about an offline script, route to
`offline-inference`; if it is about stage YAML/placement, route to
`stage-configuration`.

## Quick triage

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Model download asks for authorization, token, or license acceptance | Gated model, nested component, or safety checker is not in the local cache or account scope | Do not retry blindly. Ask the user to approve access or provide a local model path/cache. Record startup/download time separately from inference latency. |
| `model_class_name` or architecture is unsupported | The HF config architecture is not registered in vLLM-Omni, or the selected family uses a custom pipeline route | Check the bundled catalog for a supported representative family. If the user is adding a model, route to `model-integration`. |
| Request reaches server but output modality is missing | Wrong endpoint or missing model-specific `extra_body`/modalities/task fields | Re-select endpoint from `model-selection-and-recipes.md`, then route payload construction to `online-serving`. |
| `/v1/videos/sync` returns media but action metadata is missing | Sync media endpoint was used for an action route that returns metadata through async job state | Use the async `/v1/videos` route for action metadata, or the OpenPI WebSocket endpoint for robot policy. |
| `/v1/realtime` fails for a Qwen3-Omni-style route | Realtime path conflicts with launch settings such as async chunk, or the model does not expose realtime | Use non-realtime chat completion or relaunch with the model's realtime-compatible settings. |
| Startup says a pipeline does not support batching | `max_num_seqs>1` or step continuous batching was enabled for an unsupported pipeline | Reduce to `max_num_seqs=1`; validate the model first, then enable only advertised batching modes. |
| Step execution fails with missing `prepare_encode`, `denoise_step`, scheduler, or decode hook | The selected diffusion pipeline does not implement the step contract | Disable step execution and streaming output for that model. |
| Cache backend fails in step mode | Diffusion cache backends are unsupported in step execution | Disable cache or disable step execution. |
| Different concurrent requests do not batch | Shape, guidance, output count, inference steps, LoRA, or other compatibility-sensitive fields differ | Normalize request fields or benchmark as heterogeneous traffic instead of expecting one fused batch. |
| Attention backend raises immediately | Backend/platform requirements are unmet, such as TRTLLM on non-datacenter Blackwell, RainFusion off NPU, or missing optional packages | Return to platform default or a conservative backend such as `TORCH_SDPA`; install optional kernels only with user approval. |
| LTX crashes with cuDNN attention under compile | Known LTX symbolic-dimension/compile interaction | Select `FLASHINFER_ATTN` or `TORCH_SDPA` for LTX. |
| RainFusion is selected but ring sequence parallelism is enabled | NPU block-sparse attention needs whole key sequence | Use Ulysses-style sequence parallelism and ring degree 1. |
| HSDP rejects the configuration | Tensor parallelism is enabled, shard dimensions do not match world size, or HSDP is combined with an incompatible offload mode | Disable TP or HSDP; set `hsdp_shard_size`/replicate dimensions to match devices. |
| Distributed layerwise offload rejects online quantization | DLO AllGather/mmap path cannot combine with online conversion | Disable online quantization, use a pre-quantized compatible checkpoint, or switch to no-AllGather mode if acceptable. |
| MiniMax-H3 FP8 plus layerwise offload fails | H3 online FP8 is incompatible with layerwise offload | Choose CPU/DLO/HSDP/no-offload memory path, or disable FP8. |
| BitsAndBytes fails on ROCm/NPU/XPU | BitsAndBytes W4 is CUDA-only in this route | Use a backend-specific quantization method or BF16 baseline. |
| ModelOpt checkpoint behaves incorrectly with `--quantization fp8` | Pre-quantized checkpoint should self-declare ModelOpt config | Remove online quantization flag; select the validated linear/MoE backend only if needed. |
| Quantized or cached output has artifacts | Lossy optimization is too aggressive or unsupported for that model/shape | Compare same seed/shape to BF16 reference. Lower cache threshold, disable lossy attention, add ignored layers, or skip sensitive steps/layers. |
| Startup OOM before first request | Weights, nested components, VAE, CUDA graphs, or model cache exceed available memory | Reduce GPU memory utilization, choose CPU/layerwise/DLO/HSDP, lower resolution/frames, or choose a smaller family. Do not treat a CPU parser smoke test as proof of live inference. |
| Warm throughput is good but first request is slow | JIT compile, CUDA graph capture, attention kernel warmup, model load, or cache initialization | Report cold and warm separately; warm once before steady-state benchmark. |
| ROCm command copied from CUDA fails | CUDA-only optional dependency, device selector, or attention backend was reused | Use HIP-visible devices and ROCm-validated attention/quantization routes only. |
| NPU command fails with CUDA/PyTorch assumptions | NPU route uses CPU PyTorch plus accelerator-specific packages and kernels | Use NPU-specific installation and flags; avoid CUDA-only extras. |
| MUSA route fails with combined MiniMax-H3 server | MUSA support is model/partition-specific, not generic | Use the documented single-task partition, MUSA-visible devices, CPU offload, and conservative ring settings. |

## Model cache and license checklist

Before running any native model generation or benchmark, confirm:

1. The user approves network/model downloads or provides local model paths.
2. Gated model terms and nested component licenses are accepted for every
   component the pipeline loads.
3. The model cache has enough disk space for all nested components and compiled
   kernel caches.
4. Startup/download time is not mixed into warm inference latency.
5. A failure to reach a gated nested component is recorded as an access/cache
   limitation, not as proof the model family is unsupported.

## Unsupported backend or model checklist

1. Query [model-catalog.json](model-catalog.json) or the script for the family
   and backend.
2. If the backend is listed only as route-level or recipe-specific, do not
   generalize to sibling families.
3. Read startup logs for the resolved attention backend and model class.
4. Fall back to a conservative backend (`TORCH_SDPA` for diffusion attention, or
   BF16/no-cache/no-quantization) before changing multiple variables.
5. If the user is trying to add support for a new architecture, stop recipe
   adaptation and route to `model-integration`.

## Quantization/offload/cache debug order

When a model worked before an optimization change:

1. Disable cache acceleration.
2. Disable lossy/explicit attention overrides.
3. Disable online quantization or switch back from pre-quantized checkpoint to
   BF16 baseline.
4. Disable offload/HSDP/DLO or reduce to the simplest memory route that fits.
5. Re-enable one feature at a time and measure E2EL, peak memory, and quality.
6. Preserve the exact prompt, seed, shape, frame count, steps, and guidance for
   every A/B.

## Benchmark troubleshooting

| Problem | Fix |
| --- | --- |
| Token metrics are empty for image/video endpoint | Use E2EL and media throughput. Token metrics only apply to AR stages. |
| RTF looks worse on first TTS call | Warm the server and report cold vs warm. Compile/graph capture is expected. |
| Image/video throughput does not improve with higher `max_num_seqs` | Requests may not be compatible, model may not support batching, or FIFO scheduling is blocking compatible requests behind incompatible ones. |
| Offload lowers memory but not latency | Offload trades residency for transfer; expected. Use it for fit, not guaranteed speed. |
| Quantization lowers memory but quality drifts | Adjust ignored layers or use checkpoint/method-specific validation; do not declare support from latency alone. |
| Long video latency remains high after DiT attention optimization | Check VAE patch/tiling and media postprocess costs. |

## Intentional limitations

- This sub-skill does not contain credentials, model cache paths, or local
  environment paths.
- It does not instruct future agents to run original source examples or tests;
  many require large downloads, GPUs, services, or private datasets.
- Backend notes are route-level. For production on a new GPU/NPU/XPU/MUSA SKU,
  validate the exact model, kernel stack, prompt shape, and quality target.
