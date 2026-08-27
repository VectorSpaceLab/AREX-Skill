# Model selection and recipe adaptation

This reference turns vLLM-Omni's supported-model and recipe evidence into a
runtime decision guide. Use it to choose a model family, endpoint, backend route,
and first optimization plan without returning to the source repository.

## Model-family taxonomy

| Family | Representative models | Primary outputs | Best-fit tasks | Route notes |
| --- | --- | --- | --- | --- |
| Omni AR / multimodal chat | Qwen3-Omni, Qwen2.5-Omni | text, audio | text/image/audio/video to chat, speech chat, streaming audio responses | Multi-stage AR pipelines optimize text TTFT/TPOT plus first audio packet and audio RTF. Qwen3-Omni separates Thinker, Talker, and Code2Wav stages; Qwen2.5-Omni is the broader backend-coverage baseline. |
| Diffusion image and image edit | Qwen-Image, Qwen-Image-Edit, Z-Image, GLM-Image, HunyuanImage-3.0, HunyuanVideo image modes | image | text-to-image, image edit, image understanding-to-image | Main targets are image E2EL, peak memory, and images/s. HunyuanImage can expose AR, DiT-only, or AR-to-DiT routes; do not assume AR metrics describe its DiT path. |
| Diffusion video / audio-video | Wan, LTX, MiniMax-H3, HunyuanVideo, LingBot, LongCat, Cosmos3 | video, synchronized audio/video | T2V, I2V, V2V, speech-to-video, reference-to-video/audio | Choose resolution, frames, and reference format first. VAE decode, attention backend, sequence/VAE parallelism, offload, and cache often dominate usability. |
| TTS and speech generation | Qwen3-TTS, VoxCPM2, MOSS-TTS, Higgs-Audio, IndexTTS, GLM-TTS, Voxtral TTS | speech/audio | zero-shot TTS, voice cloning, streaming/realtime speech, sound effects | Use `/v1/audio/speech` for online TTS. Measure RTF, first audio packet/TTFP, and warm-server throughput; first request often includes compile or graph-capture overhead. |
| Diffusion audio / audio effects | Stable-Audio, AudioX, SoulX-Singer | audio | text-to-audio, audio-to-audio, singing voice synthesis | Treat as diffusion/media pipelines: E2EL and RTF matter more than token metrics. Verify output sample rate/channels and model-specific extra fields. |
| World, action, and robotics | Cosmos3, DreamZero, GR00T, InternVLA | image, video, action tensors, robot policy actions | world simulation, action-conditioned rollout, inverse dynamics, OpenPI robot policies | Prefer async video routes when action metadata must be returned. Robot policies use realtime OpenPI WebSocket endpoints rather than ordinary chat. |

## Endpoint and API choice

Choose the endpoint from the output contract, not from the marketing name.

| Desired output | Typical family | Online endpoint/API | Offline API | Benchmark focus |
| --- | --- | --- | --- | --- |
| Text chat or multimodal chat | Qwen3-Omni, Qwen2.5-Omni, AR paths in Hunyuan/BAGEL/Mammoth-style models | `/v1/chat/completions` with multimodal content and model-specific `extra_body` where needed | `Omni.generate(...)` with prompt dictionaries and AR/diffusion sampling params | TTFT, TPOT, E2EL, throughput |
| First streamed audio packet plus final speech | Qwen3-Omni, realtime TTS families | `/v1/chat/completions` for omni chat or `/v1/realtime` when the selected model/launch supports realtime | `Omni.generate(...)` or `AsyncOmni.generate(...)` | TTFP, RTF, E2EL, concurrent throughput |
| TTS waveform | Qwen3-TTS, VoxCPM2, MOSS, Higgs, IndexTTS | `/v1/audio/speech`; some systems also expose voice-management routes | `Omni.generate(...)` or model-specific offline TTS wrappers distilled by sibling skills | TTFP/TTFB, RTF, warm throughput, audio validity |
| Image generation | Qwen-Image, Z-Image, GLM-Image, HunyuanImage, Cosmos3 image mode | `/v1/images/generations`; some chat-style image models also accept `/v1/chat/completions` with image output content | `Omni.generate(...)` with diffusion sampling params | E2EL, images/s, peak memory, quality similarity |
| Image edit / image-to-image | Qwen-Image-Edit, LongCat-Image-Edit, VACE-style image-conditioned routes | Image edit endpoint or chat/images endpoint with reference image fields, depending on the model route | Prompt dict with `multi_modal_data.image` plus diffusion sampling params | E2EL, memory, output quality vs reference |
| Video generation or video edit | Wan, LTX, MiniMax-H3, Cosmos3, HunyuanVideo | `/v1/videos/sync` for direct media bytes; `/v1/videos` for asynchronous jobs or metadata-rich outputs | `Omni.generate(...)` with height/width/frames/fps/extra args | E2EL, media seconds/s, peak memory, VAE latency |
| Action or robot policy | Cosmos3 policy modes, DreamZero, GR00T, InternVLA | `/v1/videos` or `/v1/videos/sync` when actions accompany world-model media; `/v1/realtime/robot/openpi` for OpenPI policies | Model-family offline action route when available | Control-loop latency, E2EL, action tensor validity |

If a request payload is being built, switch to `online-serving`; if an offline
script is being written, switch to `offline-inference`.

## Representative family recipes

| Family | Start here | Add these only after baseline works | Avoid or verify carefully |
| --- | --- | --- | --- |
| Qwen3-Omni | Use the model's multi-stage route for multimodal chat and audio. Keep stage placement and async chunk behavior explicit when serving. | Thinker-stage ModelOpt/AutoRound checkpoints, separate stage placement, streaming benchmark with text+audio metrics. | `/v1/realtime` while async chunk is enabled; generic Talker/Code2Wav quantization claims. |
| Qwen2.5-Omni | Use as a broad-support omni baseline when cross-backend support matters more than latest Qwen3-Omni features. | Backend-specific launch and conservative AR metrics. | Treating output audio latency as just TPOT. |
| Qwen-Image / Qwen-Image-2512 | Baseline image generation on `/v1/images/generations`, then request batching or step execution for throughput. | FP8/ModelOpt checkpoints, TeaCache/Cache-DiT, per-role attention config, step continuous batching for supported pipelines. | Mixing multiple prompts into one prompt field; unvalidated BnB/MXFP paths. |
| Z-Image | Good single-image diffusion route with CUDA plus documented backend coverage; BitsAndBytes W4 is a useful CUDA memory path. | TeaCache, FP8/ModelOpt/AutoRound if checkpoint support exists. | Assuming Qwen-Image's sensitive-layer skips apply unchanged. |
| GLM-Image / HunyuanImage-3.0 | Use when AR reasoning and image generation may be separate concerns. For Hunyuan batching, favor the documented `TORCH_SDPA` route when multi-request step batching is required. | Tensor/sequence/CFG/expert parallelism, ModelOpt mixed FP8/NVFP4, FP8 quality checks. | Applying DiT quantization to the AR path or comparing AR TTFT to DiT E2EL. |
| Wan family | Use for T2V/I2V/S2V/VACE variants; define resolution, frame count, flow/guidance settings, and reference media before optimizing. | Ulysses/sequence parallelism, VAE patch parallelism, HSDP/offload, distilled LoRA, NPU MXFP paths where validated. | Enabling cache/offload/quantization combinations without checking compatibility. |
| LTX family | Use one-stage, ordinary two-stage, or distilled two-stage route according to model checkpoint and quality target. | Layerwise offload on memory-limited GPUs; dynamic LoRA behavior when quantization is enabled. | `CUDNN_ATTN` under torch.compile for LTX-2; use another attention backend if it fails. |
| MiniMax-H3 | Use `/v1/videos/sync` or async video endpoints for T2VA, FL2VA, and Ref2VA. Start with a memory-safe profile for the selected task partition. | Text-encoder TP, Ulysses, VAE patch parallelism, CPU offload, distributed layerwise offload, Cache-DiT request quality, FP8 where compatible. | Running FL2VA and Ref2VA servers together on a tight GPU; combining H3 FP8 with layerwise offload; generic XPU assumptions. |
| Cosmos3 | Use one pipeline for T2I/T2V/I2V/V2V/audio/world/action modes. Use async `/v1/videos` when action tensors or long jobs must be retrieved. | Layerwise offload, online FP8, distributed layerwise offload for multi-device Super/Nano, guardrail toggles with explicit policy. | Ignoring gated components or safety-checker access; expecting image/video sync endpoint to return action metadata needed by policy workflows. |
| TTS families | Use `/v1/audio/speech`; choose high-quality voice cloning vs low-latency realtime based on the family. | Warm-server RTF measurement, voice-management endpoints where supported, low-latency deploy variants. | Measuring only first cold request; assuming all TTS families share voice-clone fields. |
| DreamZero / GR00T / InternVLA | Use when the output is action/world-model behavior, not ordinary media generation. | OpenPI WebSocket and action-shape validation for robot policies; async media job when action tensors accompany generated media. | Treating robot-policy latency as video E2EL alone; changing policy-server config values without validation. |

## Route-level backend notes

These are route notes, not a full installation manual.

| Backend | Use when | Notes |
| --- | --- | --- |
| CUDA/NVIDIA GPU | Default route for nearly every family and the richest optimization support. | Attention backends include platform defaults plus FlashAttention, cuDNN, FlashInfer/TRTLLM, SageAttention variants. FP8, ModelOpt, AutoRound, BitsAndBytes, HSDP, offload, and cache have the most coverage here. |
| ROCm/AMD GPU | Use only for families whose catalog or recipe route lists AMD support. | Expect AITER/FlashAttention-style diffusion attention where validated. Avoid CUDA-only extras such as FA4. Select devices with HIP-visible variables in the serving environment. |
| Ascend NPU | Use for NPU-validated diffusion/video routes such as Wan and selected MiniMax-H3/Cosmos-style paths. | MXFP8/MXFP4, INT8, RainFusion, MindIE-SD, and diffusion FP8 KV-cache are NPU-specific tools. Online quantization plus distributed layerwise offload can be incompatible. |
| Intel XPU | Use for catalog-supported families or AutoRound-oriented checkpoints when the environment is explicitly XPU-ready. | Do not assume CUDA kernels or BitsAndBytes. Validate checkpoint quantization metadata and output quality. |
| MUSA | Treat as model-specific, not generic. | The representative route is MiniMax-H3 with MUSA-visible devices, CPU offload, VAE tiling, and MATE/FlashAttention-3. Avoid CUDA-only optional dependencies and keep ring attention degree conservative. |

## Decision checklist

1. **Output contract:** What artifact must the user receive: text, WAV, image,
   MP4, action tensor, or streaming response?
2. **Family fit:** Select the smallest family that natively produces that output
   and has a supported backend in [model-catalog.json](model-catalog.json).
3. **Endpoint:** Pick `/v1/chat/completions`, `/v1/audio/speech`,
   `/v1/images/generations`, `/v1/videos/sync`, `/v1/videos`, or OpenPI
   WebSocket from the output table above.
4. **Baseline:** Start with BF16/no cache/no exotic quantization unless the
   user specifically needs memory savings first.
5. **Memory path:** If the model does not fit, prefer documented offload,
   tensor/sequence/VAE parallelism, HSDP, or stage placement before reducing
   resolution/frames. Use quantization only when the family/method combination
   is validated or quality can be rechecked.
6. **Throughput path:** Use request batching or step execution only for pipelines
   that advertise support. Benchmark after warmup with compatible concurrent
   requests.
7. **Quality path:** For cache, lossy attention, or quantization changes, compare
   against a BF16/reference run with the same prompt, seed, resolution, frame
   count, and inference steps.
