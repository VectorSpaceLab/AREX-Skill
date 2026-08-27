---
name: layers-and-nets
description: "Use Sonnet built-in layers, normalization modules, initializers,
  metrics, and predefined nets with correct shapes and state."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sonnet Layers and Nets

Use this sub-skill for Sonnet built-ins: `Linear`, `Bias`, convolutions, transpose/depthwise convolutions, embeddings, reshape/flatten, dropout, normalization, initializers, regularizers, metrics, moving averages, and `snt.nets` models such as `MLP`, `Cifar10ConvNet`, `ResNet`, and VQ-VAE quantizers.

## Start here

1. Read [references/api-reference.md](references/api-reference.md) for grouped signatures and shape/state contracts.
2. Read [references/workflows.md](references/workflows.md) for MLP, Conv2D+BatchNorm, ResNet, VQ-VAE, metrics, and regularizer recipes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for unknown dimensions, bias conflicts, normalization state, VQ-VAE errors, and dropout flag failures.
4. Run [scripts/layers_and_nets_smoke.py](scripts/layers_and_nets_smoke.py) for a safe no-download shape/state check.

## Boundaries

- Custom module design: [../module-authoring/SKILL.md](../module-authoring/SKILL.md).
- Training/optimizer loops: [../training-and-optimization/SKILL.md](../training-and-optimization/SKILL.md).
- Recurrent modules: [../sequence-and-rnn/SKILL.md](../sequence-and-rnn/SKILL.md).
- Serialization/distribution: [../serialization-and-distribution/SKILL.md](../serialization-and-distribution/SKILL.md).

## Validation checklist

Known feature/channel dimensions are required on first call. `with_bias=False` forbids `b_init`. BatchNorm calls must pass `is_training`. VQ-VAE inputs must end with `embedding_dim`. `snt.nets.MLP` requires `is_training` only when dropout is enabled.
