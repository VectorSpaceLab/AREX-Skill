---
name: activation-maximization
description: "Uses keras-vis activation maximization to synthesize inputs that
  maximize Dense outputs, regression outputs, and convolutional filters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Activation Maximization

Use this sub-skill when a task asks for keras-vis activation maximization, feature visualization, class prototype synthesis, regression-output increase/decrease probes, or convolutional filter input synthesis.

## Routing

- Use this sub-skill for `vis.visualization.visualize_activation` and `visualize_activation_with_losses` workflows that optimize an input tensor to maximize a layer unit or filter.
- Route saliency maps, guided saliency maps, and Grad-CAM to [saliency-and-cam](../saliency-and-cam/SKILL.md).
- Route custom loss authoring, optimizer internals, callbacks, input modifiers beyond activation-maximization usage, and advanced `wrt_tensor` design to [optimization-building-blocks](../optimization-building-blocks/SKILL.md).
- Route image loading, overlay composition, stitched grids, labels, display, and file I/O to [image-utilities](../image-utilities/SKILL.md).

## Runtime assumptions

This skill targets the legacy keras-vis runtime: keras-vis 0.5.0 with standalone Keras 2.2.x and TensorFlow 1.x graph-mode backends. Use `keras`, not `tensorflow.keras`, in examples and scripts.

## Read next

1. [API reference](references/api-reference.md) for signatures, defaults, `filter_indices`, weights, modifiers, and return values.
2. [Workflows](references/workflows.md) for Dense classifier, regression, Conv filter, seeded refinement, Jitter, and GIF progress recipes.
3. [Troubleshooting](references/troubleshooting.md) when imports, softmax outputs, regularizers, modifiers, or convergence fail.

## Safe smoke check

From the generated keras-vis skill root, run the bundled smoke script without downloading data or models:

```bash
python sub-skills/activation-maximization/scripts/activation_smoke.py --help
python sub-skills/activation-maximization/scripts/activation_smoke.py --target dense --max-iter 3
```

Use the smoke script as an environment probe only; it creates a tiny untrained model and checks that activation maximization can execute.