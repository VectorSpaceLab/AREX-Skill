# optimization-building-blocks API reference

This reference covers the low-level optimization primitives exposed by `keras-vis`.

## Losses

### `vis.losses.Loss`

Abstract base class for a custom minimization objective.

- `Loss.__init__()` sets `name = "Unnamed Loss"`.
- Override `build_loss()` and return a Keras tensor expression.
- `__str__()` returns `name`.

Constraints:
- `build_loss()` must be expressible with backend tensor ops, not Python scalars.
- Use `utils.slicer` and `utils.get_img_shape()` when you need backend-agnostic channel indexing.

### `vis.losses.ActivationMaximization(layer, filter_indices)`

Builds a negative-mean loss over selected filter or dense output indices.

- `layer`: Keras layer whose output is optimized.
- `filter_indices`: scalar or sequence; normalized with `utils.listify()`.
- Dense layers use `layer_output[:, idx]`.
- Convolutional layers use `layer_output[utils.slicer[:, idx, ...]]`.

Behavior:
- Lower loss means higher activation.
- Dense `softmax` layers often work better if replaced with linear activation before optimization.

## Regularizers

### `vis.regularizers.TotalVariation(img_input, beta=2.)`

Encourages smoother, blob-like images.

- `beta` is typically in the `1.5` to `3.0` range.
- Smaller `beta` values produce sharper but spikier images.
- Computes an N-D total variation penalty normalized by image size.
- Uses `utils.slicer` and `utils.get_img_shape()` so the same code works with both data formats.

### `vis.regularizers.LPNorm(img_input, p=6.)`

Encourages bounded pixel intensity.

- `p` must be at least `1`.
- `p=float('inf')` uses max norm.
- The returned value is normalized by image size.

## Optimizer

### `vis.optimizer.Optimizer(input_tensor, losses, input_range=(0, 255), wrt_tensor=None, norm_grads=True)`

Creates a weighted-loss optimizer around a Keras graph.

Arguments:
- `input_tensor`: model input tensor.
- `losses`: list of `([Loss](#losses), weight)` tuples.
- `input_range`: final output range used by `utils.deprocess_input()`.
- `wrt_tensor`: tensor to differentiate against. Defaults to `input_tensor`.
- `norm_grads`: whether to L2-normalize gradients before the update step.

Important behavior:
- Loss terms with weight `0` are skipped entirely.
- `self.wrt_tensor_is_input_tensor` is set only when the exact same tensor is used.
- If `input_tensor is wrt_tensor`, the implementation inserts `K.identity()` before building `K.function()`.
- `self.compute_fn` returns `[loss_1, ..., overall_loss, grads, wrt_value]`.

### `Optimizer.minimize(seed_input=None, max_iter=200, input_modifiers=None, grad_modifier=None, callbacks=None, verbose=True)`

Runs the optimization loop.

Returns:
- `(optimized_input, grads, wrt_value)`

Loop details:
- `seed_input` is expanded to batch shape if needed.
- `input_modifiers` run in list order via `pre()` and reverse order via `post()`.
- `grad_modifier` may be a string or callable; `vis.grad_modifiers.get()` resolves strings.
- `verbose=True` appends the bundled `Print` callback.
- `OptimizerCallback.callback()` runs before the update step.
- When optimizing with respect to a non-input tensor, the input array is not updated; the method still returns gradients and the target tensor value.
- The update step is RMSProp-like: `cache = decay * cache + (1-decay) * grads**2`, `step = -grads / sqrt(cache + epsilon)`.

## Input modifiers

### `vis.input_modifiers.InputModifier`

Base class with no-op `pre()` and `post()` hooks.

### `vis.input_modifiers.Jitter(jitter=0.05)`

Applies wrap-around spatial jitter before each update.

Constraints:
- Scalar or sequence input is accepted.
- Negative jitter raises `ValueError`.
- Percentages below `1.0` are interpreted relative to image dimensions.
- The effective offsets are cached after first preprocessing.
- Uses SciPy `shift(..., mode='wrap', order=0)`.

## Callbacks

### `vis.callbacks.OptimizerCallback`

Base callback with:
- `callback(i, named_losses, overall_loss, grads, wrt_value)`
- `on_end()`

### `vis.callbacks.Print`

Prints iteration number, named losses, and overall loss.

### `vis.callbacks.GifGenerator(path, input_range=(0, 255))`

Writes frames to a GIF.

Constraints:
- `imageio` is required; otherwise construction raises `ImportError`.
- Pillow support is also required indirectly because frames are passed through `utils.draw_text()`.
- Appends `.gif` automatically when missing.

## Gradient modifiers

### `vis.grad_modifiers.get(identifier)`

Resolves a string or callable modifier.

Built-ins:
- `negate(grads)` → `-grads`
- `absolute(grads)` → `np.abs(grads)`
- `invert(grads)` → `1. / (grads + K.epsilon())`
- `relu(grads)` → clips negative values to zero in place
- `small_values(grads)` → `absolute(invert(grads))`

Notes:
- `relu()` mutates the provided array.
- `small_values()` is often used to highlight tiny saliency responses.

## Backprop modifiers

### `vis.backprop_modifiers.guided(model)`

Returns a modified copy of the model that uses guided backpropagation in TensorFlow.

### `vis.backprop_modifiers.rectified(model)`

Returns a modified copy with rectified/deconv-style backprop.

### Aliases
- `vis.backprop_modifiers.relu`
- `vis.backprop_modifiers.deconv`

Important caveats:
- The TensorFlow implementation relies on `tf.get_default_graph().gradient_override_map(...)`.
- Advanced activations are not supported by the TensorFlow model-rewrite path here.
- Theano backprop modification is intentionally not implemented.
- The modifier cache is keyed by the original model object and modifier name.
