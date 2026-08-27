# API Reference: Introspection and Customization

## Purpose

Read this when a user asks how to inspect attention or embeddings, remove hooks, inject a custom transformer into `efficient.ViT`, or choose a performance-oriented wrapper. These facts are distilled from the package README examples, the wrapper source modules, and installed-package signature/runtime checks.

## Recorder attention capture

`vit_pytorch.recorder.Recorder(vit, device=None)` wraps a ViT-like model and captures post-softmax attention tensors from base `vit_pytorch.vit.Attention` modules under `vit.transformer`.

Typical workflow:

```python
import torch
from vit_pytorch.vit import ViT
from vit_pytorch.recorder import Recorder

vit = ViT(
    image_size = 32,
    patch_size = 16,
    num_classes = 10,
    dim = 64,
    depth = 2,
    heads = 4,
    mlp_dim = 128,
    dim_head = 16,
)

wrapped = Recorder(vit)
img = torch.randn(1, 3, 32, 32)
logits, attn = wrapped(img)

# logits: (1, 10)
# attn: (batch, layers, heads, tokens, tokens)
# with this setup tokens = 1 CLS token + 4 image patches = 5
assert attn.shape == (1, 2, 4, 5, 5)

vit = wrapped.eject()  # removes hooks and returns the original backbone
```

Contract details:

- Hooks are registered lazily on the first `forward`, not at wrapper construction.
- Each forward clears previous recordings before running the backbone.
- Captured attention maps are cloned and detached; they are moved to `device` if one was supplied, otherwise to the input image device.
- `eject()` removes hook handles, clears the handle list, marks the wrapper as unusable, and returns the original `vit` object.
- Calling the ejected wrapper as a model raises an assertion: `recorder has been ejected, cannot be used anymore`.
- If no compatible base `vit_pytorch.vit.Attention` modules are found, the wrapper returns `attns is None`; do not assume every architecture variant exposes compatible recorder hooks.

Use `Recorder` for attention visualization or sanity-checking attention flow on the base ViT implementation. For architecture families with different attention classes, use `Extractor` or explicit PyTorch hooks at a verified layer instead.

## Extractor latent capture

`vit_pytorch.extractor.Extractor(vit, device=None, layer=None, layer_name='transformer', layer_save_input=False, return_embeddings_only=False, detach=True)` wraps a model and stores the input or output of one layer.

Typical base-ViT workflow:

```python
import torch
from vit_pytorch.vit import ViT
from vit_pytorch.extractor import Extractor

vit = ViT(
    image_size = 32,
    patch_size = 16,
    num_classes = 10,
    dim = 64,
    depth = 2,
    heads = 4,
    mlp_dim = 128,
    dim_head = 16,
)

wrapped = Extractor(vit)  # defaults to layer_name='transformer'
img = torch.randn(1, 3, 32, 32)
logits, embeddings = wrapped(img)

# embeddings: (batch, tokens, dim), including CLS when the backbone uses CLS pooling
assert embeddings.shape == (1, 5, 64)

vit = wrapped.eject()
```

Useful options:

- `layer_name`: name of an attribute on the wrapped model. The README CrossViT example uses `layer_name='multi_scale_encoder'` because that module outputs two scale-specific token tensors.
- `layer`: pass a concrete `nn.Module` object when the target is nested or when the wrapper object itself does not expose the desired attribute name.
- `layer_save_input=True`: save the layer input tuple instead of the layer output. This is useful when a module consumes tokens but returns pooled logits.
- `return_embeddings_only=True` on the wrapper or on `forward`: return just latents instead of `(predictions, latents)`.
- `detach=False`: keep graph-connected latents. Use only when gradients through the captured tensor are intentional; detached capture is safer for inspection.
- `device`: move captured latents to a specific device. This is convenient for CPU collection but may add transfers or memory pressure.

Lifecycle details:

- The target layer is looked up and hooked on first forward.
- A missing `layer_name` raises an assertion on first forward: `layer whose output to take as embedding not found in vision transformer`.
- A target layer that is not executed during the model's forward pass leaves no latent tensor to move; select a layer that is definitely in the active call path.
- Tuple outputs are preserved as tuples, with each tensor detached/moved independently.
- `eject()` removes hooks and returns the original model; the ejected wrapper cannot be used for another forward.

## `efficient.ViT` custom transformer contract

`vit_pytorch.efficient.ViT(*, image_size, patch_size, num_classes, dim, transformer, pool='cls', channels=3)` is a wrapper that supplies patch embedding, positional embedding, optional CLS pooling, and the classification head while delegating token mixing to the user-provided `transformer` module.

The wrapper performs this sequence:

1. Convert image patches to tokens of shape `(batch, num_patches, dim)`.
2. Prepend one CLS token, producing `(batch, num_patches + 1, dim)`.
3. Add positional embeddings.
4. Call `transformer(x)`.
5. Pool with `x[:, 0]` for `pool='cls'` or `x.mean(dim=1)` for `pool='mean'`.
6. Apply `LayerNorm(dim)` and a linear classifier.

The injected transformer therefore must:

- Accept a single tensor shaped `(batch, token_count, dim)`.
- Return a single tensor with the same rank and final dimension, normally the same token count.
- Preserve batch order, dtype, and device.
- Leave pooling to `efficient.ViT`; do not return logits or a pooled `(batch, dim)` tensor.
- Avoid returning tuples/lists unless you wrap them back into the token tensor before returning.

CPU-safe stub pattern:

```python
from torch import nn
from vit_pytorch.efficient import ViT

class TinyTokenMixer(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.net = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, dim))

    def forward(self, tokens):
        assert tokens.ndim == 3
        return tokens + self.net(tokens)

model = ViT(
    image_size = 32,
    patch_size = 16,
    num_classes = 10,
    dim = 64,
    transformer = TinyTokenMixer(dim = 64),
)
```

External transformer packages shown in the README, such as `nystrom-attention` and `x-transformers`, are optional. If they are unavailable, keep the contract test with a small local stub and document the exact external package separately for the user's environment.

## Performance-oriented wrappers

### `simple_flash_attn_vit.SimpleViT`

`vit_pytorch.simple_flash_attn_vit.SimpleViT(*, image_size, patch_size, num_classes, dim, depth, heads, mlp_dim, channels=3, dim_head=64, use_flash=True)` is a simple 2D ViT variant whose attention module calls PyTorch `scaled_dot_product_attention` when `use_flash=True`.

Important points:

- `use_flash=True` requires PyTorch 2.0 or newer according to the module assertion.
- CPU functional runs use PyTorch math/SDPA paths; CUDA-specific flash kernel speedups are optional and hardware-dependent.
- The helper is not a dependency on the external `flash-attn` package.
- For current package code, the non-SDPA branch is not the validated CPU fallback path; if `use_flash=True` is not possible, prefer `vit_pytorch.simple_vit.SimpleViT` or the base `vit_pytorch.vit.ViT` for CPU work.

### `simple_flash_attn_vit_3d.SimpleViT`

`vit_pytorch.simple_flash_attn_vit_3d.SimpleViT(*, image_size, image_patch_size, frames, frame_patch_size, num_classes, dim, depth, heads, mlp_dim, channels=3, dim_head=64, use_flash_attn=True)` applies the same PyTorch SDPA-style idea to video/3D token sequences. It shares the same optional-backend status: CPU can validate functional shape behavior, while speed claims require the user's PyTorch/backend combination.

### `parallel_vit.ViT`

`vit_pytorch.parallel_vit.ViT(*, image_size, patch_size, num_classes, dim, depth, heads, mlp_dim, pool='cls', num_parallel_branches=2, channels=3, dim_head=64, dropout=0.0, emb_dropout=0.0)` implements each transformer layer as parallel attention branches plus parallel feed-forward branches. The branch outputs are summed before residual addition.

Use `parallel_vit` when the user is asking about the parallel-transformer research variant or performance/optimization experimentation. It is still a classifier backbone; use the image-architecture route if the user is simply choosing among backbone families, and use this sub-skill when the parallel-branch behavior or wrapper/inspection interactions matter.

## Hook and wrapper validation checklist

Before handing a workflow back to the user:

- Check the model receives a tiny input whose image/frame dimensions are divisible by the selected patch sizes.
- For `Recorder`, confirm `attn is not None` and has `(batch, layers, heads, tokens, tokens)` when using base `vit_pytorch.vit.ViT`.
- For `Extractor`, confirm the selected layer actually runs and that latents are a tensor or tuple of tensors with expected shape.
- For `efficient.ViT`, assert the custom transformer input and output are 3D token tensors with final dimension equal to `dim`.
- After `eject()`, keep using the returned backbone, not the ejected wrapper object.
- Keep optional acceleration failures non-blocking for CPU-scoped tasks unless the user explicitly requires CUDA/flash performance.
