# Activation maximization API reference

This reference distills the keras-vis 0.5.0 activation maximization API for future runtime use. It assumes standalone Keras models and a graph-mode backend.

## Primary imports

```python
from vis.visualization import visualize_activation
from vis.visualization import visualize_activation_with_losses
from vis.visualization import get_num_filters
from vis.utils import utils
```

Use `keras` imports from standalone Keras:

```python
from keras import activations
from keras import backend as K
```

## `visualize_activation`

```python
visualize_activation(
    model,
    layer_idx,
    filter_indices=None,
    wrt_tensor=None,
    seed_input=None,
    input_range=(0, 255),
    backprop_modifier=None,
    grad_modifier=None,
    act_max_weight=1,
    lp_norm_weight=10,
    tv_weight=10,
    **optimizer_params
)
```

Generates a model input that maximizes the selected unit(s) or filter(s) in `model.layers[layer_idx]`. Internally it builds these weighted losses and minimizes them with `vis.optimizer.Optimizer`:

```python
from vis.losses import ActivationMaximization
from vis.regularizers import LPNorm, TotalVariation

losses = [
    (ActivationMaximization(model.layers[layer_idx], filter_indices), act_max_weight),
    (LPNorm(model.input), lp_norm_weight),
    (TotalVariation(model.input), tv_weight),
]
```

| Argument | Default | How to use it |
| --- | --- | --- |
| `model` | required | A standalone `keras.models.Model` or `Sequential` with image-like input. Use the same backend image data format that the model was built with. |
| `layer_idx` | required | Integer index into `model.layers`. Prefer `utils.find_layer_idx(model, "layer_name")` over hard-coding indexes for nontrivial models. |
| `filter_indices` | `None` | Unit/filter index or list of indexes to maximize. See the semantics section below. |
| `wrt_tensor` | `None` | Advanced: tensor with respect to which gradients are computed. Leave as `None` for normal input synthesis. If this is not the input tensor, the standard optimizer cannot update the input in the usual way; route advanced designs to [optimization-building-blocks](../../optimization-building-blocks/SKILL.md). |
| `seed_input` | `None` | Starting image/input. If omitted, keras-vis creates random noise around the midpoint of `input_range` with standard deviation `0.05 * (max - min)`. A seed without a batch dimension is expanded automatically. |
| `input_range` | `(0, 255)` | Output deprocessing range. Integer endpoints produce clipped `uint8` output; float endpoints such as `(0., 1.)` keep floating output, which is usually better for normalized training pipelines. |
| `backprop_modifier` | `None` | Optional backprop graph modifier: commonly `'guided'`, `'rectified'`, `'relu'`, or `'deconv'`, or a callable. Use only when a task explicitly needs modified backprop behavior. |
| `grad_modifier` | `None` | Optional gradient post-processor: `'negate'`, `'absolute'`, `'invert'`, `'relu'`, `'small_values'`, or a callable. Use `'negate'` to synthesize inputs that decrease a regression output. |
| `act_max_weight` | `1` | Weight for the activation maximization objective. Keep positive for normal synthesis. |
| `lp_norm_weight` | `10` | Weight for `LPNorm(model.input)`, which discourages extreme pixel values. Set `0.0` to disable safely. |
| `tv_weight` | `10` | Weight for `TotalVariation(model.input)`, which encourages spatial coherence. Set `0.0` to disable safely. |
| `**optimizer_params` | see below | Passed to `Optimizer.minimize`, most often `max_iter`, `verbose`, `input_modifiers`, and `callbacks`. |

### Optimizer parameters commonly passed through

`visualize_activation` and `visualize_activation_with_losses` default missing optimizer parameters to `max_iter=200`, `verbose=False`, and the supplied `seed_input`. `Optimizer.minimize` also accepts:

| Optimizer kwarg | Typical use |
| --- | --- |
| `max_iter=200` | Increase for better convergence; use small values for smoke tests. |
| `verbose=False` | Set `True` to print each weighted loss every iteration and diagnose whether regularizers dominate the objective. |
| `input_modifiers=None` | List of input modifier instances. `Jitter(...)` is the common activation-maximization modifier. |
| `callbacks=None` | List of optimizer callbacks, for example `GifGenerator(...)` for progress capture. |

Pass `grad_modifier` to `visualize_activation` directly, not both directly and inside `optimizer_params`.

## `filter_indices` semantics

`ActivationMaximization` turns a scalar index into a one-item list; a list sums several activation objectives.

| Layer output rank | Layer type pattern | Objective slice | Meaning of `filter_indices` |
| --- | --- | --- | --- |
| rank 2 | `Dense` or final output layer | `layer.output[:, idx]` | Output unit index. For classifier heads, this is a class index. For regression heads, this is the regression output dimension. |
| rank > 2 | Conv or spatial feature layer | backend-agnostic channel slice | Channel/filter index. keras-vis uses a slicer so the same index works for `channels_first` and `channels_last`. |

Practical rules:

- Use an integer for one class/unit/filter: `filter_indices=20`.
- Use a list for a combined objective: `filter_indices=[1, 7]`.
- `None` is documented as all filters/units. For predictable production code, prefer explicit indexes from `range(get_num_filters(model.layers[layer_idx]))` when iterating all filters.
- Check bounds with `get_num_filters(model.layers[layer_idx])` before looping.

## Dense classifier heads: replace softmax with linear

For final classification `Dense` layers, maximize logits rather than softmax probabilities. A softmax class probability can increase by decreasing other classes, which often gives weaker visualizations.

```python
from keras import activations
from vis.utils import utils

layer_idx = utils.find_layer_idx(model, "predictions")
model.layers[layer_idx].activation = activations.linear
model = utils.apply_modifications(model)
```

Notes:

- `utils.apply_modifications(model, custom_objects=None)` rebuilds the Keras graph and returns a modified model.
- Provide `custom_objects` if the model contains custom layers, losses, or activations.
- Perform the activation swap before calling `visualize_activation`.

## Regression outputs

For a linear regression head, `filter_indices` selects the output dimension.

```python
# Increase output 0.
img_up = visualize_activation(model, layer_idx, filter_indices=0, input_range=(0., 1.))

# Decrease output 0 by negating gradients.
img_down = visualize_activation(
    model,
    layer_idx,
    filter_indices=0,
    input_range=(0., 1.),
    grad_modifier="negate",
)
```

Regression models may provide sparse or ambiguous gradients. Start from a meaningful `seed_input` when the task asks how an existing input should change.

## Regularization weights

| Weight | Owned loss | Effect | Tuning guidance |
| --- | --- | --- | --- |
| `act_max_weight` | `ActivationMaximization` | Maximizes selected units by minimizing negative mean activation. | Keep nonzero unless using custom weighted losses. |
| `lp_norm_weight` | `LPNorm(p=6.)` | Penalizes large pixel/input values. | Lower if images are too dull or the main loss never improves. |
| `tv_weight` | `TotalVariation(beta=2.)` | Penalizes high-frequency spatial variation. | Lower or disable for tiny inputs, high-level filters that fail to converge, or non-natural-image probes. |

Use numeric `0` or `0.0` to disable a built-in loss. Although some docstrings say `None` also disables a loss, keras-vis 0.5.0 checks only `weight != 0` before multiplying the loss, so `None` can raise a `TypeError`.

## Modifiers and callbacks used by activation maximization

```python
from vis.input_modifiers import Jitter
from vis.callbacks import GifGenerator

img = visualize_activation(
    model,
    layer_idx,
    filter_indices=filter_idx,
    input_modifiers=[Jitter(0.05)],
    callbacks=[GifGenerator("activation_progress", input_range=(0, 255))],
)
```

| Component | Purpose | Activation-maximization guidance |
| --- | --- | --- |
| `Jitter(jitter=0.05)` | Randomly shifts the input before each gradient step and wraps pixels. | Often sharpens Conv filter and class prototype results. A scalar `< 1` is treated as a fraction of each image dimension; an integer-like value is pixels. |
| `GifGenerator(path, input_range=(0, 255))` | Writes optimization frames to a GIF. | Requires `imageio`; it appends `.gif` if absent. Treat file placement and image I/O as [image-utilities](../../image-utilities/SKILL.md) concerns. |
| Optimizer callbacks and custom modifiers | Advanced control over optimization. | See [optimization-building-blocks](../../optimization-building-blocks/SKILL.md) for internals and custom authoring. |

## Return value and shape

`visualize_activation` returns the optimized input without the batch dimension. If the backend uses `channels_first`, keras-vis moves the channel axis to the end before returning. For integer `input_range` endpoints the output is clipped and cast to `uint8`; for float endpoints it remains numeric float output in the requested range.