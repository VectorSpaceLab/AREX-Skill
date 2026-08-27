# Package Overview

## Purpose

Read this reference to choose a `vector-quantize-pytorch` API family, understand common tensor and return conventions, and avoid mixing similar quantizer classes.

## Public API families

| Family | Main classes | Best for | Typical output |
|---|---|---|---|
| Learned vector codebook | `VectorQuantize` | Classic VQ-VAE layers, k-means init, EMA updates, codebook usage tricks, image/sequence/3D feature maps | `(quantized, indices, commit_loss)` |
| Residual learned codebooks | `ResidualVQ`, `GroupedResidualVQ` | Multi-stage residual quantization, audio/token compression, shared/stochastic codebooks, grouped feature dimensions | `(quantized, indices, commit_loss)`; grouped indices start with a `groups` axis |
| Random projection | `RandomProjectionQuantizer` | Non-learned random projection code assignments for masked speech/token pretraining style workflows | `indices` only |
| Finite scalar quantization | `FSQ`, `ResidualFSQ`, `GroupedResidualFSQ` | Scalar level discretization without learned codebook embeddings | FSQ returns `(quantized, indices)`; residual variants return stacked indices |
| Finite scalar perturbation | `FSP` | Stochastic scalar perturbation during training with deterministic eval quantization and optional vector normalization | `(quantized, indices, norm_loss, other_info)` |
| Lookup-free/binary quantization | `LFQ`, `ResidualLFQ`, `GroupedResidualLFQ`, `BinaryMapper` | Binary latents, entropy/diversity regularization, MagViT-style tokenizers, bit-logit mapping | Usually `(quantized, indices, entropy_or_commit_loss)` |
| Latent quantization | `LatentQuantize` | Per-latent scalar code values with optional learned values and multi-codebook outputs | `(quantized, indices, loss)` |
| Evolutionary LFQ wrapper | `EvoLFQ` | Encoder/LFQ/decoder wrapper with evolutionary latent population search patterns | Depends on encoder/decoder wrapper; inspect workflow reference |
| Implicit/frozen codebooks | `SimVQ`, `ResidualSimVQ` | SimVQ-style implicit codebooks, rotation trick, residual SimVQ stacks | `(quantized, indices, commit_loss)` |
| Hierarchical image quantization | `HierarchicalVQ` | Multi-scale image feature-map quantization with per-scale indices | `(quantized, indices_list, commit_loss)` |

## Selection rules

- Start with the representation, not the model name.
  - Need nearest learned code vectors and codebook usage controls: `VectorQuantize`.
  - Need multiple codebooks over residuals: `ResidualVQ` or grouped residual variants.
  - Need no learned embedding table: `FSQ`, `FSP`, or `LFQ` depending on whether levels are scalar, perturbed, or binary lookup-free.
  - Need binary codebook size as a power of two: `LFQ`.
  - Need implicit generated/frozen codebooks: `SimVQ`.
  - Need image-feature pyramid quantization: `HierarchicalVQ`.
- For residual stacks, pick the residual class from the same family when possible: `ResidualVQ` for learned codebooks, `ResidualFSQ` for scalar levels, `ResidualLFQ` for lookup-free codes, and `ResidualSimVQ` for SimVQ.
- Use grouped residual classes when the feature dimension should be split into independent groups. Check grouped index axes before writing downstream code.
- Use `get_output_from_indices` or `indices_to_codes` only with the same module state that produced or owns the codebooks/levels. Saved indices alone are not enough for learned codebooks.

## Tensor layout conventions

- Sequence workflows usually use `(batch, sequence, dim)`.
- Image feature maps are commonly `(batch, channels, height, width)` and may need `accept_image_fmap=True` or `channel_first=True` depending on the class.
- Video features in LFQ/LatentQuantize examples use channel-first feature axes, such as `(batch, channels, time, height, width)`.
- `VectorQuantize(accept_3d_fmap=True)` handles 3D feature maps shaped `(batch, channels, depth, height, width)`.
- `LatentQuantize` treats the feature dimension as the second axis for image/video/series-style examples; transpose or reshape sequence tensors deliberately instead of guessing.

## Return tuple cautions

- `VectorQuantize`, `ResidualVQ`, `LFQ`, `LatentQuantize`, `SimVQ`, and related residual variants often look like `(quantized, indices, loss)`, but their loss shape and name differ.
- `FSQ` returns `(quantized, indices)` and may return `indices=None` when `return_indices=False`.
- `FSP` returns four values: `(quantized, indices, norm_loss, other_info)`.
- `RandomProjectionQuantizer` returns indices, not quantized vectors.
- `HierarchicalVQ` returns per-scale indices as a sequence; do not treat it as one dense index tensor without checking the workflow.
- Some APIs can return extra data when flags such as `return_all_codes` or `return_loss_breakdown` are enabled.

## Verification habits

- Run the root smoke helper first when diagnosing installation or import issues.
- Run the nearest sub-skill smoke helper before using a family-specific recipe.
- Keep checks tiny and CPU-safe unless the user explicitly needs full training or accelerator validation.
- Avoid tutorial training scripts for quick validation; they may download datasets or need optional example dependencies.
