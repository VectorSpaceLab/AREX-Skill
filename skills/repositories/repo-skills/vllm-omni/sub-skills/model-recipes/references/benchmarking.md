# Benchmarking targets and metric choice

vLLM-Omni model recipes should pick metrics from the user's output modality and
serving shape. Do not report token-only metrics for a diffusion video pipeline,
and do not report only end-to-end latency when the user needs interactive first
audio response.

## Metric vocabulary

| Metric | Meaning | Best for | Direction |
| --- | --- | --- | --- |
| TTFT | Time to first text token | AR text/chat stages and text output in omni models | lower is better |
| TPOT | Time per output token after the first token | Sustained AR decode throughput | lower is better |
| TTFP | Time to first streamed media packet, especially audio | Qwen3-Omni speech chat, realtime TTS, streaming media | lower is better |
| E2EL | End-to-end latency from request admission to final output | Image, video, audio, action, full multimodal responses | lower is better |
| RTF | Wall-clock generation time divided by generated audio duration | TTS, speech chat, audio generation, synchronized video/audio | lower than 1.0 is faster than real time |
| Throughput | Requests, tokens, images, frames, or media seconds per wall-clock second | Offline batches and concurrent online serving | higher is better |
| Peak memory | Maximum reserved/allocated device memory, plus host RAM when offloading | Memory-fit and offload/quantization decisions | lower is better, but track quality/latency too |
| Quality similarity | Same-seed image/video/audio similarity or task judge score | Quantization, cache, lossy attention, distilled LoRA | model/task-specific threshold |

## Which workflows fit which metrics

| Workflow | Primary metrics | Secondary metrics | Notes |
| --- | --- | --- | --- |
| AR-only text/chat | TTFT, TPOT, request throughput | E2EL, memory | Use vLLM-style chat serving metrics. |
| Omni chat with audio output | TTFT, TTFP, TPOT, RTF, E2EL | stage durations, throughput | First audio packet matters separately from first text token. |
| TTS `/v1/audio/speech` | TTFP/TTFB, RTF, E2EL, warm throughput | audio duration, sample rate/channels | Measure cold and warm paths separately because compile/graph capture can dominate call #1. |
| Image generation/edit | E2EL, images/s, peak memory | quality similarity, startup/loading time | TTFT/TPOT usually do not describe the DiT path. |
| Video generation/edit | E2EL, media seconds/s, peak memory | per-stage duration, VAE latency, output FPS | VAE decode and I/O may dominate after DiT optimizations. |
| Audio/video generation | E2EL, RTF for audio track, media throughput | AV sync validity, sample rate/channels | RTF can be computed for audio even when video E2EL is the headline. |
| World/action model | E2EL or control-loop latency, action tensor validity | video E2EL, throughput | Async video job endpoints may be required to recover action metadata. |
| Robot policy server | Control-loop latency and action shape/dtype | connection stability, throughput | Do not use MP4 E2EL as the only policy metric. |
| Quantization/cache/offload A/B | E2EL, throughput, peak memory, quality similarity | cold-start overhead | Compare against the same BF16/reference seed and shape. |

## Benchmark planning checklist

1. **Freeze the task shape:** prompt type, output modality, resolution, frame
   count, audio duration, number of inference steps, guidance settings, LoRA,
   and seed.
2. **Separate startup from serving:** report cold-start/load time separately from
   first request and warm steady-state request latency.
3. **Warm up once when relevant:** graph capture, JIT kernels, compile, and
   cache initialization can distort the first request.
4. **Use compatible concurrency:** concurrent requests only batch when shape and
   sampling fields match. LoRA adapters/scales and output counts also matter.
5. **Capture memory consistently:** for offload experiments, record device
   reserved/allocated memory and whether host/page-cache memory increased.
6. **Keep quality gates:** any cache, lossy attention, quantized attention,
   online quantization, pre-quantized checkpoint, or distilled LoRA should be
   checked against the reference run.
7. **Report the backend route:** CUDA/ROCm/NPU/XPU/MUSA, attention backend,
   quantization method, offload mode, HSDP/TP/SP/VAE settings, and whether the
   server was eager or graph-enabled.

## Online serving benchmarks

Use an installed serving benchmark tool when available for OpenAI-compatible
HTTP routes, but keep the metric list aligned with the endpoint:

- Chat/omni chat: include TTFT, TPOT, inter-token latency if applicable, E2EL,
  and throughput.
- Image/video endpoints: include E2EL and request throughput; token metrics are
  not meaningful unless an AR stage is also measured.
- Speech/TTS: include TTFP/TTFB, RTF, E2EL, and throughput under repeated warm
  requests.

For long video or action routes, a simple bounded client loop can be more useful
than a generic token benchmark. Record HTTP status, response size, output media
validity, job polling time for async routes, and any metadata fields such as
action tensor shape.

## Offline benchmarks

Offline `Omni.generate(...)` measurements are useful when the user wants a local
script, a single-process comparison, or a model-quality A/B. They are not the
same as warmed online server throughput because server lifetime, batching, and
request admission are absent.

Recommended offline report fields:

- model family and backend route;
- prompt/request shape;
- generation wall time;
- output artifact count, shape, duration, FPS, or sample rate;
- peak memory if available;
- seed and sampling parameters;
- cache/quantization/offload/attention settings;
- whether model weights were already local.

## Metric examples by family

| Family | What to report first | Why |
| --- | --- | --- |
| Qwen3-Omni | TTFT, TTFP, TPOT, E2EL, RTF | Multi-stage streaming AR + audio needs both token and first media packet metrics. |
| Qwen2.5-Omni | TTFT/TPOT plus E2EL and optional audio RTF | Broad omni route with AR-style serving. |
| Qwen-Image / Z-Image | E2EL, images/s, peak memory, same-seed quality | DiT image generation. |
| HunyuanImage-3.0 | DiT E2EL and throughput for image; TTFT/TPOT only for AR/understanding route | The AR and DiT routes have different bottlenecks. |
| Wan / LTX | Video E2EL, media seconds/s, peak memory, VAE latency | Video resolution/frames and VAE decode dominate target choice. |
| MiniMax-H3 | Video/audio E2EL, media throughput, RTF, stage/component timing | Text encoder, DiT, video VAE, and audio VAE costs differ. |
| Cosmos3 | Image/video/action E2EL, action tensor validity, throughput | One pipeline spans image/video/audio/action; metric follows request mode. |
| VoxCPM2 / MOSS / Higgs / IndexTTS | TTFP/TTFB, RTF, warm throughput, WAV validity | TTS users care about first audio and faster-than-realtime synthesis. |
| DreamZero / GR00T / InternVLA | Control-loop/action latency, action validity, optional media E2EL | Robotics/action tasks are not media-only benchmarks. |

## Benchmark anti-patterns

- Reporting only TTFT/TPOT for a diffusion image/video request.
- Comparing cold first request from one configuration to warm request from
  another.
- Comparing quantized/cache/lossy outputs without fixing seed, shape, and steps.
- Treating a single success on one GPU SKU as backend-general support.
- Ignoring model cache, gated license, or safety-checker downloads in startup
  time.
- Running broad native benchmarks or downloading large checkpoints without user
  budget approval.
