# LightX2V Overview

## What this skill covers

LightX2V is a lightweight image/video generation framework with four broad user-facing routes:

1. **Direct inference** through `LightX2VPipeline` and `python -m lightx2v.infer`
2. **HTTP serving** through `python -m lightx2v.server` and the `/v1/*` APIs
3. **Disaggregated deployment** through the controller / encoder / transformer / decoder stack
4. **Weight preparation** through LoRA extraction, LoRA merging, dummy-meta export, and related conversion helpers

## Route summary

| Route | Best for | Common triggers |
| --- | --- | --- |
| Inference | Local generation and model-family setup | prompt-to-video, prompt-to-image, `model_cls`, `task`, `create_generator`, `generate`, offload, parallel, quantization, LoRA-backed inference |
| Serving | Queue-based API usage | FastAPI startup, `/v1/tasks`, `/v1/images`, `/v1/service`, result download, cancel/stop flows, sync image requests |
| Disaggregation | Multi-process deployment | controller, encoder, transformer, decoder, Mooncake, RDMA, ZMQ, single-node vs multi-node deployment |
| Conversion | Checkpoint surgery and metadata helpers | LoRA extraction, LoRA merging, dummy-meta safetensors, weight-format preparation |

## Common family names

The repository supports many model families. The most common names you will see in user requests are:

- Wan 2.1 / 2.2
- Qwen Image / Qwen Image Edit
- HunyuanVideo-1.5
- Hunyuan Image 3
- LTX-2 / LTX-2.5
- MiniMax-H3
- WorldMirror
- WorldPlay
- SeedVR2
- Bagel, SenseNova-Vision, ERNIE, Z-Image, Flux2, Neopp, Motus, LingBot, FastWAM, InfiniteTalk, DreamZero, Cosmos3, Hunyuan3D

## Public package facts

- Python 3.10+ is required.
- The published package name is `lightx2v`.
- The runtime stack expects a CUDA-capable environment for real generation and service workloads.
- Optional dependencies may be required for video decoding, distributed communication, quantization, or model-family-specific paths.

## How to choose quickly

- If the user asks for a local generation recipe, start with inference.
- If the user wants to submit requests or manage tasks, start with serving.
- If the user wants controller / encoder / transformer / decoder deployment, start with disaggregation.
- If the user wants to extract, merge, or export weights, start with conversion.

If a request spans multiple routes, answer the most specific route first and then cross-read the others.
