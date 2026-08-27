# Residual Quantizers Workflows

These recipes are safe CPU-oriented patterns for `ResidualVQ` and `GroupedResidualVQ`. They are self-contained and use only the installed package API.

## 1. Basic residual VQ forward pass

Use this when a continuous sequence should be represented by multiple residual codebook indices per token.

```python
import torch
from vector_quantize_pytorch import ResidualVQ

residual_vq = ResidualVQ(
    dim=256,
    num_quantizers=8,
    codebook_size=1024,
)

x = torch.randn(1, 1024, 256)
quantized, indices, commit_loss = residual_vq(x)

assert quantized.shape == x.shape
assert indices.shape == (1, 1024, 8)
```

Operational notes:

- Use `num_quantizers` as bitrate/depth: more residual layers usually improve reconstruction but increase index storage and compute.
- Use `codebook_dim` when the residual code vector width should differ from public `dim`; the module projects in/out for you.
- `commit_loss` is one loss vector over residual layers after internal reduction in common modes. Reduce it deliberately in your training objective rather than assuming a scalar.

## 2. Return all layer codes

Use `return_all_codes=True` when a downstream task needs per-residual-layer code vectors.

```python
quantized, indices, commit_loss, all_codes = residual_vq(
    x,
    return_all_codes=True,
)

# all_codes: (num_quantizers, batch, sequence, codebook_dim)
assert all_codes.shape[:3] == (8, 1, 1024)
```

`all_codes` are the codebook vectors before the residual stack sums them and before any output projection back to `dim`.

## 3. Reconstruct from saved indices in eval mode

Use this pattern when indices are saved to disk and later decoded by the same model state.

```python
residual_vq.eval()
with torch.no_grad():
    quantized, indices, _ = residual_vq(x)
    reconstructed = residual_vq.get_output_from_indices(indices)

assert torch.allclose(quantized, reconstructed, atol=1e-5)
```

Checklist:

1. Save the model state dict, quantizer constructor configuration, and package version with the indices.
2. Restore the same model state before calling `get_output_from_indices`.
3. Generate indices in `.eval()` when they will become reconstruction targets or cross-entropy labels.
4. Avoid target-index loss mode with indices containing `-1`; those are dropout markers, not class labels.

## 4. Heterogeneous layer codebook sizes

Use a tuple for `codebook_size` when residual layers should have different vocabularies.

```python
from vector_quantize_pytorch import ResidualVQ

# Three residual layers: sizes 5, 128, and 256.
residual_vq = ResidualVQ(
    dim=2,
    codebook_size=(5, 128, 256),
)

x = torch.randn(2, 2, 2)
quantized, indices, _ = residual_vq(x, freeze_codebook=True)
assert indices.shape == (2, 2, 3)
```

Do not combine non-uniform tuple sizes with `shared_codebook=True`; shared codebooks require a single uniform codebook size across all residual layers.

## 5. Shared stochastic residual codebook

This is the RQ-VAE-style setup: all layers share a codebook, and training samples codes stochastically.

```python
residual_vq = ResidualVQ(
    dim=256,
    num_quantizers=8,
    codebook_size=1024,
    shared_codebook=True,
    stochastic_sample_codes=True,
    sample_codebook_temp=0.1,
)

quantized, indices, commit_loss = residual_vq(x)
```

Guidance:

- `shared_codebook=True` coordinates codebook updates after the residual stack, so keep all codebook sizes identical.
- Lower `sample_codebook_temp` is more deterministic. `0` is equivalent to nearest-code selection.
- You can override temperature per call: `residual_vq(x, sample_codebook_temp=0.05)`.

## 6. Quantize dropout for variable residual depth

Quantize dropout trains a stack to remain useful if later residual layers are omitted.

```python
residual_vq = ResidualVQ(
    dim=256,
    num_quantizers=8,
    codebook_size=1024,
    quantize_dropout=True,
    quantize_dropout_cutoff_index=1,
    quantize_dropout_multiple_of=1,
)

residual_vq.train()
quantized, indices, commit_loss = residual_vq(x)

# Later residual layers may be skipped.
may_have_skipped_layers = (indices == -1).any().item()
```

Use `.eval()` to produce full-depth indices for deterministic reconstruction. If you intentionally decode coarse indices, keep `quantize_dropout=True` on the model; `get_output_from_indices` can treat missing or `-1` layers as zero contribution.

## 7. Beam search residual quantization

Use beam search when greedy per-layer nearest-code selection is too myopic.

```python
residual_vq = ResidualVQ(
    dim=256,
    codebook_dim=128,
    num_quantizers=8,
    codebook_size=1024,
    quantize_dropout=True,
    beam_size=2,
    eval_beam_size=3,
)

quantized, indices, commit_loss = residual_vq(x)
```

Practical rules:

- `beam_size > 1` enables beam search. `beam_size=None` or `1` uses greedy residual quantization.
- `eval_beam_size` is allowed only when `beam_size` is set; it defaults to `beam_size`.
- Keep beam sizes small first. Runtime and memory grow with `beam_size`, sequence length, residual depth, and codebook size.
- If some residual layers matter more, set `beam_score_quantizer_weights` to a list with one weight per quantizer.

## 8. DiVeQ residual codebook learning

Use DiVeQ when codebooks should be learned by gradient updates rather than EMA or commitment/auxiliary losses.

```python
residual_vq = ResidualVQ(
    dim=256,
    num_quantizers=4,
    codebook_size=256,
    diveq=True,
)

residual_vq.train()
quantized, indices, commit_loss = residual_vq(x)
loss = downstream_loss(quantized)
loss.backward()
```

DiVeQ changes the training contract:

- Codebooks become learnable parameters.
- EMA updates are disabled.
- Commitment weight is set to `0`.
- `quant_grad_frac` is forced to `1.0`.
- Expect codebook learning through gradients from the downstream objective, not through EMA or commitment auxiliary loss.

## 9. Implicit neural codebooks

Use this when each residual layer after the first should transform its codebook conditioned on the current quantized output.

```python
residual_vq = ResidualVQ(
    dim=32,
    num_quantizers=8,
    codebook_size=128,
    implicit_neural_codebook=True,
    mlp_kwargs={"depth": 2, "dim_hidden": 64},
)

quantized, indices, commit_loss = residual_vq(x)
```

Guidance:

- Start with small tensors and codebooks; implicit codebooks add per-layer MLP computation.
- EMA is disabled and codebooks are learnable.
- If using cosine similarity, the internal MLP output is normalized to match the codebook behavior.

## 10. Grouped residual VQ for feature splits

Use `GroupedResidualVQ` when different chunks of the feature dimension should have separate residual stacks.

```python
from vector_quantize_pytorch import GroupedResidualVQ

grouped_vq = GroupedResidualVQ(
    dim=256,
    groups=2,
    num_quantizers=8,
    codebook_size=1024,
)

x = torch.randn(1, 1024, 256)
quantized, indices, commit_loss = grouped_vq(x)

assert quantized.shape == x.shape
assert indices.shape == (2, 1, 1024, 8)
```

Grouped reconstruction keeps the leading group axis:

```python
grouped_vq.eval()
with torch.no_grad():
    quantized, indices, _ = grouped_vq(x)
    reconstructed = grouped_vq.get_output_from_indices(indices)

assert torch.allclose(quantized, reconstructed, atol=1e-5)
```

Design rules:

- `dim` must be divisible by `groups`.
- Each group receives `dim // groups` channels/features and its own `ResidualVQ` instance.
- If `return_all_codes=True`, the fourth output is a tuple of per-group all-code tensors; do not assume it is a single stacked tensor.
- For image feature maps with `accept_image_fmap=True`, groups split the channel dimension instead of the last dimension.

## 11. Tiny runtime smoke check

From this sub-skill directory:

```bash
python scripts/smoke_residual_quantizers.py --help
python scripts/smoke_residual_quantizers.py
```

The smoke helper runs small CPU checks for `ResidualVQ`, `GroupedResidualVQ`, eval reconstruction, tuple codebook sizes, and dropout marker behavior.
