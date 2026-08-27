---
name: vector-quantize-pytorch
description: "Route vector-quantize-pytorch tasks across PyTorch vector,
  residual, scalar, lookup-free, latent, SimVQ, and hierarchical quantizer
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# vector-quantize-pytorch

Use this repo skill when a task asks how to use, configure, debug, or validate the `vector-quantize-pytorch` package for neural discrete representations, VQ-VAE tokenizers, residual quantizers, finite scalar quantizers, lookup-free quantizers, latent quantizers, SimVQ, or hierarchical image feature-map quantization.

Do **not** use this skill for generic PyTorch training, unrelated LLM weight quantization, bitsandbytes/QLoRA quantization, vector databases, or nearest-neighbor search libraries unless the task explicitly involves `vector-quantize-pytorch` APIs.

## Install and import baseline

```bash
pip install vector-quantize-pytorch
python - <<'PY'
import torch
from vector_quantize_pytorch import VectorQuantize
vq = VectorQuantize(dim=8, codebook_size=16)
x = torch.randn(1, 4, 8)
quantized, indices, loss = vq(x)
print(quantized.shape, indices.shape, loss.shape)
PY
```

The package imports as `vector_quantize_pytorch`. Base runtime dependencies are PyTorch, einops/einx utilities, and `torch-einops-utils`; the public package has no console entry point. Optional examples may need training-only packages such as `torchvision`, `tqdm`, `fire`, or `x-transformers`, but those are not needed for ordinary API use.

## Route by task

| Task signal | Read |
|---|---|
| Single-stage learned codebooks, `VectorQuantize`, codebook size/dim, masks/lens, image or 3D feature maps, top-k/manual EMA, random projection quantizer, codebook health tricks | [vector-quantization](sub-skills/vector-quantization/SKILL.md) |
| `ResidualVQ`, `GroupedResidualVQ`, stacked residual codebooks, shared/stochastic codebooks, quantize dropout, beam search, DiVeQ, reconstruction from residual indices | [residual-quantizers](sub-skills/residual-quantizers/SKILL.md) |
| `FSQ`, `FSP`, `ResidualFSQ`, `GroupedResidualFSQ`, finite scalar levels, scalar index encoding/decoding, projections, FSP perturbation/norm/activation choices | [scalar-quantizers](sub-skills/scalar-quantizers/SKILL.md) |
| `LFQ`, `ResidualLFQ`, `GroupedResidualLFQ`, `LatentQuantize`, `BinaryMapper`, `EvoLFQ`, binary latents, entropy/diversity losses, latent levels | [lookup-free-and-latent](sub-skills/lookup-free-and-latent/SKILL.md) |
| `SimVQ`, `ResidualSimVQ`, frozen/implicit codebooks, `HierarchicalVQ`, multi-scale image feature-map quantization | [sim-and-hierarchical](sub-skills/sim-and-hierarchical/SKILL.md) |

## Shared references and checks

- [Package overview](references/package-overview.md) summarizes public API families, tensor layouts, return tuple conventions, and common selection rules.
- [Troubleshooting](references/troubleshooting.md) covers install/import failures, PyTorch backend choices, optional example dependencies, tensor shape/layout errors, reconstruction gotchas, and when to run sub-skill smoke helpers.
- [Repository provenance](references/repo-provenance.md) records the source snapshot used to create this skill; read it before deciding whether the skill is stale for another checkout.
- [Router metadata](references/repo-routing-metadata.json) is structured import metadata for the managed `repo-skills-router` if this skill is imported later.
- [Environment checker](scripts/check_vector_quantize_env.py) performs a safe CPU import and representative quantizer smoke check:

```bash
python scripts/check_vector_quantize_env.py --help
python scripts/check_vector_quantize_env.py
```

## Common operating rules

1. Choose the quantizer family first. `VectorQuantize`/`ResidualVQ` are learned-codebook workflows; FSQ/FSP avoid learned embeddings; LFQ/LatentQuantize use binary or per-latent code values; SimVQ/HierarchicalVQ cover implicit/frozen and multi-scale image cases.
2. Decide tensor layout before coding. Many APIs default to `(batch, sequence, dim)`; image/video APIs may require `accept_image_fmap=True`, `accept_3d_fmap=True`, `channel_first=True`, or a class-specific layout.
3. Treat return tuples as class-specific. Do not assume every quantizer returns `(quantized, indices, loss)`: FSQ returns two values, FSP returns four, random projection returns indices only, and hierarchical APIs may return a list/tuple of indices.
4. Use eval mode when generating indices for later reconstruction unless the workflow explicitly needs training-time stochastic sampling or dropout.
5. Do not run original tutorial training loops as quick checks. Use the bundled smoke scripts first; full examples can require dataset downloads, optional packages, and training time.
6. If a workflow spans families, read both sub-skills and keep ownership clear: for example, an audio tokenizer may combine residual routing with scalar or lookup-free details.
