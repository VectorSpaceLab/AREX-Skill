# Multi-GPU backend patterns

This reference covers the LTX-2 multi-GPU latency path.

## What MGPU is for

MGPU is a **latency tool**, not a memory tool. It reduces the latency of one generation by splitting the denoising work and VAE decode across GPUs on a single machine.

It does **not** make an oversized checkpoint fit. The transformer working copy is still replicated on each GPU.

## Hard gates

- Linux only.
- Single machine only.
- One process per GPU.
- CUDA and NCCL available.
- `ltx-kernels` built for SP all2all.
- GPU count >= 2.

## Technique map

### Sequence parallelism (SP)

- Splits the token sequence across ranks.
- Keeps global attention semantics through all2all exchange.
- Faithful to single-GPU results.
- Mandatory kernel dependency: `ltx_kernels.All2All`.

Use SP when you want the same result with lower latency.

### Tiled data parallelism (TDP)

- Splits the latent into spatial tiles.
- Each GPU denoises its own tile(s).
- Blended output is approximate, not bit-faithful.
- Best for out-of-distribution resolution upscaling.
- Do not use TDP as the first diffusion stage.
- Do not rely on the TDP stage's audio output; keep audio from the SP stage.

### Distributed decoder

- Splits VAE decode across ranks.
- Decodes tiles round-robin and assembles on the driver rank.
- Useful for latency reduction when VAE decode is expensive.
- Has a separate inter-GPU tiling concept from intra-GPU VAE tiling.

### Distributed Gemma

Two approaches exist:

- `AccelerateGemmaBuilder`: sharded Gemma on the source rank with broadcast to others.
- `BatchParallelGemmaBuilder`: replicate + split prompts across ranks.

For the distilled pipeline, use the Accelerate path; batch-parallel only helps when there are multiple prompts to encode.

### MGPU controller

- Persistent one-job-at-a-time worker fleet.
- One `MGPURunner` instance per rank.
- Start once, stream one job, then drain or shut down.
- Unexpected errors poison the controller; symmetric validation errors can be recoverable.

## Builder wiring order

In a runner `setup()`:

1. Build the normal single-GPU pipeline.
2. Create one shared registry.
3. Create one weight tracker for the transformer group.
4. Swap in the MGPU builders:
   - SP for the shared or first stage transformer.
   - TDP for the upscale stage transformer.
   - Accelerate Gemma for text encoding.
   - Distributed decoder for VAE decode.

## Limitations to remember

- SP requires compiled all2all support.
- TDP is still approximate.
- Multi-GPU does not remove the need for FP8/offload when a model does not fit.
- Distributed decode and Gemma are performance strategies, not model-capacity changes.

## Safe response shape

When a user asks for a multi-GPU setup, answer in this order:

1. Whether the request is SP, TDP, distributed decode, Gemma sharding, or controller usage.
2. Whether the machine satisfies Linux / NCCL / multi-GPU / `ltx-kernels` gates.
3. Whether the path is faithful or approximate.
4. Whether there is a simpler single-GPU fallback.
