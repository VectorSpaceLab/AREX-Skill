---
name: introspection-and-customization
description: "Routes vit-pytorch attention recording, embedding extraction,
  custom transformer injection, flash-attention-style wrappers, and parallel
  transformer customization helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Introspection and Customization

Use this sub-skill when the user wants to inspect a vit-pytorch backbone or swap in a transformer implementation, especially prompts mentioning `Recorder`, `Extractor`, attention maps, embeddings/latents, `efficient.ViT`, Nystromformer, `x-transformers`, `simple_flash_attn_vit`, `simple_flash_attn_vit_3d`, or `parallel_vit`.

## Route by user intent

- **Attention maps from a base ViT**: use `vit_pytorch.recorder.Recorder`. Read [API reference](references/api-reference.md#recorder-attention-capture) and run [smoke_introspection.py](scripts/smoke_introspection.py) when validating an install. The recorder wraps a backbone, registers hooks on first forward, returns `(predictions, attention_maps)`, and must be ejected when hooks are no longer needed.
- **Embedding or latent extraction**: use `vit_pytorch.extractor.Extractor`. Read [API reference](references/api-reference.md#extractor-latent-capture) before choosing `layer_name`, `layer`, `layer_save_input`, `return_embeddings_only`, or `detach`. Use this for transformer outputs, multi-scale outputs, and custom hook points.
- **Custom efficient transformer injection**: use `vit_pytorch.efficient.ViT` when the user already has or wants to provide a token-sequence transformer. Read [API reference](references/api-reference.md#efficientvit-custom-transformer-contract). External examples such as `nystrom-attention` and `x-transformers` are optional; the CPU-supported contract can be checked with the bundled smoke helper's tiny in-script transformer stub.
- **Performance-oriented variants**: route `parallel_vit` and `simple_flash_attn_vit` questions here. Treat flash/SDPA and CUDA behavior as optional performance paths, not requirements for the selected CPU scope. Read [API reference](references/api-reference.md#performance-oriented-wrappers) and [troubleshooting](references/troubleshooting.md#flash-attention-and-backend-expectations).

## Boundaries

This sub-skill owns hook lifecycle, attention-map capture, latent extraction, custom transformer token contracts, optional acceleration caveats, and safe fallback advice for introspection/customization wrappers.

Route elsewhere instead of duplicating guidance:

- Plain image backbone selection, architecture zoo comparisons, patch-size choices, and normal `ViT`/`SimpleViT` classifier construction belong to the image-architecture route.
- Variable-resolution batches, 1D/3D/N-D routing, and video model selection belong to the variable-shapes/video route unless the user is specifically asking about `simple_flash_attn_vit_3d` as a flash/SDPA customization wrapper.
- Training, distillation, masked modeling, DINO/EsViT, decorrelation losses, and other loss-based wrappers belong to the pretraining/adaptation route.

## Operating rules for future agents

1. **Wrap raw backbones deliberately.** `Recorder` and `Extractor` are wrappers around a model object; avoid stacking wrappers unless you explicitly pass the inner layer object to `Extractor`. If a wrapper is ejected, use the returned backbone or create a fresh wrapper for more introspection.
2. **Validate hook targets before long runs.** Hooks register on the first forward, so wrong `layer_name` values and unsupported attention-module types often fail only when the model is called. Prefer a tiny random tensor smoke check before training or large inference.
3. **Keep custom transformer outputs token-shaped.** `efficient.ViT` supplies tokens shaped `(batch, token_count, dim)` and then performs pooling and the classifier head itself. The injected transformer must return a compatible token tensor, not pooled logits, a tuple, or a changed embedding dimension.
4. **Treat accelerations as optional.** The flash-attention-style modules use PyTorch scaled dot-product attention when enabled; they do not require the external `flash-attn` package for CPU functional checks. If a backend or optional package is unavailable, fall back to standard vit-pytorch backbones or a stub/standard transformer rather than blocking the CPU workflow.
5. **Use the bundled smoke helper for confidence.** After installing `vit-pytorch`, run:

   ```bash
   python sub-skills/introspection-and-customization/scripts/smoke_introspection.py
   ```

   Run it from the generated `vit-pytorch` skill directory, or pass the script path directly from any working directory. It imports the installed package and does not read external source files.

## References

- [API reference and wrapper contracts](references/api-reference.md)
- [Troubleshooting hook, optional dependency, and backend pitfalls](references/troubleshooting.md)
- [CPU smoke helper](scripts/smoke_introspection.py)
