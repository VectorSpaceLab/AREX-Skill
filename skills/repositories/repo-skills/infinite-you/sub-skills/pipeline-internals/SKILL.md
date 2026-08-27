---
name: pipeline-internals
description: "Routes implementation-level debugging and customization of
  InfiniteYou pipeline internals, including identity face detection and
  embedding, Resampler projection, InfuseNet and FluxControlNet integration,
  control guidance, CPU offload, quantization, LoRA adapters, and Diffusers API
  drift."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Internals

Use this sub-skill when you need to inspect, explain, or adjust the implementation behind InfiniteYou identity conditioning. The implementation is bundled under the generated skill's `runtime/pipelines/` directory, so signature inspection and ordinary debugging do not require the original checkout.

## Use this route for

- Face detection and largest-face selection.
- ArcFace embedding extraction and Resampler projection.
- InfuseNet / FluxControlNet integration.
- Control guidance, timestep handling, and scheduler drift.
- CPU offload, bfloat16, quantization, and LoRA adapter behavior.
- Dependency or API drift in Diffusers, InsightFace, or related runtime packages.

## Read first

- [Pipeline internals reference](references/pipeline-internals.md)
- [Resampler reference](references/resampler.md)
- [Troubleshooting guide](references/troubleshooting.md)

## Safe inspection helper

- [scripts/inspect_pipeline_signatures.py](scripts/inspect_pipeline_signatures.py) — prints or JSON-serializes the bundled runtime's verified public signatures without instantiating models or downloading weights.

## Route elsewhere

For end-user command recipes and generation walkthroughs, use the local-inference route instead.
