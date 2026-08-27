# Visualization and UI Troubleshooting

## Missing helper imports

**Symptom:** `show()` and `plot()` work, but `close()`, `load_scalars()`, or
`plot_scalars()` are missing.

**Likely cause:** the caller used `from phi.flow import *` only.

**Recovery:** import the visualization module explicitly:

```python
import phi.vis as vis
```

`phi.flow` re-exports the most common plotting helpers, but the more specialized
figure, histogram, and scalar-log functions live in `phi.vis`.

## Stale `view()` examples

**Symptom:** an old notebook or doc tries to call `view()`.

**Likely cause:** the docs are from an older visualization API.

**Recovery:** replace the call with `show()` or `plot()` from `phi.vis`.
This version does not expose a public `view()` symbol.

## `control()` errors

**Symptom:** `control()` raises an assertion about the calling context.

**Likely cause:** `control()` was called outside an assignment statement.

**Recovery:** use top-level script assignment syntax, for example:

```python
learning_rate = vis.control(1e-3, (1e-5, 1e-1))
```

Only primitive `int`, `float`, `bool`, and `str` values are supported.

## Plotting backend mismatch

**Symptom:** Matplotlib plots work but Plotly or the web UI does not.

**Likely cause:** the optional `plotly` or `dash` dependency is missing.

**Recovery:** install the missing optional package and rerun the smoke helper.

## Scalar log loading failures

**Symptom:** `load_scalars()` cannot find the curve.

**Likely cause:** the scene does not contain a `log_<name>.txt` file or the
curve name is wrong.

**Recovery:** confirm the scene path and the exact log filename, then re-run the
helper or recreate the scene log with the expected prefix.

## Deprecated scalar plotting wrapper

**Symptom:** `plot_scalars()` emits a deprecation warning.

**Likely cause:** the convenience wrapper is still in use.

**Recovery:** prefer `load_scalars()` plus `plot()` in new code. Keep
`plot_scalars()` only when you need the old wrapper semantics.
