---
name: sim-and-hierarchical
description: "Use SimVQ, ResidualSimVQ, and HierarchicalVQ for implicit/frozen
  codebooks and multi-scale image feature-map quantization in
  vector-quantize-pytorch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SimVQ and HierarchicalVQ Router

Use this sub-skill when the task mentions vector-quantize-pytorch SimVQ, ResidualSimVQ, frozen or implicit codebooks, rotation-trick SimVQ, residual SimVQ reconstruction, or HierarchicalVQ multi-scale image feature-map quantization.

## Route here for

- `SimVQ` sequence or feature-map quantization with a frozen codebook transformed by a learnable linear layer or custom module.
- `ResidualSimVQ` stacked residual SimVQ layers, including `channel_first=True`, quantizer-dropout indices, `return_all_codes`, and reconstruction with `get_output_from_indices`.
- `HierarchicalVQ` image feature maps with sorted `scales`, `quant_resi`, `share_quant_resi`, `accept_image_fmap=True`, and a tuple/list of per-scale index tensors.
- Debugging layout, reconstruction tolerance, finite commitment losses, or implicit-codebook semantics for the above classes.

## Route elsewhere

- Classic `VectorQuantize` codebook settings, masks, image fmap VQ, `RandomProjectionQuantizer`, top-k, and manual EMA updates: use the `vector-quantization` sub-skill.
- Classic `ResidualVQ` or `GroupedResidualVQ`: use the `residual-quantizers` sub-skill.
- `FSQ`, `FSP`, residual/grouped FSQ: use the `scalar-quantizers` sub-skill.
- `LFQ`, `ResidualLFQ`, `GroupedResidualLFQ`, `LatentQuantize`, `BinaryMapper`, or `EvoLFQ`: use the `lookup-free-and-latent` sub-skill.

## Start here

1. Pick the API family:
   - one-stage implicit codebook: `SimVQ`;
   - stacked residual implicit codebooks: `ResidualSimVQ`;
   - image feature-map hierarchy: `HierarchicalVQ`.
2. Confirm tensor layout before writing code:
   - `SimVQ` / `ResidualSimVQ` default to channel-last tensors such as `(batch, sequence, dim)`;
   - set `channel_first=True` for feature maps shaped `(batch, dim, height, width)`;
   - `HierarchicalVQ` always expects image feature maps shaped `(batch, channels, height, width)` and requires `accept_image_fmap=True`.
3. Read the detailed references:
   - [API reference](references/api-reference.md) for constructor and return contracts.
   - [Workflows](references/workflows.md) for sequence SimVQ, channel-first residual reconstruction, and hierarchical scale selection.
   - [Troubleshooting](references/troubleshooting.md) for layout, scale, reconstruction, index-list, loss, and implicit-codebook issues.
4. For an environment check, run the bundled helper:

```bash
python sub-skills/sim-and-hierarchical/scripts/smoke_sim_hierarchical.py --help
python sub-skills/sim-and-hierarchical/scripts/smoke_sim_hierarchical.py
```

Run the script from the generated repo-skill root or pass the script path from another working directory after installing `vector-quantize-pytorch` and its base dependencies.
