# Lookup-Free and Latent Workflows

These workflows are self-contained package usage patterns. They assume `torch` and `vector-quantize-pytorch` are installed.

## 1. Choose the family

| Need | Prefer | Why |
|---|---|---|
| Binary lookup-free quantization with entropy/diversity regularization | `LFQ` | No learned embedding lookup; codes are signs/bits and indices are bit-packed. |
| Stacked binary residual quantization | `ResidualLFQ` | Multiple LFQ layers quantize residuals and support reconstruction from stacked indices. |
| Grouped residual binary quantization | `GroupedResidualLFQ` | Splits features into groups before residual LFQ, useful for independent channels or grouped audio features. |
| Per-dimension latent levels with optional learnable scalar values | `LatentQuantize` | Each latent dimension is quantized to configured level values. |
| Sample discrete binary codes from logits | `BinaryMapper` | Converts bit logits into one-hot categorical codes and optional indices. |
| Encoder/LFQ/decoder wrapper plus genetic latent search utilities | `EvoLFQ` | Adds a model wrapper and binary population search helpers around LFQ. |

## 2. LFQ for sequences

Use `(batch, seq, dim)` for rank-3 sequence tensors.

```python
import torch
from vector_quantize_pytorch import LFQ

lfq = LFQ(
    dim=8,
    codebook_size=256,          # log2(256) == 8
    entropy_loss_weight=0.1,
    diversity_gamma=1.0,
)

x = torch.randn(2, 16, 8)
quantized, indices, aux_loss = lfq(x, inv_temperature=100.0)

assert quantized.shape == x.shape
assert indices.shape == (2, 16)
assert torch.allclose(quantized, lfq.indices_to_codes(indices))
```

Use a boolean sequence mask only for training-time entropy and commitment loss:

```python
mask = torch.ones(2, 16, dtype=torch.bool)
mask[:, -4:] = False
(ret, breakdown) = lfq(x, mask=mask, return_loss_breakdown=True)
quantized, indices, aux_loss = ret
```

## 3. LFQ for images, video, and multiple codebooks

Rank-4 and rank-5 LFQ inputs default to channel-first layout. The feature axis is the second dimension.

```python
import torch
from vector_quantize_pytorch import LFQ

lfq = LFQ(
    dim=16,
    codebook_size=4096,         # log2(4096) == 12
    num_codebooks=2,            # internal binary width 24, so projections are used
    entropy_loss_weight=0.02,
)

image = torch.randn(1, 16, 8, 8)
quantized, indices, aux_loss = lfq(image)

assert quantized.shape == image.shape
assert indices.shape == (1, 8, 8, 2)
assert lfq.indices_to_codes(indices).shape == image.shape

video = torch.randn(1, 16, 3, 8, 8)
quantized_video, video_indices, _ = lfq(video)
assert quantized_video.shape == video.shape
assert video_indices.shape == (1, 3, 8, 8, 2)
```

If you do not want projections, choose `dim == log2(codebook_size) * num_codebooks`.

## 4. ResidualLFQ roundtrip from indices

```python
import torch
from vector_quantize_pytorch import ResidualLFQ

residual_lfq = ResidualLFQ(
    dim=32,
    codebook_size=256,
    num_quantizers=4,
)
residual_lfq.eval()

x = torch.randn(2, 64, 32)
quantized, indices, losses = residual_lfq(x)
reconstructed = residual_lfq.get_output_from_indices(indices)

assert quantized.shape == x.shape
assert indices.shape == (2, 64, 4)
assert losses.shape[-1] == 4
assert torch.allclose(quantized, reconstructed)
```

When `quantize_dropout=True`, training can fill dropped future quantizers with `-1`. Preserve those indices if you plan to reconstruct a coarse representation later.

## 5. GroupedResidualLFQ for split feature groups

```python
import torch
from vector_quantize_pytorch import GroupedResidualLFQ

model = GroupedResidualLFQ(
    dim=32,
    groups=4,
    codebook_size=256,
    num_quantizers=2,
)
model.eval()

x = torch.randn(2, 20, 32)
quantized, indices, losses = model(x)
reconstructed = model.get_output_from_indices(indices)

assert quantized.shape == x.shape
assert indices.shape == (4, 2, 20, 2)     # groups first
assert torch.allclose(quantized, reconstructed)
```

For image feature maps, set `accept_image_fmap=True` and pass `(batch, channels, height, width)` with `channels == dim`.

## 6. LatentQuantize for channel-first image/video/series tensors

LatentQuantize uses `(batch, dim, ...)` even for 1D series. If your sequence is `(batch, seq, dim)`, transpose before and after the quantizer.

```python
import torch
from vector_quantize_pytorch import LatentQuantize

latent_q = LatentQuantize(
    levels=[5, 5, 8],
    dim=16,
    commitment_loss_weight=0.1,
    quantization_loss_weight=0.1,
)

image = torch.randn(1, 16, 8, 8)
quantized, indices, loss = latent_q(image)

assert quantized.shape == image.shape
assert indices.shape == (1, 8, 8)
assert torch.allclose(quantized, latent_q.indices_to_codes(indices))

series = torch.randn(1, 16, 64)
quantized_series, series_indices, _ = latent_q(series)
assert quantized_series.shape == series.shape
assert series_indices.shape == (1, 64)
```

For multi-codebook LatentQuantize:

```python
latent_q = LatentQuantize(
    levels=[4, 8, 16],
    dim=9,
    num_codebooks=3,
)

x = torch.randn(2, 9, 5)
quantized, indices, loss = latent_q(x)

assert quantized.shape == x.shape
assert indices.shape == (2, 5, 3)
assert loss.ndim == 0
```

When all codebook dimensions should share the same number of levels, use an integer `levels` and set `codebook_dim` explicitly:

```python
latent_q = LatentQuantize(levels=5, dim=6, codebook_dim=3, num_codebooks=2)
x = torch.randn(2, 6, 10)
quantized, indices, loss = latent_q(x)
assert indices.shape == (2, 10, 2)
```

## 7. BinaryMapper for bit logits

```python
import torch
from vector_quantize_pytorch import BinaryMapper

mapper = BinaryMapper(bits=4, deterministic_on_eval=True)
logits = torch.randn(3, 7, 4)

mapper.eval()
one_hot, indices, aux_loss = mapper(
    logits,
    deterministic=True,
    calc_aux_loss=True,
    return_indices=True,
    reduce_aux_kl_loss=False,
)

assert one_hot.shape == (3, 7, 16)
assert indices.shape == (3, 7)
assert aux_loss.shape == (3, 7)
assert mapper.log_prob(logits, indices=indices).shape == (3, 7)
assert torch.allclose(
    mapper.log_prob(logits, indices=indices),
    mapper.log_prob(logits, one_hot=one_hot),
)
```

## 8. EvoLFQ minimal encoder/decoder wrapper

EvoLFQ is safe to construct and run with tiny modules. Full training and evolution loops are separate workloads.

```python
import torch
from torch import nn
from vector_quantize_pytorch import EvoLFQ

class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Linear(6, 4)

    def forward(self, x):
        return self.net(x)       # (batch, dim), accepted by EvoLFQ

class Decoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Linear(4, 6)

    def forward(self, codes):
        return self.net(codes)   # receives quantized latent, not original input

model = EvoLFQ(
    encoder=Encoder(),
    decoder=Decoder(),
    codebook_size=4,             # log2(4) == 2
    num_codebooks=2,             # internal LFQ width == 4
    pop_size=4,
    elitism_count=1,
    generations=1,
)

x = torch.randn(2, 6)
reconstructed, indices, aux_loss = model(x)
assert reconstructed.shape == x.shape
assert indices.shape == (2, 2)
```

To test genetic utilities without a long run, use one generation and a tiny population:

```python
model.eval()

def fitness_fn(decoded, bits):
    return -decoded.square().mean(dim=-1)

population = model.init_random_population(pop_size=4, shape=(4,))
result = next(model.evolve(fitness_fn, pop_bits=population, generations=1))
assert result.pop_bits.shape == population.shape
```

## 9. Run the bundled smoke helper

From this sub-skill directory, run:

```bash
python scripts/smoke_lookup_free_latent.py
python scripts/smoke_lookup_free_latent.py --skip-evo
```

The script avoids dataset downloads, training loops, and optional example dependencies.
