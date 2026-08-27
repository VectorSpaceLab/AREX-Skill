# Profiling and numerical comparison

Profiling answers two different questions:

1. **Range selection:** Are weights and activations covered by the fixed-point ranges in the current hls4ml config?
2. **Numerical parity:** Do the generated hls4ml C-simulation outputs match the original frontend model closely enough after quantization and graph optimizations?

The profiling stack requires the profiling optional dependencies (`hls4ml[profiling]`). Those dependencies were available during the live checks for this skill.

## Main APIs

```python
from hls4ml.model.profiling import numerical, compare

figs = numerical(model=frontend_model, hls_model=hls_model, X=X, plot="boxplot")
# returns: (weights_before, weights_after, activations_before, activations_after)

fig = compare(frontend_model, hls_model, X, plot_type="dist_diff")
```

Accepted `numerical()` inputs:

- `model`: Keras model or PyTorch module.
- `hls_model`: converted hls4ml `ModelGraph`.
- `X`: representative test data, already formatted exactly as the frontend model expects. hls4ml does not normalize or reformat user data automatically.
- `plot`: the implemented plot styles in this checkout are `boxplot` and `histogram`; `boxplot` is the default.

When `hls_model` is provided, `numerical()` produces HLS-side views for an unoptimized clone and the final optimized `ModelGraph`. This matters because optimizer passes can fuse or remove layers: for example, BatchNormalization may be folded into a preceding Dense layer, so the correct precision target is the post-optimization HLS graph rather than the raw frontend layer list.

## Interpreting profiling figures

- Weight plots show non-zero weights and biases by layer/variable.
- Activation plots require `X` and show layer output distributions.
- Grey range boxes, when an HLS model is provided, show the current representable fixed-point range.
- Make sure the right side of the grey box covers observed values to avoid overflow. If the box is too shallow on the left, increase fractional precision only if accuracy or parity demands it.
- A profile is a starting point, not proof. Validate edited configs with CPU `compile()`/`predict()` parity and, when required, backend C simulation.

## Trace output for layer-by-layer comparison

Layer-by-layer HLS traces require per-layer trace selection in the config. A common pattern is:

```python
config = hls4ml.utils.config_from_keras_model(model, granularity="name", backend=backend)
for layer_cfg in config["LayerName"].values():
    layer_cfg["Trace"] = True

# Convert with the traced config, then:
hls_model.compile()
pred, trace = hls_model.trace(X)
```

Operational details:

- `Trace=True` in `LayerName` selects which layer outputs are collected.
- `hls_model.trace(X)` recompiles with trace output enabled and returns `(prediction, trace_dict)`.
- `trace_dict` keys are traced layer names and values are NumPy arrays over samples.
- `compare(keras_model, hls_model, X, plot_type="dist_diff")` compares Keras intermediate outputs against `hls_model.trace(X)`. Use `plot_type="norm_diff"` when you need one norm value per traced layer.
- If no layer has tracing enabled, HLS activation profiling can raise a runtime error because the trace dictionary is empty.

## Practical profiling recipe

1. Start from a representative sample batch. Keep batch size small enough for fast CPU C-simulation but large enough to expose typical activation ranges.
2. Generate a `granularity="name"` config with the backend specified so backend-specific precision attributes are visible.
3. Mark only the layers you need with `Trace=True`; tracing every layer is useful for debugging but increases compile/run overhead.
4. Run `numerical(model=model, hls_model=hls_model, X=X)` and inspect whether weight and activation ranges are covered.
5. If parity fails, use `compare()` with `dist_diff` or `norm_diff` to localize the first layer whose output diverges.
6. Change one precision or resource knob at a time, then rerun the same parity check.

## PyTorch notes

The PyTorch profiling helpers can profile weights from modules and activations from simple sequential child-module flows. For complex custom modules, prefer conversion-time layer inspection plus HLS tracing for the exact generated layer names, and route frontend data-layout questions to the `frontends` sub-skill.
