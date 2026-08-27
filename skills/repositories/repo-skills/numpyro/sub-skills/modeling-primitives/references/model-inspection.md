# Model inspection

Inspect model behavior on tiny inputs before running expensive inference. This catches site-name, shape, support, and handler-composition mistakes early.

## Trace a model

```python
from jax import random
from numpyro import handlers

seeded = handlers.seed(model, random.key(0))
tr = handlers.trace(seeded).get_trace(*args, **kwargs)
for name, site in tr.items():
    value = site.get("value")
    print(name, site["type"], getattr(value, "shape", ()), site.get("is_observed"))
```

Use this to answer:

- Which sample/param/deterministic sites exist on this execution path?
- Which sites are observed?
- Which plates are active for each site?
- Are values finite and shaped as expected?

## Check shape text with `format_shapes`

`numpyro.util.format_shapes(trace)` formats a trace into a human-readable table. It is especially useful after a plate/to_event error.

```python
from numpyro.util import format_shapes
print(format_shapes(tr))
```

If shape text shows an unexpected extra event dimension, route distribution-object debugging to `../distributions-transforms/`. If plate dimensions collide or observation axes are missing, stay here and fix `plate(..., dim=...)` placement.

## Model relation utilities

`numpyro.infer.inspect.get_model_relations(model, model_args=None, model_kwargs=None)` and `get_dependencies(...)` summarize dependencies among sample and deterministic sites. Use them for model-review tasks where the user needs to understand parent/child structure or conditional dependencies.

```python
from numpyro.infer.inspect import get_model_relations
relations = get_model_relations(model, model_args=(x,), model_kwargs={"y": y})
print(relations.keys())
```

## Rendering a model graph

`numpyro.render_model(model, model_args=..., model_kwargs=..., render_distributions=True)` renders a graph representation when Graphviz support is installed. Graph rendering is optional: if `graphviz` is missing, keep using traces and relation dictionaries.

```python
import numpyro

graph = numpyro.render_model(
    model,
    model_args=(x,),
    model_kwargs={"y": y},
    render_distributions=True,
)
# In notebooks graph displays directly. In scripts, save through Graphviz APIs when available.
```

Do not make a future workflow depend on Graphviz unless the user explicitly wants visualization.

## Trace without inference: conditioned check

```python
from jax import random
from numpyro import handlers

observed = handlers.condition(model, {"obs": y})
seeded = handlers.seed(observed, random.key(0))
tr = handlers.trace(seeded).get_trace(x)
assert tr["obs"]["is_observed"]
assert tr["obs"]["value"].shape == y.shape
```

This pattern is useful when the user asks for a model audit, a predictive-shape check, or a guide/model signature comparison.

## What to inspect before routing to inference

- Site names and whether latent/observed status matches the intended model.
- Distribution object support and event shape for each site.
- Plate stack and `dim` assignments for each batched site.
- Deterministic values that downstream diagnostics or predictions need.
- Whether model execution performs downloads, file I/O, plotting, or Python-side mutation; remove those from model execution.
- Whether every JAX array branch/loop is compatible with JAX control flow.
