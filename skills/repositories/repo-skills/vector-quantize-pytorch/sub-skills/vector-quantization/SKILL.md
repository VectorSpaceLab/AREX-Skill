---
name: vector-quantization
description: "Base VectorQuantize and RandomProjectionQuantizer workflows for
  single-stage codebook quantization, including masks and lens, image and 3D
  feature maps, kmeans/cosine/codebook-dim tuning, top-k/manual EMA behavior,
  gradient tricks, and optional FVQ bridge guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vector Quantization

Use this sub-skill for the single-stage, codebook-based APIs in `vector_quantize_pytorch`.

## Covers
- `VectorQuantize`
- `RandomProjectionQuantizer`
- `get_output_from_indices`
- `update_ema_indices`
- `topk`
- `mask` and `lens` handling
- `accept_image_fmap` and `accept_3d_fmap`
- `kmeans_init`, `use_cosine_sim`, `codebook_dim`
- stale-code expiration
- orthogonal and codebook-diversity losses
- multi-headed VQ
- `rotation_trick` and `directional_reparam`
- `sync_codebook`
- optional FVQ bridge guidance

## Route elsewhere
- Residual or grouped residual codebooks -> residual-quantizers
- FSQ or FSP -> scalar-quantizers
- LFQ, ResidualLFQ, GroupedResidualLFQ, LatentQuantize, BinaryMapper, EvoLFQ -> lookup-free-and-latent
- SimVQ, ResidualSimVQ, HierarchicalVQ -> sim-and-hierarchical

## Start here
- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke helper](scripts/smoke_vector_quantize.py)

## Fast read
If you only need a safe check, run the smoke helper on CPU. It covers a tiny `VectorQuantize` forward/reconstruction check and a tiny `RandomProjectionQuantizer` round trip.
