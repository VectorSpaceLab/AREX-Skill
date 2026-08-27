---
name: fast-clipping
description: "Routes TensorFlow Privacy users who need fast gradient clipping,
  layer registries, or sparsity-preserving noise helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Fast clipping

Use this sub-skill when the user wants to work with the fast gradient clipping internals or the sparse-noise helpers used by DP models.

## Trigger phrases

- "fast gradient clipping"
- "layer registry"
- "sparse noise"
- "per-example gradient norms"
- "clip weights"
- "LayerNormalization registry"
- "MultiHeadAttention registry"
- "EinsumDense registry"

## What this sub-skill covers

- `compute_gradient_norms()`, `compute_clip_weights()`, and `compute_clipped_gradients_and_outputs()`
- `LayerRegistry` and `make_default_layer_registry()`
- registry functions for Dense, Embedding, LayerNormalization, MultiHeadAttention, and EinsumDense
- optional NLP/BERT helper registry functions
- `SparsityPreservingNoiseConfig` and `add_aggregate_noise()`

## What it does not cover

- high-level DP training usage -> `../training/`
- privacy budgets and accounting -> `../privacy-accounting/`
- `DPQuery` internals -> `../queries/`
- membership inference and secret-sharer analysis -> `../privacy-tests/`

## Read this before you act

- `references/api-reference.md` for the verified function signatures and registry coverage.
- `references/troubleshooting.md` for unsupported-layer, loss-reduction, and optional-dependency failures.
- `../../references/install-and-scope.md` for the CPU-only minimum runtime and the optional NLP/BERT helper caveat.

## Typical workflow

1. Check whether the model's trainable layers are covered by the default registry.
2. If the model has only the core Keras layers, use the default registry first.
3. If the model has a missing layer, decide whether to extend the registry or stay on the plain DP optimizer path.
4. Use the bundled smoke helper to verify the registry and noise-addition path on a tiny model.

## Bundled helper

Run `scripts/tiny_fast_clipping_smoke.py` to verify the default registry and the noise-addition path on a tiny Dense model.
