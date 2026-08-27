---
name: modules-and-networks
description: "Route and implement Haiku model-building tasks with layers,
  normalization, attention, recurrent cores, and built-in networks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Haiku Modules and Networks

Use this sub-skill when the task is to build, inspect, or debug a Haiku model from public `haiku` / `hk` layers, recurrent or attention modules, and `hk.nets` network families.

## Read First

- Read [references/api-reference.md](references/api-reference.md) when you need constructor/call signatures, shape contracts, or a module-family decision table.
- Read [references/model-overview.md](references/model-overview.md) when you need to choose between MLP, convolutional, recurrent, attention, normalization, ResNet/MobileNet, VQ-VAE, or example-derived patterns.
- Read [references/workflows.md](references/workflows.md) when you need self-contained recipes for tiny no-download validation, BatchNorm/state decisions, RNNs, transformers, ResNets, VAEs, or IMPALA-style model bodies.
- Read [references/troubleshooting.md](references/troubleshooting.md) when shapes, data formats, stateful layers, RNG/dropout, optional example dependencies, or JAX backend expectations fail.
- Run [scripts/haiku_mlp_smoke.py](scripts/haiku_mlp_smoke.py) to validate a synthetic MNIST-style MLP with no dataset, Optax, TensorFlow, or TFDS dependency.

## Owned Capability Surface

This sub-skill owns routing and model-building guidance for:

- Common modules: `hk.Linear`, `hk.Bias`, `hk.Sequential`, `hk.dropout`, `hk.one_hot`, `hk.multinomial`, `hk.avg_pool`, `hk.max_pool`, `hk.AvgPool`, `hk.MaxPool`, `hk.Flatten`, and `hk.Reshape` when they are part of a model body.
- Convolutional modules: `hk.ConvND`, `hk.Conv1D`, `hk.Conv2D`, `hk.Conv3D`, transposed variants, `hk.DepthwiseConv1D/2D/3D`, grouped convolution, masks, padding, and data-format choices.
- Normalization modules: `hk.BatchNorm`, `hk.LayerNorm`, `hk.GroupNorm`, `hk.InstanceNorm`, `hk.RMSNorm`, `hk.SpectralNorm`, and how their statefulness affects model wrappers.
- Sequence/model modules: `hk.Embed`, `hk.MultiHeadAttention`, `hk.RNNCore`, `hk.dynamic_unroll`, `hk.static_unroll`, `hk.VanillaRNN`, `hk.LSTM`, `hk.GRU`, `hk.DeepRNN`, reset/identity cores, and convolutional LSTMs.
- Built-in networks: `hk.nets.MLP`, `hk.nets.ResNet*`, `hk.nets.MobileNetV1`, `hk.nets.VectorQuantizer`, and `hk.nets.VectorQuantizerEMA`.
- Distilled example patterns: synthetic MLP classification, VAE-style stochastic modules, ResNet/ImageNet-style `is_training` and BatchNorm flow, RNN unrolls, transformer blocks, and IMPALA-style model composition without full downloads or training loops.

## Route Elsewhere

- For `hk.transform`, `hk.transform_with_state`, `hk.without_apply_rng`, `hk.multi_transform`, or exact init/apply signature mechanics, route to `core-transforms`.
- For direct `hk.get_parameter`, `hk.get_state`, `hk.set_state`, `hk.next_rng_key`, `hk.PRNGSequence`, module naming, creators/getters/setters, and RNG sequence debugging, route to `params-state-rng`.
- For Haiku wrappers around JAX transforms/control flow such as `hk.scan`, `hk.vmap`, `hk.grad`, `hk.lift`, `hk.layer_stack`, mixed precision policies, tree utilities, or visualization, route to `jax-interop-and-advanced`.
- For optional Flax variables or Haiku-in-Flax / Flax-in-Haiku workflows, route to `flax-interop`.

## Operating Checklist

1. Identify the model family and leading shape convention: tabular `[B, F]`, image `[B, H, W, C]` / `[B, C, H, W]`, sequence `[T, B, F]` or `[B, T, F]`, or token `[B, T]`.
2. Decide whether the model body is stateless or stateful. `BatchNorm`, `SpectralNorm`, ResNet/MobileNet with BatchNorm, and `VectorQuantizerEMA` require state; prefer stateless `LayerNorm`, `GroupNorm`, `InstanceNorm`, or `RMSNorm` when moving-average state is not needed.
3. Keep `hk.Sequential` only for single-input/single-output chains. If a later layer needs `is_training`, `mask`, `rng`, or multiple arguments, write a small `hk.Module` or forward function instead.
4. Validate with synthetic arrays before expensive data loading. Check output shape, parameter leaves, and state keys; only then add optimizer, datasets, distributed maps, or long training.
5. If a failure involves state/RNG/transform signatures, stop editing the model body and route to the appropriate sibling sub-skill before changing code.
