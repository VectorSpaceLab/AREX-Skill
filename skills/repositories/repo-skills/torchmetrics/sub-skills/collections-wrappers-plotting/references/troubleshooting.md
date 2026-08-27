# Collections, wrappers, and plotting troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `MetricCollection` rejects duplicate names | A list contains duplicate metric classes or generated keys collide | Use a dict with explicit unique names or add prefixes/postfixes. |
| A collection update fails for only one member | Metrics in the collection do not share a compatible update signature | Split them into separate collections or pass kwargs that match each metric's signature. |
| Computed values have unexpected prefixes or postfixes | The collection or nested collection added naming transforms | Inspect `collection.keys(keep_base=True)` and the configured prefix/postfix. |
| Train and validation values contaminate each other | The same metric collection instance is reused for multiple streams | Use `clone(prefix=...)` to create independent metric state per stream. |
| `MetricTracker` says `increment` was not called | Tracking starts only after a step/epoch is created | Call `tracker.increment()` before every tracked step or epoch. |
| `MetricTracker` cannot infer `maximize` | The metric lacks `higher_is_better` or the collection is nested | Pass `maximize=True/False` or a list of booleans matching collection outputs. |
| `ClasswiseWrapper` output labels look wrong | Labels do not match class order or the base metric is not per-class | Use a base metric with `average=None` and pass labels in model class order. |
| `MinMaxMetric` fails on a dict or vector | The base metric output is not scalar | Wrap only scalar metrics or reduce/flatten outputs yourself. |
| `BootStrapper` output is not loggable as one scalar | Bootstrap returns mean/std/quantile/raw fields | Flatten the dict with stable names before logging. |
| Plotting fails in a notebook-free or server session | Matplotlib is missing, the backend needs a display, or the installed science style depends on missing TeX packages | Install the visual extra, set `matplotlib.use('Agg')` before importing pyplot, and force the default style or disable `text.usetex` if the science style is present but TeX is unavailable. |
| `science` style or LaTeX warnings appear | SciencePlots or LaTeX is unavailable | Use the default matplotlib style or install the plotting extras and LaTeX separately if publication style is required. |
| A model-backed metric inside a wrapper triggers a download | The wrapped metric belongs to a model-backed family | Route cache/device/download planning to `../model-based-metrics/` first. |
