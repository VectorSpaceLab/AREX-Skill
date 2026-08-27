# Activation maximization workflows

These workflows are written for future runtime use. They intentionally stay close to the public keras-vis API and avoid source-checkout dependencies.

## 0. Smoke the environment first

Use the bundled smoke script before debugging a larger model:

```bash
python sub-skills/activation-maximization/scripts/activation_smoke.py --help
python sub-skills/activation-maximization/scripts/activation_smoke.py --target dense --max-iter 3
```

If the smoke script reports an import failure, see [troubleshooting](troubleshooting.md) before changing model code.

## 1. Maximize a final Dense class output

Use this when the task asks what input image best matches a class, output index, or output neuron.

```python
from keras import activations
from vis.utils import utils
from vis.visualization import visualize_activation

layer_idx = utils.find_layer_idx(model, "predictions")
model.layers[layer_idx].activation = activations.linear
model = utils.apply_modifications(model)

img = visualize_activation(
    model,
    layer_idx,
    filter_indices=class_index,
    input_range=(0., 1.),
    max_iter=200,
    verbose=True,
)
```

Tips:

- Use `filter_indices=class_index` for one class.
- Use `filter_indices=[class_a, class_b]` for a multi-label prototype.
- Keep `input_range=(0., 1.)` when the model was trained on normalized floats.
- Turn on `verbose=True` when the regularizers hide the activation loss.

## 2. Increase or decrease a regression output

Use this when the task asks how to synthesize an input that pushes a regression head up or down.

```python
from vis.visualization import visualize_activation

# Increase the output.
img_up = visualize_activation(
    model,
    layer_idx,
    filter_indices=0,
    seed_input=seed_input,
    input_range=(0., 1.),
    max_iter=150,
)

# Decrease the output by negating gradients.
img_down = visualize_activation(
    model,
    layer_idx,
    filter_indices=0,
    seed_input=seed_input,
    input_range=(0., 1.),
    grad_modifier="negate",
    max_iter=150,
)
```

Workflow notes:

- A representative `seed_input` often matters more for regression than for classification.
- If the model is not image-based, disable `tv_weight` and consider whether activation maximization is appropriate for the task.

## 3. Visualize a Conv filter

Use this when the task asks what pattern a convolutional channel or filter responds to.

```python
import numpy as np
from vis.input_modifiers import Jitter
from vis.visualization import get_num_filters, visualize_activation
from vis.utils import utils

layer_idx = utils.find_layer_idx(model, "block1_conv2")
num_filters = get_num_filters(model.layers[layer_idx])

for filter_idx in range(num_filters):
    img = visualize_activation(
        model,
        layer_idx,
        filter_indices=filter_idx,
        input_modifiers=[Jitter(0.05)],
        input_range=(0., 1.),
    )
```

Workflow notes:

- `filter_indices` names the channel/filter within the chosen Conv layer.
- `Jitter` is often enough to sharpen the result without changing the objective.
- For display or stitching, route image output handling to [image-utilities](../../image-utilities/SKILL.md).

## 4. Recover from over-regularized or noisy results

If the visualization is blurry, flat, or dominated by noise, use a two-pass refinement:

```python
from vis.input_modifiers import Jitter
from vis.visualization import visualize_activation

coarse = visualize_activation(
    model,
    layer_idx,
    filter_indices=filter_idx,
    tv_weight=0.0,
    lp_norm_weight=0.0,
    max_iter=100,
    input_range=(0., 1.),
)

refined = visualize_activation(
    model,
    layer_idx,
    filter_indices=filter_idx,
    seed_input=coarse,
    input_modifiers=[Jitter(0.05)],
    max_iter=150,
    input_range=(0., 1.),
)
```

Use this workflow when the first pass shows the target concept but the regularizers prevent convergence.

## 5. Use custom weighted losses

Use `visualize_activation_with_losses` when the built-in activation + LP + TV objective is not enough.

```python
from vis.losses import ActivationMaximization
from vis.regularizers import LPNorm, TotalVariation
from vis.input_modifiers import Jitter
from vis.visualization import visualize_activation_with_losses

losses = [
    (ActivationMaximization(model.layers[layer_idx], filter_indices), 1.0),
    (LPNorm(model.input), 5.0),
    (TotalVariation(model.input), 2.0),
]

img = visualize_activation_with_losses(
    model.input,
    losses,
    seed_input=seed_input,
    input_range=(0., 1.),
    max_iter=100,
    input_modifiers=[Jitter(0.05)],
    verbose=True,
)
```

Workflow notes:

- Keep custom loss design and optimizer tuning in [optimization-building-blocks](../../optimization-building-blocks/SKILL.md).
- Use this API when the caller explicitly needs a custom objective, not just a class or filter probe.
- Use `0.0` for any loss you want to disable.

## 6. Capture optimization progress as a GIF

When the task asks for progress frames, attach `GifGenerator`.

```python
from vis.callbacks import GifGenerator
from vis.input_modifiers import Jitter
from vis.visualization import visualize_activation

img = visualize_activation(
    model,
    layer_idx,
    filter_indices=filter_idx,
    input_modifiers=[Jitter(0.05)],
    callbacks=[GifGenerator("activation_progress", input_range=(0, 255))],
    max_iter=200,
)
```

Keep the GIF path inside the current workspace or artifact tree. File placement, overlaying labels, and image export details belong to [image-utilities](../../image-utilities/SKILL.md).

## 7. Reproducibility checklist

When a future agent needs a repeatable activation-maximization answer, collect these choices before tuning:

- Input format: `channels_first` or `channels_last`.
- Target type: Dense class, Dense regression, or Conv filter.
- Whether the final Dense activation must be swapped to linear.
- Whether `seed_input` should be random or derived from a known input.
- Whether the default LP/TV regularizers should stay on, be reduced, or be disabled.
- Whether `Jitter` or `GifGenerator` is needed.
- Whether the call should use `visualize_activation` or `visualize_activation_with_losses`.