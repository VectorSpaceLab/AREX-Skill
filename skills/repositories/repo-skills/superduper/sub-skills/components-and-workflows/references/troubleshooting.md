# Components and Workflows Troubleshooting

Use this guide when a Superduper component workflow constructs successfully but fails at apply time, writes no listener output, produces unusable downstream fields, or cannot be serialized.

## Fast Triage Checklist

1. Confirm every component has a non-empty `identifier`.
2. Call each `ObjectModel.predict(...)` directly before wrapping it in a listener.
3. Compare `model.signature` with the listener `key` shape.
4. Confirm `select` is a query that returns the fields named by `key`.
5. For chained listeners, use `upstream_listener.outputs` as the downstream field and include the upstream output in the downstream query.
6. Match `datatype` to the callable's actual return value.
7. Prefer top-level functions/classes over lambdas, nested closures, open handles, active clients, or local-only objects.
8. Treat cron, Streamlit pages, `serve=True`, and provider/API models as server or plugin responsibilities unless their runtime is explicitly configured.

## Common Symptoms and Fixes

| Symptom | Likely cause | Repair |
| --- | --- | --- |
| `Identifier cannot be empty or None` | `Component`, `ObjectModel`, `Listener`, or `Application` was created without a stable identifier. | Pass `identifier="readable-name"` explicitly. For `FunctionCronJob`, either pass an identifier or use a named top-level function. |
| ObjectModel construction fails for a callable | Missing required `object=` argument or callable is not callable after serialization/setup. | Use `ObjectModel(identifier="...", object=callable, datatype="...")`; prefer a top-level function or a small callable class. |
| `Invalid lookup key ... for model signature ...` | Listener `key` does not match `model.signature`. | For `singleton`, use a string or `None`; for `*args`, use a tuple/list of field names; for `**kwargs`, use a dict from parameter names to field names; for `*args,**kwargs`, use `([pos_fields], {kw: field})`. |
| Listener writes nothing | No missing ids, `select` returns no documents, `select.subset(ids)` is empty, or `select` is not the table/query containing the intended fields. | Run the select independently, check row count and field names, then verify `select.missing_outputs(listener.predict_id)` is non-empty before expecting outputs. |
| Downstream listener cannot find an upstream output | Downstream `select` does not include the upstream output id, or downstream `key` uses `predict_id` where the document field name is required. | Build the query with the upstream output id and set `key=upstream_listener.outputs`. Read the field using `upstream_listener.outputs`. |
| Output table name is surprising or too long | Listener output names are generated from a truncated identifier plus component hash and the configured output prefix. | Do not hard-code the generated table/field. Store the listener object and use `listener.outputs` and `listener.predict_id`. |
| Output rows contain one list per source row when individual rows were expected | `flatten` is `False` but the model returns a list of records. | Set `flatten=True` on the listener when each element of a list output should become its own output record. |
| Serialization fails or reloaded component behaves differently | Callable captures local state, an open file/client, a dynamically defined class, or a non-deterministic object. | Move logic into a top-level function or class with stable imports and simple fields; initialize clients in `setup()` or prediction code rather than storing live handles. |
| Component hash changes unexpectedly | Object state, callable closure contents, or class hashing is unstable. | Use deterministic callables/classes; for custom classes, define stable fields and avoid mutable hidden state in hashing-sensitive components. |
| Listener output cannot be stored or decoded | `datatype` does not match actual callable output. | Use `"str"`/`"int"` for scalar values, `"json"` for JSON-compatible dict/list outputs, `"pickleencoder"` or `"dillencoder"` for Python objects, and route vector-index design separately. |
| Validation metrics are empty or not updated | `validation`, `datasets`, `metrics`, or dataset `key` mapping is missing or mismatched. | Ensure `Validation(key=(input_key, target_key), datasets=[...], metrics=[...])` is attached to the model and that each dataset loads documents with those fields. |
| Training job sees no rows | The selected training data is empty or the automatic split expects `_fold` values. | Confirm `trainer.select.execute()` returns rows; if relying on split behavior, include `_fold="train"` and `_fold="valid"` rows. |
| Cron job component constructs but does not run | Cron deployment needs the crontab/server service. | Use `CronJob`/`FunctionCronJob` only as component declarations unless the Enterprise/server runtime is configured. |
| Streamlit page constructs but cannot be served | Streamlit runtime/server is not available or the demo imports optional packages. | Keep `demo_func` small and explicit; install/configure Streamlit outside this sub-skill route. |
| `serve=True` does not route remotely | A compute cluster/service is not configured on the Datalayer. | Leave `serve=False` for local workflows, or configure compute/cluster through the datalayer/config route before enabling serving. |

## Listener Select/Key Mismatch Workflow

When listener outputs are missing:

```python
# 1. Inspect the model signature.
print(listener.model.signature)

# 2. Inspect the key shape.
print(listener.key)

# 3. Run the select without the listener.
rows = listener.select.execute()
print(len(rows), rows[0] if rows else None)

# 4. Confirm the selected row has every field named in the key.
# 5. For downstream listeners, confirm the query includes the upstream output.
print(upstream_listener.outputs, upstream_listener.predict_id)
```

Repair examples:

```python
# Wrong: downstream field uses predict_id as a document key.
Listener(identifier="bad", model=model, select=db[source.outputs].select(), key=source.predict_id)

# Right: use the output field/table name as the document key.
Listener(identifier="good", model=model, select=db[source.outputs].select(), key=source.outputs, upstream=[source])
```

If the downstream query uses a helper that accepts output ids, pass `source.predict_id` to the query helper and still use `source.outputs` as the listener `key`.

## Datatype Mismatch Workflow

A downstream failure often starts with an upstream callable returning a different type than declared.

```python
from superduper import ObjectModel

def returns_dict(text):
    return {"length": len(text)}

# Risky: declared as a string but returns a dict.
bad = ObjectModel(identifier="bad", object=returns_dict, datatype="str")

# Better: JSON-compatible output.
good = ObjectModel(identifier="good", object=returns_dict, datatype="json")
```

Diagnosis steps:

1. Call `model.predict(sample)` and inspect the exact Python type.
2. Call `model.predict_batches([...])` to confirm batch shape.
3. Choose a datatype that can encode that type.
4. Rebuild listeners that depend on the model so their output table schema matches.
5. Update downstream keys and models to consume the actual decoded value.

## Non-Serializable Function or Artifact Workflow

Prefer:

```python
def score_text(text):
    return len(str(text))

model = ObjectModel(identifier="score-text", object=score_text, datatype="int")
```

Avoid:

```python
client = make_live_client()          # external handle
model = ObjectModel(
    identifier="score-text",
    object=lambda text: client.score(text),  # captures non-portable state
    datatype="int",
)
```

If a model needs external resources, store only simple configuration on the component and create the resource at runtime in `setup()` or inside `predict`, with explicit error messages for missing credentials or services. Provider installation and credentials belong outside this sub-skill.

## Enterprise or Server-Only Surfaces

These components can be declared locally but should not be treated as verified execution paths unless the deployment service is configured:

- `CronJob` / `FunctionCronJob`: needs crontab/server integration.
- `Streamlit`: needs a Streamlit server/runtime.
- `Model(serve=True)`: needs a configured compute cluster.
- External API/provider models: need plugin packages, credentials, and network access.

For local smoke tests, replace external or server-backed models with deterministic `ObjectModel` stand-ins.
