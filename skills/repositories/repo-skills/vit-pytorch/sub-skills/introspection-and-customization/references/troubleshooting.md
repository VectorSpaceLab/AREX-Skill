# Troubleshooting: Hooks, Optional Dependencies, and Backends

## Purpose

Use this guide when a vit-pytorch introspection or customization workflow fails after wrapping a model, selecting a hook layer, injecting a custom transformer, or trying a performance-oriented variant.

## Missing or wrong layer names for `Extractor`

Symptoms:

- First forward raises `AssertionError: layer whose output to take as embedding not found in vision transformer`.
- The wrapper returns predictions but latent movement fails because no tensor was captured.
- CrossViT or another variant returns a tuple/shape that the downstream code was not expecting.

Likely causes:

- `layer_name` is not an attribute on the wrapped model.
- The requested layer exists but is not called in the active forward path.
- The user wrapped another wrapper rather than the raw backbone, so the expected layer attribute is hidden on `wrapped.vit`.
- The chosen layer returns a tuple, while the user's downstream code assumes one tensor.

Recovery:

1. For base `vit_pytorch.vit.ViT`, start with the default `layer_name='transformer'`.
2. For CrossViT-style multi-scale extraction, target the model's multi-scale encoder and expect a tuple of tensors rather than one tensor.
3. If the layer is nested, pass the concrete `layer=<module>` object to `Extractor` instead of guessing a top-level name.
4. If the target module consumes the desired tokens but returns something else, retry with `layer_save_input=True`.
5. Run a tiny random-tensor forward before a long job and assert the exact latent shape.

## `Recorder` returns `attns is None`

Symptoms:

- `logits, attns = Recorder(model)(img)` succeeds, but `attns` is `None`.
- The code expected `(batch, layers, heads, tokens, tokens)` attention maps but got no maps.

Likely causes:

- `Recorder` searches for base `vit_pytorch.vit.Attention` modules under `model.transformer`. Many architecture variants define their own `Attention` class, so they are not matched by the recorder's type check.
- The wrapped object does not expose `.transformer` in the expected shape, or it is another wrapper around the actual model.
- The model has no compatible attention layers in the active path.

Recovery:

1. Reproduce the workflow with a base `vit_pytorch.vit.ViT` if the user specifically needs recorder attention maps.
2. For variant backbones, switch to `Extractor` on a verified layer or write a custom PyTorch hook against the variant's actual attention/softmax module.
3. Do not treat `attns is None` as a successful attention-capture result; it only proves the backbone forward ran.
4. Use `scripts/smoke_introspection.py` to check the expected base-ViT recorder behavior in the installed package.

## Hook lifecycle after `eject()`

Symptoms:

- Forward on a wrapper raises `recorder has been ejected, cannot be used anymore` or `extractor has been ejected, cannot be used anymore`.
- After `v = v.eject()`, a later `v.eject()` call raises `AttributeError` because `v` is now the original backbone.
- A user ejects before any forward and wonders why no hooks were removed.

Expected behavior:

- Hooks register lazily on first forward. Ejecting before first forward is allowed, but there are no registered hook handles to remove.
- `eject()` returns the original model and marks the wrapper object unusable.
- Calling `eject()` twice on the same wrapper object is not a workflow; if the user reassigned the return value, they are no longer holding the wrapper.

Recovery:

1. Keep names clear:

   ```python
   recorder = Recorder(vit)
   logits, attn = recorder(img)
   vit = recorder.eject()
   # use vit from here; create Recorder(vit) again if more attention maps are needed
   ```

2. Do not call the ejected wrapper for another forward.
3. If a hook was ejected too early, create a fresh wrapper around the returned backbone and run the tiny input again.
4. If nested wrappers were used, simplify to one wrapper at a time or pass a concrete `layer` to `Extractor`.

## Optional dependency errors for custom transformer examples

Symptoms:

- `ModuleNotFoundError: No module named 'nystrom_attention'`.
- `ModuleNotFoundError: No module named 'x_transformers'`.
- The custom transformer imports, but `efficient.ViT` fails during pooling or the classifier head.

Likely causes:

- README research-idea examples use optional external packages that are not part of the minimum vit-pytorch CPU install.
- The external transformer returns pooled output, logits, auxiliary state, or a tuple rather than token sequences.
- The external transformer's `dim` differs from the `efficient.ViT(dim=...)` wrapper.

Recovery:

1. First validate `efficient.ViT` with a local token-preserving stub, as in `references/api-reference.md#efficientvit-custom-transformer-contract` or the bundled smoke script.
2. Install optional external packages only when the user explicitly needs that exact implementation.
3. Wrap external modules so their public forward returns only a `(batch, token_count, dim)` token tensor.
4. Keep `dim`, number of input tokens, dtype, and device consistent through the custom transformer.
5. If the transformer changes token count intentionally, verify the selected pooling still makes sense and that the final token dimension remains `dim`.

## Flash-attention and backend expectations

Symptoms:

- `AssertionError: in order to use flash attention, you must be using pytorch 2.0 or above`.
- CPU runs succeed but are not faster.
- CUDA flash kernels are unavailable or silently use math/memory-efficient alternatives.
- Setting a non-flash path in a simple flash module raises a Python name error in current package code.

Likely causes:

- `simple_flash_attn_vit` and `simple_flash_attn_vit_3d` rely on PyTorch scaled dot-product attention when flash mode is enabled; real performance depends on PyTorch version, hardware, dtype, and backend kernel selection.
- CPU validates functional behavior but does not prove CUDA flash speed.
- The selected CPU scope does not require external `flash-attn` or CUDA-only verification.
- In the current package code, the manually computed non-SDPA branch is not the validated fallback path.

Recovery:

1. For CPU-scoped functional work, use standard `vit_pytorch.vit.ViT`, `vit_pytorch.simple_vit.SimpleViT`, or `efficient.ViT` with a normal transformer if PyTorch SDPA is unavailable.
2. If the user requires flash performance, check PyTorch version, CUDA availability, GPU architecture, dtype, and `torch.backends.cuda` SDPA settings in their runtime; do not infer speed from a CPU smoke test.
3. Do not require the external `flash-attn` package for the bundled helper; these vit-pytorch modules use PyTorch's attention API.
4. Prefer documenting a backend limitation over installing broad optional accelerator packages.

## Custom transformer returns the wrong shape

Symptoms:

- `efficient.ViT` errors inside pooling, `LayerNorm`, or the classifier head.
- Output logits have a surprising shape such as `(batch,)` or token count instead of `(batch, num_classes)`.
- The model fails only after swapping in an external transformer.

Likely causes:

- The custom transformer returned pooled `(batch, dim)` features instead of tokens.
- The final dimension is not equal to the `efficient.ViT` `dim`.
- The transformer returned `(tokens, batch, dim)` instead of `(batch, tokens, dim)`.
- The transformer returned an auxiliary tuple or dict.
- CLS/mean pooling assumptions were changed inside the transformer and again in `efficient.ViT`.

Recovery:

1. Add an assertion to the custom transformer:

   ```python
   def forward(self, tokens):
       assert tokens.ndim == 3
       out = self.layers(tokens)
       assert out.shape[0] == tokens.shape[0]
       assert out.shape[-1] == tokens.shape[-1]
       return out
   ```

2. Leave classifier logits and pooling to `efficient.ViT`.
3. If using a library that returns multiple values, adapt it with a small wrapper that returns the token tensor only.
4. Validate with the bundled smoke script's bad-transformer guard before using high-resolution images.

## Parallel branches and introspection wrappers

Symptoms:

- A `parallel_vit.ViT` classifier forward works, but `Recorder` does not capture maps.
- Changing `num_parallel_branches` changes parameter count or memory but not the expected output shape.

Likely causes:

- `parallel_vit` defines its own `Attention` class and sums branch outputs through a `Parallel` module; the base `Recorder` type check does not target these modules.
- More branches increase compute/memory even though the classifier API remains `(batch, num_classes)`.

Recovery:

1. Use `parallel_vit` as a performance/architecture variant with normal classifier shape checks.
2. For branch-specific inspection, hook the actual branch module with `Extractor(layer=<module>)` or a custom PyTorch hook after identifying the desired branch.
3. Keep branch count as an explicit experiment parameter; do not present it as a CPU requirement.

## Memory and device pitfalls during capture

Symptoms:

- Attention extraction runs out of memory on large images or deep models.
- Captured tensors are on an unexpected device.
- Backpropagation memory grows unexpectedly when extracting embeddings.

Likely causes:

- Attention maps scale with `batch * layers * heads * tokens * tokens`.
- Supplying `device` to `Recorder` or `Extractor` moves captured tensors, which may add transfers or concentrate memory.
- `Extractor(detach=False)` keeps graph-connected latents.

Recovery:

1. Use smaller images, fewer layers/heads, or reduced batch size for attention visualization.
2. Capture only one layer with `Extractor` when full attention maps are too large.
3. Prefer default detached capture for inspection-only workflows.
4. Move captures to CPU only when the transfer is intentional and the tensor size is manageable.
