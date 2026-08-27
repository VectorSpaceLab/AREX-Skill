# optimization-building-blocks customization guide

Use these building blocks when a caller needs explicit control over the optimization loop instead of the high-level visualization helpers.

## 1. Decide the target tensor

- If you want to optimize the model input directly, leave `wrt_tensor=None`.
- If you want gradients with respect to an internal activation, pass that tensor as `wrt_tensor`.
- When `wrt_tensor` is the same object as `input_tensor`, `Optimizer` inserts a copied identity tensor so the graph can still build gradients cleanly.
- When `wrt_tensor` is different, the optimization loop does **not** update the seed input. In that mode, use the run as a gradient inspection pass, not an input synthesis loop.

## 2. Assemble losses

Common low-level losses:
- `ActivationMaximization(layer, filter_indices)` for filter or class output maximization.
- `TotalVariation(model.input)` for smoother images.
- `LPNorm(model.input)` for bounded magnitude.

Combine them as `[(loss, weight), ...]`.

Rules of thumb:
- Zero-weight losses are ignored at construction time.
- Loss names show up in the built-in `Print` callback.
- The sign of the weight is part of the objective design; `ActivationMaximization` itself returns a minimization-friendly loss.

## 3. Choose modifiers

### Gradient modifiers

Use these when you want to reshape the update signal without changing the underlying graph:
- `negate`: visualize decrease instead of increase.
- `absolute`: default saliency-style magnitude view.
- `invert` / `small_values`: emphasize tiny gradients.
- `relu`: keep only positive gradient values.

### Input modifiers

Use these when the seed should be transformed before and after each update:
- `Jitter` is the canonical modifier.
- Run `pre()` before the update step and `post()` in reverse order afterward.
- Keep the modifier list short and deterministic for reproducible smoke tests.

### Backprop modifiers

Use these only for TensorFlow graph-mode models that need guided or rectified propagation:
- `guided` gates gradients by positive activations and positive upstream gradients.
- `rectified`/`relu`/`deconv` gates only positive gradients.

These are graph-level rewrites, not post-hoc numpy transforms.

## 4. Pick callbacks

- `Print` is the default visibility aid.
- `GifGenerator` is for frame capture only when optional image dependencies are installed.

A callback should be used when you need either:
- a running loss trace,
- final cleanup via `on_end()`, or
- frame capture across iterations.

## 5. Understand the update loop

`Optimizer.minimize()` follows this order:
1. apply each `InputModifier.pre()`
2. evaluate the compiled Keras function
3. reshape gradients if backend output shape drifts from the target tensor shape
4. run the gradient modifier
5. run callbacks
6. RMSProp-style update when the target is the input tensor
7. apply `InputModifier.post()` in reverse order
8. keep the best input seen so far

Implications:
- Input modifiers can influence both the evaluated loss and the cached best input.
- `callbacks` observe the post-modified gradients, not raw gradients.
- `norm_grads=False` is the right choice when you want the actual gradient magnitude.

## 6. TensorFlow caveats

Guided and rectified backprop in TensorFlow depend on legacy graph mechanics.

Practical constraints:
- Use graph mode behavior; eager-style execution is not the target for this code path.
- Model cloning is done through temporary save/load with a gradient override map.
- Advanced activations are not handled by the TensorFlow rewrite path and should be treated as unsupported here.
- The backprop override is only meaningful for ops that pass through the modified `Relu` gradient registration.
- The code maintains a cache per `(model, backprop_modifier)` pair, so repeated calls may reuse the modified graph.

## 7. Loss weighting and RMSProp tuning

The optimizer is intentionally simple:
- no momentum term beyond the RMSProp cache
- no learning-rate schedule
- no early stopping criterion

If results are noisy:
- reduce the regularizer weights first
- try a smaller `max_iter`
- inspect `named_losses` with `verbose=True`
- add or adjust `Jitter`

If the optimized tensor barely changes:
- set `norm_grads=False` only for inspection
- lower regularization weights
- confirm the selected `wrt_tensor` is actually being updated
