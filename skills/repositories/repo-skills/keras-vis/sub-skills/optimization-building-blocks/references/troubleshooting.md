# optimization-building-blocks troubleshooting

Start from the smallest scope that can fail: import, custom loss construction, optimizer construction, one optimization step, then optional callbacks or backprop modifiers.

## Import and environment problems

### `keras`, `tensorflow`, or `scipy` import failures

Likely causes:
- incompatible legacy Keras/TensorFlow pairing
- missing SciPy for `Jitter`
- missing `imageio` or Pillow for GIF output

Actions:
1. Confirm the Python environment already contains a legacy Keras 2.x + TensorFlow 1.x stack.
2. Import `vis.optimizer` and `vis.losses` before testing callbacks.
3. Import `vis.input_modifiers` only after confirming SciPy is present.
4. Import `vis.callbacks` only when GIF output is needed.

### Protobuf or TensorFlow graph bootstrap errors

This code path depends on TensorFlow 1.x style graph behavior.

Symptoms:
- default-graph errors
- `gradient_override_map` failures
- protobuf-related import or descriptor crashes before model creation

Actions:
- Use a TensorFlow 1.x compatible runtime.
- Do not try to validate TensorFlow backprop modifiers in eager mode.
- If the environment is using a newer protobuf that breaks the graph runtime, fix the TensorFlow import stack before debugging `Optimizer` itself.

## Custom loss failures

### `Loss.build_loss()` raises `NotImplementedError`

This means the subclass did not override `build_loss()`.

Actions:
- Override `build_loss()` and return a tensor expression.
- Give the subclass a descriptive `name` so `Print` output is readable.

### Loss builds but gradients are `None`

Likely causes:
- the loss tensor is disconnected from `input_tensor` or `wrt_tensor`
- the chosen tensor is not part of the model graph
- the loss uses unsupported Python-side control flow

Actions:
1. Confirm the tensor passed to `Optimizer` is actually in the graph.
2. Verify `wrt_tensor` is reachable from the loss expression.
3. Reduce the custom loss to a single backend reduction before adding complexity.

## Optimizer construction failures

### Weight tuples appear to have no effect

Likely causes:
- weight is zero, so the loss is skipped
- the loss is numerically tiny compared with regularizers
- the wrong tensor is selected for the objective

Actions:
- Inspect `loss_names` and `named_losses` with `verbose=True`.
- Temporarily set regularizer weights to zero.
- Use a tiny synthetic model to confirm each loss term contributes.

### `wrt_tensor` does not update the input

This is expected when `wrt_tensor` is not the same object as `input_tensor`.

Actions:
- Treat the run as a gradient/feature probe.
- If you want actual input synthesis, leave `wrt_tensor=None` or point it to the input tensor.
- Check `Optimizer.wrt_tensor_is_input_tensor`.

## Input modifier failures

### `Jitter` raises a shape mismatch

Likely causes:
- jitter length does not match the number of image dimensions
- the input tensor shape is not what the modifier expects

Actions:
- Pass one scalar or one jitter value per image dimension.
- Confirm the model uses the image shape you think it does.
- Remember the percentage-to-pixel conversion happens on first `pre()` call and is then cached.

### `Jitter` gives unexpected wrapping artifacts

This is expected behavior: the modifier uses wrap-around shifts.

Actions:
- Reduce jitter magnitude.
- Try a deterministic seed input to make the effect easier to see.

## Gradient modifier failures

### `invert` produces very large values

This is caused by division by tiny gradient values.

Actions:
- Use `small_values` only when you explicitly want this magnification.
- Consider `absolute` or `negate` first.
- If gradients are near zero, inspect the model/loss choice rather than the modifier.

### `relu` mutates the array in place

This is by design.

Actions:
- Pass a copied array if you need to preserve the original gradient values.

## Backprop modifier failures

### Guided/rectified backprop does not change results

Likely causes:
- the model uses unsupported advanced activations
- the model did not rebuild under the override map
- the backend is not TensorFlow graph mode
- the selected layer path does not exercise `Relu`

Actions:
1. Confirm the model uses plain ReLU paths.
2. Retest on a tiny Sequential model with Dense + ReLU.
3. Compare original and modified gradients on a positive/negative input pair.
4. If the model uses advanced activations, treat this path as unsupported.

### `modify_model_backprop()` fails inside temporary save/load

Likely causes:
- save path permission issues
- corrupted model serialization
- incompatible Keras/TensorFlow version pair

Actions:
- Confirm temporary directory write permission.
- Try a minimal model first.
- Do not assume this is a graph problem until save/load itself succeeds.

## Callback failures

### `GifGenerator` raises `ImportError`

`imageio` is missing.

Actions:
- Install `imageio` and Pillow, or omit the GIF callback.
- Use `Print` instead when only text traces are needed.

### `GifGenerator` fails to write frames

Likely causes:
- image frames are not in a drawable format
- Pillow is missing or cannot load image data
- output path is unwritable

Actions:
- Confirm the input range is compatible with integer image output.
- Test `utils.draw_text()` separately if font rendering is the failure point.
- Use a writable `.gif` path.

## Smoke-test failures

When the bundled smoke script is added to this sub-skill, it should catch import and backend errors before a real optimization run.

Interpretation:
- import failure: environment problem, not a loss-definition problem
- optimizer construction failure: inspect loss tensor or `wrt_tensor`
- optimization failure after one step: check graph mode, gradient availability, or callback dependencies
