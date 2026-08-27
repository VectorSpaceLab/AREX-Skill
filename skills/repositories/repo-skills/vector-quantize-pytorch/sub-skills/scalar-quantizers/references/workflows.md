# Scalar Quantizer Workflows

Use these recipes as starting points for safe package usage. They assume `torch` and `vector_quantize_pytorch` are installed and use small in-memory tensors only.

## Choose the scalar quantizer family

| Need | Use | Why |
|---|---|---|
| Simple codebook-free scalar rounding with straight-through gradients | `FSQ` | Minimal outputs, no auxiliary losses, exact index roundtrip in deterministic no-projection cases |
| Scalar perturbation during training plus deterministic eval bins | `FSP` | Returns `norm_loss` and diagnostic info; useful when stochastic perturbation is desired during learning |
| Multi-stage residual scalar quantization | `ResidualFSQ` | Stacks several FSQ stages and reconstructs by summing residual codes |
| Split features into independent residual scalar groups | `GroupedResidualFSQ` | Runs one residual scalar stack per feature group and stacks group indices |

Route lookup-free binary quantization and latent quantization to the lookup-free/latent sub-skill, not here.

## FSQ sequence roundtrip

Use this for a simple `(batch, sequence, dim)` tensor where `dim == len(levels)`.

```python
import torch
from vector_quantize_pytorch import FSQ

levels = [8, 5, 5, 5]
fsq = FSQ(levels)

x = torch.randn(1, 16, len(levels))
quantized, indices = fsq(x)

assert quantized.shape == x.shape
assert indices.shape == x.shape[:2]
assert torch.equal(quantized, fsq.indices_to_codes(indices))
```

If you set `return_indices=False`, keep the two-value unpacking but expect `indices is None`:

```python
fsq = FSQ([8, 5, 5, 5], return_indices=False)
quantized, indices = fsq(torch.randn(1, 16, 4))
assert indices is None
```

Do not call `indices_to_codes` on that instance unless indices were returned by another compatible FSQ with the same levels, projection, and layout settings.

## FSQ with projections and multiple codebooks

When `dim` differs from `len(levels) * num_codebooks`, FSQ learns projection layers. Multiple scalar codebooks keep an extra index axis.

```python
import torch
from vector_quantize_pytorch import FSQ

fsq = FSQ(
    levels=[4, 4],
    dim=6,
    num_codebooks=2,
)

x = torch.randn(2, 8, 6)
quantized, indices = fsq(x)
reconstructed = fsq.indices_to_codes(indices)

assert fsq.has_projections
assert quantized.shape == x.shape
assert indices.shape == (2, 8, 2)
assert reconstructed.shape == x.shape
assert torch.allclose(quantized, reconstructed)
```

Use `torch.allclose` instead of exact equality when projections or low precision are involved.

## FSQ channel-first image or feature map

FSQ treats 4D and higher inputs as channel-first feature maps. Set `dim` to the channel count.

```python
import torch
from vector_quantize_pytorch import FSQ

fsq = FSQ(levels=[4, 4, 4], dim=3, channel_first=True)
x = torch.randn(2, 3, 8, 8)
quantized, indices = fsq(x)

assert quantized.shape == x.shape
assert indices.shape == (2, 8, 8)
assert fsq.indices_to_codes(indices).shape == x.shape
```

For lower-rank channel-first tensors such as `(B, D, N)`, set `channel_first=True`; otherwise FSQ expects the feature dimension at the end.

## FSP training and eval pattern

FSP returns four values and behaves differently in training and eval.

```python
import torch
from vector_quantize_pytorch import FSP

fsp = FSP(
    levels=[8, 5, 5, 5],
    act_name="normal",
    quantize_rate=0.5,
    vector_norm="var",
)

x = torch.randn(1, 16, 4)
quantized, indices, norm_loss, other_info = fsp(x)

assert quantized.shape == x.shape
assert indices.shape == x.shape[:2]
assert norm_loss.ndim == 0
assert "level_indices" in other_info
```

During training, `quantize_rate < 1.0` can perturb the activated scalar values, so the forward output may not be exactly recoverable from `indices`. Use eval mode for deterministic index roundtrips:

```python
fsp.eval()
with torch.no_grad():
    quantized, indices, _, _ = fsp(torch.randn(1, 16, 4))
    recovered = fsp.indices_to_codes(indices)

assert torch.allclose(quantized, recovered, atol=1e-5)
```

## FSP index encoding and projections

Use level-index helpers when you need to inspect or store factorized scalar coordinates.

```python
import torch
from vector_quantize_pytorch import FSP

fsp = FSP(levels=[8, 5, 5, 5], dim=8)
fsp.eval()

level_indices = torch.tensor([[[7, 4, 4, 4]]])
flat = fsp.level_indices_to_indices(level_indices)
assert flat.item() == 999
assert torch.equal(fsp.indices_to_level_indices(flat), level_indices)

x = torch.randn(1, 8, 8)
quantized, indices, _, _ = fsp(x)
recovered = fsp.indices_to_codes(indices)
assert recovered.shape == x.shape
assert torch.allclose(quantized, recovered, atol=1e-4)
```

For NCHW images, set `channel_first=True`:

```python
fsp = FSP(levels=[8, 5, 5, 5], dim=4, channel_first=True)
fsp.eval()

x = torch.randn(2, 4, 8, 8)
quantized, indices, _, _ = fsp(x)
assert quantized.shape == x.shape
assert indices.shape == (2, 8, 8)
assert torch.allclose(quantized, fsp.indices_to_codes(indices), atol=1e-5)
```

## Tiny FSP training step

When checking gradient flow, unpack FSP manually instead of placing it inside `torch.nn.Sequential` without a wrapper, because it returns a tuple.

```python
import torch
from vector_quantize_pytorch import FSP

encoder = torch.nn.Linear(8, 8)
fsp = FSP(levels=[4, 4], dim=8, quantize_rate=0.5, vector_norm="none")
decoder = torch.nn.Linear(8, 8)

x = torch.randn(2, 4, 8, requires_grad=True)
h = encoder(x)
quantized, indices, norm_loss, _ = fsp(h)
out = decoder(quantized)
loss = out.square().mean() + norm_loss
loss.backward()

assert x.grad is not None
assert torch.isfinite(x.grad).all()
```

## ResidualFSQ reconstruction from indices

Use eval mode for deterministic residual reconstruction checks.

```python
import torch
from vector_quantize_pytorch import ResidualFSQ

residual_fsq = ResidualFSQ(
    dim=8,
    levels=[4, 4],
    num_quantizers=3,
)
residual_fsq.eval()

x = torch.randn(1, 12, 8)
quantized, indices = residual_fsq(x)
recovered = residual_fsq.get_output_from_indices(indices)

assert quantized.shape == x.shape
assert indices.shape == (1, 12, 3)
assert torch.allclose(quantized, recovered)
```

If you need all per-stage residual codes:

```python
quantized, indices, all_codes = residual_fsq(x, return_all_codes=True)
assert all_codes.shape == (3, 1, 12, 2)  # num_quantizers, batch, sequence, len(levels)
```

## GroupedResidualFSQ sequence workflow

Use grouped residual scalar quantization when the feature dimension can be split cleanly into independent groups.

```python
import torch
from vector_quantize_pytorch import GroupedResidualFSQ

grouped = GroupedResidualFSQ(
    dim=8,
    groups=2,
    levels=[4, 4],
    num_quantizers=2,
)
grouped.eval()

x = torch.randn(1, 12, 8)
quantized, indices = grouped(x)
recovered = grouped.get_output_from_indices(indices)

assert quantized.shape == x.shape
assert indices.shape == (2, 1, 12, 2)  # groups, batch, sequence, quantizers
assert torch.allclose(quantized, recovered)
```

For image feature maps, prefer flattening to sequence layout unless you have already validated the `accept_image_fmap=True` path for the exact package version and tensor layout:

```python
# NCHW -> sequence -> NCHW, avoiding image-map grouped axis ambiguity.
b, c, h, w = 2, 8, 4, 4
x_img = torch.randn(b, c, h, w)
x_seq = x_img.permute(0, 2, 3, 1).reshape(b, h * w, c)

quantized_seq, indices = grouped(x_seq)
quantized_img = quantized_seq.reshape(b, h, w, c).permute(0, 3, 1, 2)
assert quantized_img.shape == x_img.shape
```

## Safe smoke command

From this sub-skill directory, run:

```bash
python scripts/smoke_scalar_quantizers.py
```

Run a narrower case while debugging:

```bash
python scripts/smoke_scalar_quantizers.py --case fsq
python scripts/smoke_scalar_quantizers.py --case fsp
python scripts/smoke_scalar_quantizers.py --case residual
```
