# Backend Compatibility

Swift supports four main inference backends: `transformers`, `vllm`, `sglang`, and `lmdeploy`. The right backend depends on model support, installed optional dependencies, adapter strategy, multimodal needs, and throughput requirements.

## Quick decision table

| Need | Recommended backend | Why |
| --- | --- | --- |
| First run, unknown model support, QLoRA, or debugging | `transformers` | Broadest Swift compatibility and adapter support. |
| High-throughput OpenAI-compatible LLM/VLM serving | `vllm` | Fast serving, OpenAI API, batching, TP/PP/DP, dynamic LoRA support when backend supports it. |
| SGLang-supported text acceleration | `sglang` | Fast text generation with SGLang parallel features. |
| LMDeploy-supported text/VLM acceleration | `lmdeploy` | Turbomind/PyTorch backend with TP/DP-style deployment support. |
| Multiple named LoRA adapters under one server | usually `vllm` | Swift exposes adapter names as model ids and configures vLLM LoRA options. |
| QLoRA adapter inference | `transformers` or merged/exported path | Accelerated backends do not support QLoRA directly. |
| Multimodal Qwen-VL with memory pressure | `transformers` first, then tuned `vllm` if supported | Use media env limits and vLLM prompt media limits. |

## Capability matrix

| Capability | `transformers` | `vllm` | `sglang` | `lmdeploy` |
| --- | --- | --- | --- | --- |
| OpenAI-compatible deploy | Yes | Yes | Yes | Yes |
| Multimodal | Yes | Yes for supported VLMs | No in the documented matrix | Yes for supported VLMs, with version/model constraints |
| Quantized models | Yes | Yes for supported quantization/model combinations | Yes for supported combinations | Yes for supported combinations |
| Multiple LoRAs | Yes in Python/direct patterns | Yes when vLLM LoRA is supported | No in documented matrix | No in documented matrix |
| QLoRA | Yes | No | No | No |
| Batch inference | Yes, via `--max_batch_size` and dataset mode | Yes, backend batching | Yes, backend batching | Yes, backend batching |
| Parallel techniques | DDP / `device_map` | TP / PP / DP | TP / PP / DP / EP | TP / DP |

## Optional dependency caveats

A minimal ms-swift install can expose base CLI routes while accelerated backends may be missing. Treat missing modules as optional dependency issues, not as proof that the command is invalid.

- `vllm`: requires a compatible vLLM install, GPU/runtime support, and a model in vLLM’s supported set.
- `sglang`: requires SGLang and model support in SGLang.
- `lmdeploy`: requires LMDeploy and model support in LMDeploy. Multimodal maintenance has version constraints in Swift’s engine.
- Evaluation integrations such as evalscope are optional and should be installed only for evaluation workflows.
- Megatron extras are optional and belong to distributed/training workflows, not this inference deployment sub-skill.

## `transformers` backend

Choose this backend when correctness and compatibility matter more than throughput.

Useful flags and Python constructor args:

| CLI/API | Meaning |
| --- | --- |
| `--infer_backend transformers` | Select TransformersEngine. |
| `--max_batch_size` | Batch cap for `TransformersEngine`. |
| `--adapters` | Load LoRA adapters directly. |
| `--merge_lora true` | Merge adapter before inference when desired. |
| `--device_map`, `--attn_impl`, `--torch_dtype` | Model loading/runtime controls inherited from base args. |

Strengths:

- Supports Swift’s broad model registry and template handling.
- Supports QLoRA and adapter debugging.
- Supports text, image, video, and audio model families when the model itself supports them.
- Good for reproducing template or model issues before moving to acceleration.

Limits:

- Throughput is usually lower than purpose-built serving engines.
- Multi-GPU requires DDP or device-map planning rather than backend-native serving parallelism.

## `vllm` backend

Choose vLLM for high-throughput LLM/VLM serving when the model and runtime are supported.

Key flags:

| Flag | Meaning |
| --- | --- |
| `--infer_backend vllm` | Select vLLM engine. |
| `--vllm_gpu_memory_utilization 0.9` | Fraction of GPU memory for model/KV cache. Lower it for OOM or co-hosting. |
| `--vllm_tensor_parallel_size N` | Tensor parallel workers. |
| `--vllm_pipeline_parallel_size N` | Pipeline parallel workers. |
| `--vllm_data_parallel_size N` | Data parallel deploy/rollout size; deploy requires async engine. |
| `--vllm_max_num_seqs N` | Maximum concurrent sequences. Lower it for OOM. |
| `--vllm_max_model_len N` | Context length cap. Lower it for OOM or VLM memory pressure. |
| `--vllm_enforce_eager true` | Disable CUDA graph-style execution; can reduce memory or avoid graph issues. |
| `--vllm_limit_mm_per_prompt '{"image": 5, "video": 2}'` | Cap multimodal items per prompt. Needed for multi-image/multivideo prompts in supported vLLM versions. |
| `--vllm_max_lora_rank N` | Maximum LoRA rank for dynamic vLLM LoRA. Must be >= adapter rank. |
| `--vllm_quantization METHOD` | vLLM quantization method where supported. |
| `--vllm_reasoning_parser NAME` | vLLM reasoning parser when installed vLLM supports it. |
| `--vllm_engine_kwargs JSON` | Additional vLLM engine args as JSON. |

Swift deploy defaults `vllm_use_async_engine` to true. Direct `swift infer` defaults it false for normal generation unless encode task types require async.

LoRA behavior:

- Any adapter passed to vLLM causes Swift to enable LoRA and set `max_loras` from the adapter count.
- Direct `swift infer` uses the first adapter as the active adapter request.
- `swift deploy --adapters name=path ...` exposes adapter names as selectable model ids.
- QLoRA is not supported by accelerated backends; merge/export or use `transformers`.

Multimodal behavior:

- Set `MAX_PIXELS`, `VIDEO_MAX_PIXELS`, and `FPS_MAX_FRAMES` for Qwen-VL-style processor limits.
- Set `--vllm_limit_mm_per_prompt` when a prompt has multiple images/videos and vLLM rejects the request.
- Lower `--vllm_max_model_len`, `--vllm_max_num_seqs`, or `--vllm_gpu_memory_utilization` if VLM deployment OOMs.

## `sglang` backend

Choose SGLang when the model is supported and the serving target is text acceleration.

Key flags:

| Flag | Meaning |
| --- | --- |
| `--infer_backend sglang` | Select SGLang engine. |
| `--sglang_tp_size N` | Tensor parallel workers. |
| `--sglang_pp_size N` | Pipeline parallel workers. |
| `--sglang_dp_size N` | Data parallel workers. |
| `--sglang_ep_size N` | Expert parallel workers for MoE-style cases. |
| `--sglang_context_length N` | Context length cap. |
| `--sglang_mem_fraction_static X` | GPU memory fraction for model/KV pool; lower for OOM. |
| `--sglang_disable_cuda_graph true` | Avoid CUDA graph issues. |
| `--sglang_quantization METHOD` | Quantization where SGLang supports it. |
| `--sglang_kv_cache_dtype auto|fp8_e5m2|fp8_e4m3` | KV cache dtype. |
| `--sglang_enable_dp_attention true` | DP attention path for supported model families. |

Limits:

- The documented matrix marks multimodal and multiple LoRA support as unavailable.
- Optional SGLang dependency failures should be treated as install/runtime issues.
- Backend model support may differ from Swift’s broad `transformers` support.

## `lmdeploy` backend

Choose LMDeploy for models and deployments supported by LMDeploy.

Key flags:

| Flag | Meaning |
| --- | --- |
| `--infer_backend lmdeploy` | Select LMDeploy engine. |
| `--lmdeploy_tp N` | Tensor parallel workers. |
| `--lmdeploy_session_len N` | Maximum session length. |
| `--lmdeploy_cache_max_entry_count X` | GPU cache fraction. |
| `--lmdeploy_quant_policy 0|4|8` | KV cache quantization policy. |
| `--lmdeploy_vision_batch_size N` | Vision batch size for multimodal models. |

Limits:

- The documented matrix marks multiple LoRA and QLoRA as unavailable.
- Multimodal support depends on LMDeploy version and model support; Swift’s LMDeploy multimodal path has version constraints.

## Backend/model support mismatch checklist

When a backend fails to load a model:

1. Confirm the same model works with `--infer_backend transformers`.
2. Check whether the backend officially supports the architecture, quantization, and multimodal modality.
3. Remove adapters, custom quantization, speculative decoding, and reasoning parser flags until the base model loads.
4. Lower context and batch/concurrency limits.
5. Pin/install a backend version compatible with the Swift version and the model family.
6. If only the adapter path fails, test `--merge_lora true` or use a merged/exported model.

## Recommended fallback order

For production planning:

1. Validate prompts/template and media inputs with `transformers`.
2. If throughput is needed, test vLLM with the base model and deterministic text prompts.
3. Add multimodal limits or adapter loading only after the base accelerated model serves.
4. If vLLM is unsupported, test SGLang or LMDeploy if their model lists support the architecture.
5. For LoRA-heavy or QLoRA workloads, prefer `transformers`, merged checkpoints, or separate merged deployments per adapter.
