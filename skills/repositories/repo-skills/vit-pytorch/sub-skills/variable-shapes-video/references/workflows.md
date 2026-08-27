# Workflows: Variable Shapes, N-D Tensors, and Video

## Purpose

Read this reference when routing or implementing vit-pytorch workflows that are not ordinary fixed-size 2D image classifiers: variable-resolution NaViT batches, nested tensor NaViT, 1D time/sequence models, 3D/video models, N-D tensor models, and image-model wrappers that accept video.

Evidence comes from the package README examples for NaViT, 3D ViT, SimpleViT 3D, CCT 3D, ViViT, and non-square image FAQ guidance, plus the source modules named in each section and installed-package signature/import probes.

## Quick routing table

| User asks about | Use | Input layout | Key checks |
| --- | --- | --- | --- |
| Variable-resolution images, max token budget, grouped batches | `vit_pytorch.na_vit.NaViT` | `List[Tensor]` with `group_images=True`, or manual `List[List[Tensor]]`; each tensor `(channels, height, width)` | `height % patch_size == 0`, `width % patch_size == 0`, image no larger than configured position grid, per-group tokens fit attention budget |
| Nested tensor variable images | `vit_pytorch.na_vit_nested_tensor.NaViT` | Flat `List[Tensor]`, each `(channels, height, width)` | PyTorch nested/jagged support, patch divisibility, flat list not grouped list |
| Nested tensor variable volumes/videos | `vit_pytorch.na_vit_nested_tensor_3d.NaViT` | Flat `List[Tensor]`, each `(channels, frames, height, width)` | PyTorch nested/jagged support, `frames <= max_frames`, `frames % frame_patch_size == 0`, spatial divisibility |
| Plain 3D/video ViT | `vit_pytorch.vit_3d.ViT` | `(batch, channels, frames, height, width)` | `frames % frame_patch_size == 0`, spatial dimensions divisible by `image_patch_size` |
| Simple 3D/video ViT | `vit_pytorch.simple_vit_3d.SimpleViT` | `(batch, channels, frames, height, width)` | Same as 3D ViT; uses sin-cos 3D positions and mean pooling |
| 3D CCT | `vit_pytorch.cct_3d.CCT` | `(batch, channels, frames, height, width)` | Match actual input size to `img_size`/`num_frames` when using positional embeddings; convolution/pooling changes sequence length |
| ViViT video transformer | `vit_pytorch.vivit.ViViT` | `(batch, channels, frames, height, width)` | `variant` in `factorized_encoder` or `factorized_self_attention`; self-attention variant requires equal spatial/temporal depth |
| ViViT with MOSS | `vit_pytorch.vivit_with_moss.ViViT` | `(batch, channels, frames, height, width)` | MOSS local sizes should be odd; causal MOSS cannot receive `mask` |
| Wrap an image model over frames | `vit_pytorch.accept_video_wrapper.AcceptVideoWrapper` | Wrapper input `(batch, channels, time, height, width)`; inner image model sees `(batch*time, channels, height, width)` | `time_seq_len` if adding time pos emb; image net output structure and chosen output position; patch-token count if using MOSS |
| 1D series | `vit_pytorch.vit_1d.ViT` or `vit_pytorch.simple_vit_1d.SimpleViT` | `(batch, channels, seq_len)` | `seq_len % patch_size == 0` |
| Generic N-D tensors | `vit_pytorch.vit_nd.ViTND`, `vit_pytorch.vit_nd_pope.ViTND`, `vit_pytorch.vit_nd_rotary.ViTND` | `(batch, channels, *input_shape)` | `1 <= ndim <= 7`, tuple lengths match `ndim`, every input dimension divisible by its patch dimension |

## NaViT variable-resolution image batches

`vit_pytorch.na_vit.NaViT` is the standard route for mixed image sizes and aspect ratios in one forward pass.

### Constructor and positions

Use:

```python
from vit_pytorch.na_vit import NaViT

model = NaViT(
    image_size = 256,
    patch_size = 32,
    num_classes = 1000,
    dim = 1024,
    depth = 6,
    heads = 16,
    mlp_dim = 2048,
    dropout = 0.1,
    emb_dropout = 0.1,
    token_dropout_prob = 0.1,
)
```

Important details:

- `image_size` may be an integer or `(height, width)` pair. It defines the maximum factorized height/width position tables: `image_size // patch_size` positions per axis.
- Every input image must be `(channels, height, width)`, not `(batch, channels, height, width)`.
- Height and width must each be divisible by `patch_size`.
- The README FAQ allows non-square images as long as height and width are less than or equal to the configured `image_size` and divisible by `patch_size`.
- An image larger than the configured `image_size` can pass early divisibility checks but later fail when position indices exceed the height or width position table.

### Manual grouping

Manual grouping passes `List[List[Tensor]]`: each inner list is one packed attention batch element, and all images inside that inner list can attend only within their own image id mask.

```python
images = [
    [torch.randn(3, 256, 256), torch.randn(3, 128, 128)],
    [torch.randn(3, 128, 256), torch.randn(3, 256, 128)],
    [torch.randn(3, 64, 256)],
]

logits = model(images)  # one row per image, in group order then inner-list order
```

Use manual grouping when the data loader already batches images under a known token budget. The model does not sort or rebalance manual groups for you.

### Auto grouping by max sequence length

Auto grouping passes a flat `List[Tensor]` and sets `group_images=True`:

```python
flat_images = [
    torch.randn(3, 256, 256),
    torch.randn(3, 128, 128),
    torch.randn(3, 128, 256),
    torch.randn(3, 256, 128),
    torch.randn(3, 64, 256),
]

logits = model(
    flat_images,
    group_images = True,
    group_max_seq_len = 64,
)
```

Grouping behavior is greedy and order-preserving:

1. For each image, compute token count as `(height // patch_size) * (width // patch_size)`.
2. During training with `token_dropout_prob`, grouping uses the model's token-dropout estimate to reduce the effective token count.
3. If one image's effective token count is greater than `group_max_seq_len`, grouping raises an assertion; no grouping strategy can fit that image under the requested budget.
4. If adding the next image would exceed `group_max_seq_len`, the helper closes the current group and starts a new one.
5. Output rows preserve the input image order because the greedy grouping preserves input order.

A flat list without `group_images=True` is treated as one group. That may be intentional for small batches, but it is a common source of memory blowups because no `group_max_seq_len` gate is applied.

### Tiny grouped example

```python
import torch
from vit_pytorch.na_vit import NaViT, group_images_by_max_seq_len

model = NaViT(
    image_size = 32,
    patch_size = 8,
    num_classes = 7,
    dim = 32,
    depth = 1,
    heads = 2,
    mlp_dim = 64,
    dim_head = 16,
    token_dropout_prob = 0.0,
).eval()

images = [
    torch.randn(3, 32, 32),  # 16 tokens
    torch.randn(3, 16, 16),  # 4 tokens
    torch.randn(3, 16, 32),  # 8 tokens
    torch.randn(3, 8, 32),   # 4 tokens
]

groups = group_images_by_max_seq_len(images, patch_size = 8, max_seq_len = 20)
assert [len(group) for group in groups] == [2, 2]

with torch.no_grad():
    logits = model(images, group_images = True, group_max_seq_len = 20)
assert logits.shape == (4, 7)
```

The bundled [smoke helper](../scripts/smoke_variable_shapes_video.py) runs this pattern with CPU tensors.

## Nested tensor NaViT variants

Use nested tensor variants when the user explicitly wants to avoid padding/masking overhead and the runtime supports PyTorch nested/jagged tensors.

### 2D nested NaViT

Module and class:

```python
from vit_pytorch.na_vit_nested_tensor import NaViT
```

Input is a flat list of image tensors:

```python
images = [torch.randn(3, 256, 256), torch.randn(3, 128, 128)]
logits = model(images)
```

The constructor mirrors standard NaViT with additional `qk_rmsnorm=True` and `token_dropout_prob: float | None = None`. In training mode, prefer passing an explicit numeric `token_dropout_prob` such as `0.0` or `0.1`; leaving it as `None` can be unsafe in versions where the forward path compares it to zero.

### 3D nested NaViT

Module and class:

```python
from vit_pytorch.na_vit_nested_tensor_3d import NaViT
```

Input is a flat list of volume/video tensors shaped `(channels, frames, height, width)`. The constructor uses `max_frames`, `frame_patch_size`, `patch_size`, and 3-way frame/height/width factorized position tables.

Rules:

- `max_frames` must be divisible by `frame_patch_size`.
- Each input's frame count should be no greater than `max_frames` and divisible by `frame_patch_size`.
- Height and width should be no greater than `image_size` and divisible by `patch_size`.
- The model adds register tokens before nested tensor attention pooling.

### Version caveat

The README notes the nested tensor flavor was tested with PyTorch 2.5. Treat this as a soft gate: if a user sees nested/jagged layout, scaled-dot-product attention, or unsupported operator errors, switch to standard `na_vit.NaViT` or upgrade to a PyTorch version with the required nested tensor coverage. Keep nested tensor checks opt-in in automation; do not make them the only proof that the variable-resolution workflow works.

## 3D and video transformer families

All 3D/video modules in this section consume video tensors shaped:

```python
video = torch.randn(batch, channels, frames, height, width)
```

They do not accept `(batch, frames, channels, height, width)` unless the user rearranges it first.

The common patch count is:

```text
num_frame_patches = frames // frame_patch_size
num_image_patches = (height // image_patch_height) * (width // image_patch_width)
total_patch_tokens = num_frame_patches * num_image_patches
```

### `vit_3d.ViT`

Use `vit_pytorch.vit_3d.ViT` for the closest 3D extension of the base ViT:

```python
from vit_pytorch.vit_3d import ViT

model = ViT(
    image_size = 128,
    image_patch_size = 16,
    frames = 16,
    frame_patch_size = 2,
    num_classes = 1000,
    dim = 1024,
    depth = 6,
    heads = 8,
    mlp_dim = 2048,
)

logits = model(torch.randn(4, 3, 16, 128, 128))
```

`image_patch_size` may be an integer or `(height, width)` pair. `pool` can be `'cls'` or `'mean'`.

### `simple_vit_3d.SimpleViT`

Use `vit_pytorch.simple_vit_3d.SimpleViT` for a simpler 3D ViT with sin-cos 3D positional embeddings and mean pooling. The layout and divisibility rules match `vit_3d.ViT`, but there is no dropout or `pool` constructor argument.

### `cct_3d.CCT`

Use `vit_pytorch.cct_3d.CCT` for a convolutional 3D tokenizer followed by a transformer classifier. It uses `img_size` and `num_frames` to compute the positional sequence length by running a zero tensor through the tokenizer. If `positional_embedding` is `'sine'` or `'learnable'`, the actual input's token sequence length should match the configured `img_size`/`num_frames` tokenizer result.

Key temporal/spatial tokenizer arguments include `frame_kernel_size`, `frame_stride`, `frame_pooling_kernel_size`, `frame_pooling_stride`, `kernel_size`, `stride`, `pooling_kernel_size`, and `pooling_stride`.

### `vivit.ViViT`

Use `vit_pytorch.vivit.ViViT` for the repository's ViViT implementation. Some README examples use the import name `ViT`; if the installed module does not expose that alias, import `ViViT`.

Constructor-specific choices:

- `variant='factorized_encoder'`: spatial transformer first, then temporal transformer.
- `variant='factorized_self_attention'`: alternating spatial and temporal attention; source asserts `spatial_depth == temporal_depth`.
- `pool='cls'` uses spatial and temporal CLS tokens; `pool='mean'` uses mean pooling.
- `mask`, when used, is reduced from frame-level mask positions by `frame_patch_size`.

Use `use_flash_attn=False` for conservative CPU smoke checks; use the default only after confirming the installed PyTorch supports the scaled-dot-product attention backend needed by the runtime.

### `vivit_with_moss.ViViT`

Use `vit_pytorch.vivit_with_moss.ViViT` when the prompt explicitly asks about MOSS or spatio-temporal state-space-style local processing inside ViViT.

Rules from the source:

- MOSS local dimensions (`moss_local_time`, `moss_local_height`, `moss_local_width`) should be odd.
- `moss_causal=True` makes the temporal transformer causal and forbids passing `mask` to forward.
- The model reshapes patch tokens back to `(batch, frame_patches, patch_grid_height, patch_grid_width, dim)` for MOSS, so `image_size` and `image_patch_size` must define the patch grid expected by the actual video.

## AcceptVideoWrapper workflow

`vit_pytorch.accept_video_wrapper.AcceptVideoWrapper` wraps an image network and makes it accept video shaped `(batch, channels, time, height, width)`:

1. Rearrange to `(batch, time, channels, height, width)`.
2. Flatten time into the batch so the image net receives `(batch * time, channels, height, width)`.
3. Call `getattr(image_net, forward_function)`.
4. Restore a time dimension on every tensor output with more than one element.
5. Optionally project one selected output, add learnable time positional embeddings, and/or apply MOSS to patch tokens.

Use it when a user has an image backbone and wants framewise features/logits, not when they need true joint spatio-temporal attention from the start.

Caveats:

- If `add_time_pos_emb=True`, pass `dim_emb` and `time_seq_len`; runtime asserts `time <= time_seq_len`.
- If `proj_embed_to_dim` is set, `dim_emb` is required.
- If using MOSS, the wrapper needs `patch_size` from the image model or an explicit `patch_size` argument, and the chosen output must contain patch tokens whose count matches `(height // patch_h) * (width // patch_w)` plus any CLS/register tokens.

## 1D and N-D tensor families

### 1D models

Use `vit_pytorch.vit_1d.ViT` or `vit_pytorch.simple_vit_1d.SimpleViT` for tensors shaped `(batch, channels, seq_len)`.

```python
from vit_pytorch.vit_1d import ViT

model = ViT(
    seq_len = 256,
    patch_size = 16,
    num_classes = 1000,
    dim = 1024,
    depth = 6,
    heads = 8,
    mlp_dim = 2048,
)

logits = model(torch.randn(4, 3, 256))
```

`seq_len` must be divisible by `patch_size`. The base 1D ViT uses a CLS token; `simple_vit_1d.SimpleViT` uses sin-cos 1D positions and mean pooling.

### N-D models

Use `vit_pytorch.vit_nd.ViTND` for a CLS/mean-pooled N-D classifier over inputs shaped `(batch, channels, *input_shape)`. `ndim` must be between 1 and 7. `input_shape` and `patch_size` may be integers or tuples, but tuple lengths must exactly match `ndim`.

```python
from vit_pytorch.vit_nd import ViTND

model = ViTND(
    ndim = 3,
    input_shape = (4, 8, 8),
    patch_size = (2, 4, 4),
    num_classes = 5,
    dim = 32,
    depth = 1,
    heads = 2,
    mlp_dim = 64,
)

logits = model(torch.randn(2, 3, 4, 8, 8))
```

Use `vit_pytorch.vit_nd_pope.ViTND` or `vit_pytorch.vit_nd_rotary.ViTND` when the user specifically asks for N-D polar/rotary positional embeddings or asks for patch-grid embeddings. These variants support `return_embed=True`, which returns a reconstituted patch grid shaped `(batch, *num_patches_per_dim, dim)` instead of logits.

## What the bundled smoke helper covers

`scripts/smoke_variable_shapes_video.py` runs tiny CPU checks for:

- standard NaViT greedy grouping, manual grouped forward, and a single-image token-budget failure;
- `vit_3d.ViT`, `simple_vit_3d.SimpleViT`, `cct_3d.CCT`, and `vivit.ViViT` forward shapes;
- `AcceptVideoWrapper` restoring a time dimension and adding time positional embeddings;
- representative 1D and N-D forward shapes, including PoPE/RoPE `return_embed=True` patch-grid outputs;
- optional nested tensor NaViT checks when run with `--include-nested`.
