---
name: residual-quantizers
description: "Operate stacked and grouped residual vector quantizers in
  vector-quantize-pytorch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Residual Quantizers

Use this sub-skill when the task involves stacked residual codebook quantization with `ResidualVQ` or feature-split residual quantization with `GroupedResidualVQ`.

## Route here for

- `ResidualVQ` setup, forward output shapes, `return_all_codes`, `get_output_from_indices`, and saved-index reconstruction.
- Shared or stochastic residual codebooks: `shared_codebook`, `stochastic_sample_codes`, and `sample_codebook_temp`.
- Training-time residual codebook dropout: `quantize_dropout`, cutoff/multiple settings, and why indices can contain `-1`.
- Layer-specific codebook sizes such as `codebook_size=(5, 128, 256)` and inferred quantizer depth.
- Beam-search residual quantization with `beam_size`, `eval_beam_size`, and quantizer score weights.
- DiVeQ residual codebook updates (`diveq=True`) and implicit neural codebooks (`implicit_neural_codebook=True`).
- `GroupedResidualVQ` feature-group splitting, grouped indices, grouped commit losses, and grouped reconstruction.

## Route elsewhere

- Single-stage `VectorQuantize`, multi-headed base VQ, random projection quantizers, codebook health, or manual EMA updates: use the vector-quantization sub-skill.
- `ResidualFSQ` or `GroupedResidualFSQ`: use the scalar-quantizers sub-skill.
- `ResidualLFQ` or `GroupedResidualLFQ`: use the lookup-free-and-latent sub-skill.
- `ResidualSimVQ`: use the sim-and-hierarchical sub-skill.

## Operating sequence

1. Read [API reference](references/api-reference.md) for constructor/forward signatures, exact return tuples, and shape contracts.
2. Read [workflows](references/workflows.md) for common recipes: reconstruction from indices, grouped residual settings, stochastic/shared codebooks, dropout, beam search, DiVeQ, and implicit neural codebooks.
3. Read [troubleshooting](references/troubleshooting.md) before debugging shape, `-1` index, beam-memory, tuple-codebook, or DiVeQ loss behavior.
4. For an installation/runtime smoke check, run `python scripts/smoke_residual_quantizers.py --help` or `python scripts/smoke_residual_quantizers.py` from this sub-skill directory.

## Minimum usage facts

- Default tensor layout is sequence-last-features: input `(batch, sequence, dim)` returns quantized output with the same shape.
- `ResidualVQ` indices normally have shape `(batch, sequence, num_quantizers)`; `GroupedResidualVQ` indices normally have shape `(groups, batch, sequence, num_quantizers)`.
- `get_output_from_indices(indices)` reconstructs quantized outputs from the current model codebooks, not from standalone indices. Save/load the model state together with indices.
- Prefer `.eval()` when generating indices intended for later reconstruction or cross-entropy targets; training dropout can mark skipped residual layers with `-1`.
