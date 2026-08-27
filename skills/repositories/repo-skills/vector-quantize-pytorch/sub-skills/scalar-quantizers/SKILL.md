---
name: scalar-quantizers
description: "Operate FSQ, FSP, ResidualFSQ, and GroupedResidualFSQ scalar
  quantizers in vector-quantize-pytorch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Scalar Quantizers

Use this sub-skill when a task needs scalar discretization in `vector-quantize-pytorch`: finite scalar quantization, finite scalar perturbation, residual scalar quantizers, grouped residual scalar quantizers, index roundtrips, tensor-layout decisions, or scalar-quantizer troubleshooting.

## Route here for

- `FSQ` setup with `levels`, `dim`, `num_codebooks`, `return_indices`, `channel_first`, `preserve_symmetry`, `bound_hard_clamp`, `orthogonal_rotation`, projections, and index conversion.
- `FSP` setup with `levels`, `dim`, `channel_first`, `act_name`, `quantize_rate`, `need_inv_act`, `vector_norm`, four-value return tuples, stochastic training perturbation, and eval-time roundtrips.
- `ResidualFSQ` and `GroupedResidualFSQ` for residual stacks, grouped feature splits, `num_quantizers`, residual reconstruction from indices, `return_all_codes`, and quantize-dropout caveats.
- Debugging shape, dtype, projection, activation, norm, and exact-vs-allclose reconstruction issues in scalar quantizers.

## Route elsewhere

- Use the top-level skill to choose package installation and overall routing.
- Use `../vector-quantization/` for learned codebook `VectorQuantize`, `RandomProjectionQuantizer`, codebook EMA, masks, and top-k/manual EMA updates.
- Use `../residual-quantizers/` for `ResidualVQ` and `GroupedResidualVQ` learned-codebook residual workflows.
- Use `../lookup-free-and-latent/` for `LFQ`, `ResidualLFQ`, `GroupedResidualLFQ`, `LatentQuantize`, binary entropy losses, and lookup-free/latent quantization.
- Use `../sim-and-hierarchical/` for `SimVQ`, `ResidualSimVQ`, and `HierarchicalVQ`.

## Required references

Read these bundled references before implementing or debugging a scalar workflow:

1. [`references/api-reference.md`](references/api-reference.md) for constructor signatures, return tuples, shape contracts, index helpers, projections, and dtype behavior.
2. [`references/workflows.md`](references/workflows.md) for safe FSQ/FSP/residual recipes and code patterns.
3. [`references/troubleshooting.md`](references/troubleshooting.md) for common errors, unsupported settings, roundtrip caveats, and precision/layout fixes.

## Safe smoke helper

Run the bundled helper when you need a quick CPU sanity check of the installed package and the scalar APIs:

```bash
python scripts/smoke_scalar_quantizers.py --help
python scripts/smoke_scalar_quantizers.py
```

The helper uses small random tensors only. It does not download datasets, train MNIST models, or depend on any source tree.

## Operating cautions

- FSQ returns exactly two values: `(quantized, indices)`. If `return_indices=False`, the second value is `None` and index roundtrip helpers are unavailable for that instance.
- FSP returns exactly four values: `(quantized, indices, norm_loss, other_info)`.
- Prefer eval mode and `torch.allclose` for reconstruction checks that involve FSP, projections, autocast, or low precision. Exact equality is reliable only for the narrow deterministic cases called out in the API reference.
- For image-like tensors, confirm whether the class expects channel-first handling. FSQ treats 4D+ inputs as channel-first feature maps; FSP requires `channel_first=True` for NCHW-style inputs.
