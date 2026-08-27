---
name: model-inference
description: "Run or plan Motus CUDA inference for real-world images and
  RoboTwin policy evaluation, including checkpoint loading, T5 conditioning,
  output contracts, and VRAM troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Motus model inference

Use this route for Motus image-to-video/action prediction, pre-encoded T5
conditioning, checkpoint compatibility, or RoboTwin policy deployment.

- Read [api-reference.md](references/api-reference.md) for model/checkpoint
  contracts and tensor shapes.
- Read [workflows.md](references/workflows.md) for real-world and RoboTwin
  command recipes and asset preflight.
- Read [troubleshooting.md](references/troubleshooting.md) for VRAM, CUDA,
  flash-attn, checkpoint, image, and external-runtime failures.
- Use [data-preparation](../data-preparation/SKILL.md) for dataset/image layout
  preparation and [training](../training/SKILL.md) for training configuration.

## Operating procedure

1. Select real-world no-environment inference or RoboTwin evaluation. Confirm
   the checkpoint family, embodiment YAML, WAN/VAE assets, VLM checkpoint, and
   input image format before loading a model.
2. For real-world inference, provide one three-view concatenated RGB image,
   state/config matching the embodiment, and a language instruction. Prefer a
   pre-encoded WAN T5 tensor when VRAM is limited.
3. Run the parser/help preflight, then verify CUDA, GPU memory, file paths, and
   action/image dimensions. Actual model construction and denoising are
   CUDA-only and require large downloaded weights; do not substitute a CPU
   import for an inference result.
4. Inspect both returned artifacts: predicted future frames are `[B,C,F,H,W]`
   in `[0,1]`, and actions are `[B, action_chunk_size, action_dim]`.
5. For RoboTwin, configure the external simulator/runtime and policy paths
   separately. The policy route may execute robot/simulation side effects and
   is not a safe generic smoke test.

Launches, downloads, and simulator runs require explicit user approval.
