# Activation maximization troubleshooting

This page covers the failure modes owned by activation maximization. For custom optimizer internals, use [optimization-building-blocks](../../optimization-building-blocks/SKILL.md). For saliency and Grad-CAM failures, use [saliency-and-cam](../../saliency-and-cam/SKILL.md).

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` when importing `keras` or `vis` | Legacy Keras/TF dependencies are missing or incompatible | Use the legacy runtime expected by keras-vis 0.5.0: standalone Keras 2.2.x with TensorFlow 1.x graph mode. Do not switch to `tensorflow.keras` for this skill. |
| `AttributeError` or `ModuleNotFoundError` around TensorFlow graph/session helpers | TensorFlow 2.x eager execution or incompatible backend API | Use a Keras 2.2.x + TF 1.x environment. If you are only probing the environment, stop at the smoke script and fix the runtime first. |
| Output looks like noise or gray mush | Regularizers dominate the activation objective | Re-run with `verbose=True`, lower `lp_norm_weight` and `tv_weight`, or temporarily set them to `0.0`. |
| Output is crisp but not related to the target class | Final Dense layer still uses softmax | Switch the final Dense activation to linear and rebuild the graph with `utils.apply_modifications`. |
| Regression output does not move in the expected direction | Wrong gradient direction | Use `grad_modifier="negate"` to decrease a regression output. |
| `TypeError` from multiplying a loss by `None` | A built-in weight was passed as `None` | Use `0.0` rather than `None` to disable a built-in regularizer in keras-vis 0.5.0. |
| `ValueError` or `IndexError` around `filter_indices` | The requested class/unit/filter index is outside the layer output range | Check `get_num_filters(model.layers[layer_idx])` before looping or indexing. |
| `No layer with name ...` | The layer lookup name is wrong | Use `utils.find_layer_idx(model, layer_name)` after inspecting `model.layers`. |
| `Jitter value should be positive` or shape mismatch in `Jitter` | Negative or wrong-dimensional jitter specification | Pass a nonnegative scalar or a sequence whose length matches the number of image dimensions. |
| `ImportError: Failed to import imageio. You must install imageio` | GIF callback dependency missing | Install `imageio`, or skip `GifGenerator` and use the numeric smoke workflow instead. |
| `ImportError: Failed to import PIL. You must install Pillow` | Text overlay helpers are missing Pillow | Route text overlay and image export to [image-utilities](../../image-utilities/SKILL.md) or install Pillow in the target runtime. |
| Gradient computation returns nothing useful | `wrt_tensor` points somewhere other than the input tensor or the chosen layer is not connected to the input | Keep `wrt_tensor=None` for normal activation maximization. For advanced graph routing, move to [optimization-building-blocks](../../optimization-building-blocks/SKILL.md). |

## Import and legacy dependency failures

The smoke script reports import failures explicitly so future agents can stop early instead of debugging model code against the wrong runtime.

Example recovery sequence:

```bash
python sub-skills/activation-maximization/scripts/activation_smoke.py --target dense --max-iter 1
```

If the script prints import advice, confirm the backend and versions before touching the model.

Recommended legacy checks:

- Standalone `keras` imports without `tensorflow.keras`.
- TensorFlow graph mode available to Keras.
- `numpy`, `h5py`, `Pillow`, and `imageio` installed when the chosen workflow uses them.

## Model and objective failures

### Softmax head still active

If the final Dense layer still uses softmax, the objective is usually weaker than the class-logit version.

Fix:

1. Locate the output layer.
2. Replace the activation with `linear`.
3. Rebuild the graph with `utils.apply_modifications(model)`.
4. Re-run activation maximization.

### Wrong target type

- Dense classification: use the output class index.
- Dense regression: use the output dimension index and consider `grad_modifier="negate"` for a decrease probe.
- Conv filter: use the channel/filter index inside the chosen Conv layer.

### Over-regularization

Symptoms include loss values that barely move, a bland output, or a target that appears to be completely suppressed by the prior.

Try this order:

1. Set `verbose=True`.
2. Reduce `lp_norm_weight` and `tv_weight`.
3. Increase `max_iter`.
4. Add `Jitter(0.05)`.
5. Use a coarse pass with no regularizers, then seed a second pass from the coarse image.

### Seed input problems

When the model is regression-heavy or the gradient is weak, random noise may not be enough.

Use a representative seed image or a known good partial synthesis as `seed_input`.

Rules to remember:

- The seed may omit the batch dimension.
- The seed must still match the backend channel ordering.
- `seed_input` is clipped back to `input_range` at the end.

## Modifier and callback failures

### Gradient modifier names are wrong

Use the identifiers exposed by `vis.grad_modifiers`:

- `negate`
- `absolute`
- `invert`
- `relu`
- `small_values`

Pass a callable only when the task explicitly needs custom gradient post-processing.

### Backprop modifier errors

Backprop modifiers change the model graph. If a task does not ask for guided or rectified backprop, leave `backprop_modifier=None`.

If the model contains custom layers or unusual graph nodes, first confirm the plain activation-maximization workflow works before adding a backprop modifier.

### GIF generation fails

`GifGenerator` needs `imageio` and a writable destination path.

If the run only needs numeric confirmation, drop the GIF callback and rely on the smoke script output or the final synthesized array.

## Output-format surprises

- Integer `input_range` endpoints return clipped `uint8` output.
- Float endpoints keep float output.
- `channels_first` inputs are moved back to channels-last before return.

If a downstream consumer expects a different shape or dtype, adapt the consumer instead of changing the activation-maximization objective.