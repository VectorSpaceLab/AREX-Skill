# Modeling/data troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ShapeError` when calling `pm.set_data` | New value rank changed, or dimension length conflicts with registered coords. | Keep rank unchanged and pass replacement `coords` for any resized named dimension. |
| Coordinate length changed but outputs still use old labels | Data value was replaced without new coordinates. | Call `pm.set_data({"x": new_x}, coords={"obs_id": new_labels})` inside the model context. |
| `Variables that depend on other nodes cannot be used for observed data` | Observed value is symbolic and depends on graph nodes. | Use data-like observed values; if designing custom likelihood logic, route to `distributions-logprob`. |
| Duplicate or invalid variable name | A model variable or coord already uses that name. | Rename variables/dimensions; inspect `model.named_vars` and `model.coords`. |
| Unexpected `*_unobserved` variables | Missing observed values triggered imputation. | Decide whether imputation is intended; otherwise clean observed data before model construction. |
| Compiled logp expects `sigma_log__` instead of `sigma` | Value variable transform for constrained RV. | Use `model.initial_point()` keys or map RVs to values with model helpers. |
| Graphviz render failure | Optional Python/system Graphviz missing. | Install Graphviz packages or inspect textual registries instead. |

When debugging predictions after data updates, first fix model/data shape with this sub-skill, then use `inference-predictive` for `sample_posterior_predictive(predictions=True)` and group validation.
