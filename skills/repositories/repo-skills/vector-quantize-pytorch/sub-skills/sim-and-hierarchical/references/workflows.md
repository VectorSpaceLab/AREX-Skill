# SimVQ and HierarchicalVQ Workflows

Use these recipes after choosing this sub-skill from the router. They are intentionally tensor-only and do not require training datasets or external example files.

## Workflow 1: one-stage SimVQ for sequence embeddings

Use `SimVQ` when you want an implicit codebook: a frozen codebook buffer transformed into the model dimension by a learned module.

```python
import torch
from vector_quantize_pytorch import SimVQ

sim_vq = SimVQ(
    dim=512,
    codebook_size=1024,
    rotation_trick=True,
)

x = torch.randn(1, 1024, 512)  # (batch, sequence, dim)
quantized, indices, commit_loss = sim_vq(x)

assert quantized.shape == x.shape
assert indices.shape == (1, 1024)
assert torch.isfinite(commit_loss)
assert torch.allclose(quantized, sim_vq.indices_to_codes(indices), atol=1e-6)
```

Training pattern:

```python
reconstruction = decoder(quantized)
reconstruction_loss = loss_fn(reconstruction, target)
loss = reconstruction_loss + commit_loss
loss.backward()
```

Adjust `commitment_weight` when the SimVQ commitment term overwhelms or disappears relative to the reconstruction loss.

## Workflow 2: SimVQ for channel-first image feature maps

Set `channel_first=True` when the embedding dimension is the channel axis.

```python
import torch
from vector_quantize_pytorch import SimVQ

sim_vq = SimVQ(dim=64, codebook_size=256, channel_first=True)
features = torch.randn(2, 64, 8, 8)  # (batch, channels, height, width)

quantized, indices, commit_loss = sim_vq(features)

assert quantized.shape == features.shape
assert indices.shape == (2, 8, 8)
assert sim_vq.indices_to_codes(indices).shape == features.shape
```

This is the correct pattern for convolutional autoencoders that place `SimVQ` between an encoder and decoder.

## Workflow 3: custom implicit codebook transform

Use `codebook_transform` to replace the default linear transform. If the frozen codebook dimension differs from the model dimension, set `frozen_codebook_dim` explicitly.

```python
import torch
from torch import nn
from vector_quantize_pytorch import SimVQ

transform = nn.Sequential(
    nn.Linear(128, 512),
    nn.ReLU(),
    nn.Linear(512, 256),
)

sim_vq = SimVQ(
    dim=256,
    codebook_size=2048,
    frozen_codebook_dim=128,
    codebook_transform=transform,
    init_fn=lambda codes: codes.uniform_(-0.5, 0.5),
    rotation_trick=True,
)

x = torch.randn(4, 128, 256)
quantized, indices, commit_loss = sim_vq(x)
```

Checklist:

- The last dimension of the transform output must equal `dim`.
- The transform input dimension must equal `frozen_codebook_dim`.
- If you save token indices for later decoding, save/restore the trained transform and frozen buffer too.

## Workflow 4: ResidualSimVQ with channel-first reconstruction

Use `ResidualSimVQ` when a single implicit codebook is too coarse and you want stacked residual corrections.

```python
import torch
from vector_quantize_pytorch import ResidualSimVQ

residual_sim_vq = ResidualSimVQ(
    dim=512,
    num_quantizers=4,
    codebook_size=1024,
    channel_first=True,
    rotation_trick=True,
)

x = torch.randn(1, 512, 32, 32)
quantized, indices, losses = residual_sim_vq(x)
reconstructed = residual_sim_vq.get_output_from_indices(indices)

assert quantized.shape == x.shape
assert indices.shape == (1, 32, 32, 4)
assert losses.shape == (4,)
assert torch.allclose(quantized, reconstructed, atol=1e-5)

loss = downstream_reconstruction_loss + losses.sum()
```

Notes:

- `heads` is present in the constructor but must stay `1`.
- The third return is per-quantizer loss, not a single scalar in general.
- Keep the module in eval mode or disable quantize dropout for deterministic reconstruction tests.

## Workflow 5: ResidualSimVQ with quantize dropout

Quantize dropout trains the model to tolerate coarser residual stacks.

```python
residual_sim_vq = ResidualSimVQ(
    dim=256,
    num_quantizers=8,
    codebook_size=512,
    quantize_dropout=True,
    quantize_dropout_cutoff_index=2,
    quantize_dropout_multiple_of=2,
)

residual_sim_vq.train()
quantized, indices, losses = residual_sim_vq(torch.randn(2, 128, 256))

# Dropped quantizers are encoded as -1 and produce zero contribution during reconstruction.
coarse_or_full = residual_sim_vq.get_output_from_indices(indices)
```

When storing indices from a dropout-trained model, keep the final quantizer axis and preserve `-1` values. Do not replace them with a real code index.

## Workflow 6: choose HierarchicalVQ scales for small feature maps

Use `HierarchicalVQ` when quantizing image feature maps at multiple square scales. A safe scale list is sorted, positive, and ends at the latent feature-map size.

```python
import torch
from vector_quantize_pytorch import HierarchicalVQ

# Example: a convolutional encoder maps an image to a 7x7 latent feature map.
hq = HierarchicalVQ(
    dim=32,
    codebook_size=128,
    accept_image_fmap=True,
    scales=(1, 2, 4, 7),
    quant_resi=0.5,
    share_quant_resi=1,
)

x = torch.randn(1, 32, 7, 7)
quantized, index_list, commit_loss = hq(x)
reconstructed = hq.get_output_from_indices(index_list)

assert quantized.shape == x.shape
assert len(index_list) == 4
assert [tuple(ind.shape) for ind in index_list] == [(1, 1, 1), (1, 2, 2), (1, 4, 4), (1, 7, 7)]
assert reconstructed.shape == x.shape
assert torch.isfinite(commit_loss)
```

For very small feature maps, prefer scale schedules such as:

| Feature map | Suggested `scales` | Why |
|---|---|---|
| `4 x 4` | `(1, 2, 4)` | coarse-to-full with valid index reconstruction |
| `7 x 7` | `(1, 2, 4, 7)` | matches the package's tested pattern |
| `8 x 8` | `(1, 2, 4, 8)` | power-of-two pyramid ending at full size |
| `16 x 16` | `(1, 2, 4, 8, 16)` or a shorter subset ending in `16` | trade off index count and compute |

The forward pass can upsample from each scale to the actual input size, but `get_output_from_indices` reconstructs to `scales[-1] x scales[-1]`. If exact index-only reconstruction shape matters, make `height == width == scales[-1]`.

## Workflow 7: HierarchicalVQ inside an autoencoder

A convolutional autoencoder usually places `HierarchicalVQ` after downsampling and before upsampling.

```python
import torch
from torch import nn
from vector_quantize_pytorch import HierarchicalVQ, Sequential

model = Sequential(
    nn.Conv2d(1, 16, kernel_size=3, padding=1),
    nn.MaxPool2d(2),
    nn.GELU(),
    nn.Conv2d(16, 32, kernel_size=3, padding=1),
    nn.MaxPool2d(2),  # 28x28 input becomes 7x7 latent features
    HierarchicalVQ(
        dim=32,
        codebook_size=512,
        accept_image_fmap=True,
        scales=(1, 2, 4, 7),
        quant_resi=0.5,
        share_quant_resi=1,
        kmeans_init=True,
    ),
    nn.Upsample(scale_factor=2, mode="nearest"),
    nn.Conv2d(32, 16, kernel_size=3, padding=1),
    nn.GELU(),
    nn.Upsample(scale_factor=2, mode="nearest"),
    nn.Conv2d(16, 1, kernel_size=3, padding=1),
)

x = torch.randn(8, 1, 28, 28)
out, indices, commit_loss = model(x)
loss = (out - x).abs().mean() + 10.0 * commit_loss
```

For smoke tests or tiny synthetic batches, set `kmeans_init=False` to avoid data-dependent initialization dominating the check.

## Decision checklist before implementation

- Is the data sequence-like with embedding dimension last? Use default `SimVQ` or `ResidualSimVQ`.
- Is the data a convolutional feature map? Use `channel_first=True` for SimVQ variants, or `HierarchicalVQ` for multi-scale image quantization.
- Do you need stored indices to reconstruct later? Save the model state and check the reconstruction helper immediately after encoding.
- Do you need multiple residual layers? Use `ResidualSimVQ`, not classic `ResidualVQ`, only if the implicit/frozen SimVQ codebook is part of the design.
- Do you need scalar, binary, lookup-free, or latent quantization? Route out to the matching sibling sub-skill.
