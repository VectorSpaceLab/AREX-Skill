---
name: lookup-free-and-latent
description: "Lookup-free, binary, latent, and evolutionary quantization
  workflows for vector-quantize-pytorch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Lookup-Free and Latent Quantization

Use this sub-skill when a task needs lookup-free, binary, latent, or evolutionary quantization from `vector-quantize-pytorch`:

- `LFQ` for MagViT-style lookup-free binary latents, entropy/diversity regularization, sequence/image/video inputs, masks, and `indices_to_codes` roundtrips.
- `ResidualLFQ` and `GroupedResidualLFQ` for stacked residual lookup-free quantizers, grouped feature splits, dropout-aware indices, and reconstruction from indices.
- `LatentQuantize` for per-latent scalar code values, `levels`, `num_codebooks`, optional learnable values, and image/video/series channel-first tensors.
- `BinaryMapper` for mapping Bernoulli bit logits to one-hot binary code indices plus optional auxiliary KL loss.
- `EvoLFQ` for wrapping an encoder, decoder, and LFQ bottleneck and optionally evolving binary latent populations.

Route elsewhere for:

- FSQ, FSP, `ResidualFSQ`, or `GroupedResidualFSQ`: use `../scalar-quantizers/`.
- `SimVQ`, `ResidualSimVQ`, or `HierarchicalVQ`: use `../sim-and-hierarchical/`.
- Classic `VectorQuantize`, `RandomProjectionQuantizer`, or codebook EMA health: use `../vector-quantization/`.
- Non-binary residual VQ composition: use `../residual-quantizers/`.

## First steps

1. Confirm which family matches the task: LFQ for binary lookup-free codes, LatentQuantize for per-dimension latent levels, BinaryMapper for bit-logit sampling, or EvoLFQ when there is an encoder/decoder wrapper.
2. Check tensor layout before constructing the module. LFQ accepts sequence-last features for 3D tensors and channel-first image/video features; LatentQuantize treats the feature dimension as the second axis for all ranks.
3. Choose dimensions from the code representation, not just the model hidden size. LFQ requires a power-of-two `codebook_size`; `log2(codebook_size) * num_codebooks` is the internal binary width.
4. Use the API reference for exact constructor and return tuple details, then run the bundled smoke script if the package environment is uncertain.

## Bundled references

- [API reference](references/api-reference.md) for signatures, return values, layout, and reconstruction helpers.
- [Workflows](references/workflows.md) for safe setup patterns and concise examples.
- [Troubleshooting](references/troubleshooting.md) for shape, power-of-two, mask, levels, tuple, and EvoLFQ wrapper failures.

## Bundled smoke helper

Run the CPU smoke helper after installing `vector-quantize-pytorch` and PyTorch:

```bash
python scripts/smoke_lookup_free_latent.py --help
python scripts/smoke_lookup_free_latent.py
```

The helper performs tiny CPU checks for LFQ, ResidualLFQ, GroupedResidualLFQ, LatentQuantize, BinaryMapper, and a minimal EvoLFQ forward unless `--skip-evo` is passed.
