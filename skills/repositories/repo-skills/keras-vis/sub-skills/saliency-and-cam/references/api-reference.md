# API Reference

Validated against `keras-vis 0.5.0`.

## Core functions

| Function | Exact signature | Default behavior | Return shape | Notes |
| --- | --- | --- | --- | --- |
| `visualize_saliency` | `visualize_saliency(model, layer_idx, filter_indices, seed_input, wrt_tensor=None, backprop_modifier=None, grad_modifier='absolute', keepdims=False)` | Computes gradients for a single layer output, optionally applies a backprop modifier, then applies a gradient modifier | `keepdims=False` collapses the channel axis to a spatial heatmap; `keepdims=True` keeps the sample-squeezed input shape | Use for classification, multi-label, regression increase/decrease/maintenance, and guided or rectified saliency |
| `visualize_saliency_with_losses` | `visualize_saliency_with_losses(input_tensor, losses, seed_input, wrt_tensor=None, grad_modifier='absolute', keepdims=False)` | Uses custom weighted losses with optional `wrt_tensor` | `keepdims=False` collapses channels; `keepdims=True` keeps the sample-squeezed tensor shape | This helper does not take `backprop_modifier`; route new loss construction to `../optimization-building-blocks/SKILL.md` |
| `visualize_cam` | `visualize_cam(model, layer_idx, filter_indices, seed_input, penultimate_layer_idx=None, backprop_modifier=None, grad_modifier=None)` | Finds a nearby penultimate convolutional or pooling layer unless overridden | Spatial heatmap matched to the input spatial dimensions | Use when the model has a close spatial layer before the target and you want Grad-CAM |
| `visualize_cam_with_losses` | `visualize_cam_with_losses(input_tensor, losses, seed_input, penultimate_layer, grad_modifier=None)` | Uses a resolved penultimate layer object and custom losses | Spatial heatmap matched to the input spatial dimensions | Lower-level helper; the caller resolves the penultimate layer first |

## Modifier values

### `grad_modifier`

Common identifiers for these workflows:

- `absolute` — default for saliency helpers; takes `np.abs(grads)`.
- `relu` — clips negative gradients to zero.
- `negate` — flips gradient sign so negative gradients become positive signals.
- `small_values` — highlights low-magnitude gradients via reciprocal magnitude.
- a callable that accepts and returns a NumPy gradient array.

The package also exposes a lower-level `invert` modifier, but the saliency/CAM recipes usually use the four values above.

### `backprop_modifier`

Allowed identifiers in this release:

- `guided` — guided backpropagation.
- `rectified` — rectified / deconv-style backpropagation.
- `relu` and `deconv` are aliases for `rectified`.
- a callable accepted by `vis.backprop_modifiers.get`.

## Penultimate-layer selection

`visualize_cam` searches backward from `layer_idx` for the nearest `Conv` or `Pooling` layer and skips wrapper layers while searching.

- If no suitable layer is found, the helper raises a `ValueError`.
- If a manual `penultimate_layer_idx` is after `layer_idx`, the helper raises a `ValueError`.
- If the model is dense-only or the spatial layer is too far from the target, use saliency instead.

## Shape notes

- Saliency heatmaps are normalized after the channel collapse or the `keepdims=True` path.
- CAM heatmaps are built from the penultimate feature maps, ReLU-thresholded, zoomed to the input spatial size, and normalized.
- For non-image regression inputs, prefer `keepdims=True` so the feature axis is preserved.
- For image inputs with `channels_first` or `channels_last`, the returned heatmap drops the batch dimension.

## Useful sign conventions

- Saliency defaults to "increase the target output".
- `grad_modifier='negate'` shows decrease in a regression target.
- `grad_modifier='small_values'` highlights features that preserve the current prediction.
- `visualize_saliency_with_losses` is the right entry point when the explanation target is already encoded as a weighted loss list.
