# Components, Models, Listeners, and Workflow Primitives

This reference summarizes the Superduper component APIs that are useful for composing local AI workflows. It focuses on construction and routing behavior, not provider installation or vector nearest-neighbor internals.

## Core Component Contract

All user-facing workflow building blocks inherit from `Component`.

```python
from superduper import Component

component = Component(identifier="name", upstream=None, compute_kwargs={})
```

Important operating rules:

- `identifier` is required and must be non-empty. It becomes part of component metadata, human-readable IDs, output names, and apply/load calls.
- `upstream` is an optional list of components that must be applied before this component or that provide data consumed downstream.
- `compute_kwargs` is for a compute backend. Keep it empty unless a selected cluster/compute backend has already been configured.
- `component.component` is the class name, for example `ObjectModel`, `Listener`, or `Application`.
- `component.huuid` combines class, identifier, and a content hash; use it for debugging only, not as a stable user-facing name.
- `component.save()` requires `component.db` and calls `db.apply(component, jobs=False, force=True)`.

Use explicit `upstream` dependencies for workflows even when a component is nested inside another component. This makes apply order and failure propagation easier to reason about.

## ObjectModel and Model Basics

`Model` is the abstract base for components that can predict. `ObjectModel` is the usual local wrapper for a Python callable or an object's method.

```python
from superduper import ObjectModel

def normalize_text(text: str) -> str:
    return " ".join(str(text).split()).lower()

model = ObjectModel(
    identifier="normalize-text",
    object=normalize_text,
    datatype="str",
)
assert model.predict(" Hello   WORLD ") == "hello world"
assert model.predict_batches(["A", "B"]) == ["a", "b"]
```

Useful constructor fields:

| Class | Fields commonly set |
| --- | --- |
| `Model` | `identifier`, `datatype`, `predict_kwargs`, `num_workers`, `serve`, `trainer`, `validation`, `metric_values`, `compute_kwargs` |
| `ObjectModel` | all `Model` fields plus required `object` callable and optional `method` string |
| `QueryModel` | all `Model` fields plus `select`, optional `preprocess`, optional `postprocess`, and explicit `signature` |
| `APIBaseModel` | all `Model` fields plus provider/model name fields used by provider subclasses |

`ObjectModel` signature inference is based on the callable passed through `object=`:

| Callable shape | Inferred signature | Single `predict` call | Batch item shape | Listener `key` shape |
| --- | --- | --- | --- | --- |
| `f(x)` | `singleton` | `model.predict(value)` | each item is a value | string field name, or `None` to pass the whole document |
| `f(x, y)` | `*args` | `model.predict(x, y)` | each item is a list/tuple such as `(x, y)` | list/tuple of field names |
| `f(*, a=None, b=None)` or all-default params | `**kwargs` | `model.predict(a=..., b=...)` | each item is a dict | dict mapping parameter names to document field names |
| `f(x, *, scale=1)` or required plus default params | `*args,**kwargs` | `model.predict(x, scale=...)` | each item is `([positional_values], {"kw": value})` | `([positional_field_names], {"kw": "field_name"})` |

`predict_batches(dataset)` loops over the dataset and dispatches each item according to the model signature. Setting `num_workers` on a `Model` can parallelize local prediction, but the callable and all inputs must then be safe for multiprocessing.

Use `datatype` to describe the output stored by listeners. Common choices in this codebase include simple strings such as `"str"`, `"int"`, `"json"`, `"pickleencoder"`, `"dillencoder"`, `"array[float:10x10]"`, and `"vector[float:32]"`. Route vector-index design to `vector-search-and-retrieval`; keep only the producer/listener shape here.

## Listener Contract

A `Listener` binds a model to rows selected from a table/query and writes predictions to a managed output table.

```python
from superduper import Listener, ObjectModel

model = ObjectModel(identifier="double", object=lambda x: x * 2, datatype="int")
listener = Listener(
    identifier="double-x",
    model=model,
    select=db["documents"].select(),
    key="x",
)
db.apply(listener)
```

Constructor fields:

| Field | Meaning |
| --- | --- |
| `identifier` | Stable listener name. Also prefixes output IDs. |
| `model` | A `Model` component. `Listener.run` calls `model.predict_batches(inputs)`. |
| `select` | Query that returns source documents. `run` requires it; construction without a database may leave it `None`. |
| `key` | Input mapping from selected documents into the model signature. |
| `flatten` | If `True`, one list output is split into many output records. |
| `upstream` | Components that must exist or run before this listener. Use it for chained listeners. |
| `cdc_table` | Usually inferred from `select.table` when `select` is present. |

Listener key checks mirror model signatures:

```python
# singleton model: f(text)
Listener(identifier="clean", model=clean_model, select=table.select(), key="text")

# *args model: f(title, body)
Listener(identifier="join", model=join_model, select=table.select(), key=("title", "body"))

# **kwargs model: f(question=None, context=None)
Listener(
    identifier="answer",
    model=answer_model,
    select=table.select(),
    key={"question": "query", "context": "retrieved_context"},
)

# *args,**kwargs model: f(text, *, language="en")
Listener(
    identifier="translate",
    model=translate_model,
    select=table.select(),
    key=(["text"], {"language": "lang"}),
)
```

Output naming:

- `listener.predict_id` is a unique prediction id derived from the listener identifier and component hash.
- `listener.outputs` is the output table/field name and is prefixed by the configured output prefix, normally `_outputs__`.
- Downstream listeners should use `key=upstream_listener.outputs` and select from a query that includes the upstream output.
- Query helpers may ask for output ids; use `listener.predict_id` there, then read the resulting field using `listener.outputs`.

When a listener runs, it:

1. Checks that `key` matches `model.signature`.
2. Uses `select.missing_outputs(listener.predict_id)` when no explicit ids are provided.
3. Builds model inputs from selected documents.
4. Calls `model.predict_batches(inputs)`.
5. Inserts output documents into `db[listener.outputs]`.

If no ids are missing, or `select.subset(ids)` returns no documents, the listener logs a skip and writes nothing.

## Dataset, Metric, Validation, and Trainer

Use these components to scaffold training and validation while keeping the expensive training implementation in a custom `Trainer.fit` subclass.

```python
from superduper import Dataset, Metric, ObjectModel, Trainer, Validation

class MyTrainer(Trainer):
    def fit(self, model, db, train_dataset, valid_dataset):
        # mutate or replace model internals here; keep this deterministic in tests
        model.metric_values.setdefault("fit", []).append(len(train_dataset))
        return model

accuracy = Metric(identifier="accuracy", object=lambda preds, targets: sum(p == t for p, t in zip(preds, targets)) / len(targets))
valid = Dataset(identifier="valid-docs", select=db["documents"].select())
validation = Validation(identifier="validation", key=("features", "label"), datasets=[valid], metrics=[accuracy])
model = ObjectModel(
    identifier="classifier",
    object=lambda features: 1,
    datatype="int",
    trainer=MyTrainer(identifier="trainer", key="features", select=db["documents"].select()),
    validation=validation,
)
```

Key behaviors:

- `Dataset(select=...)` loads documents from a query when set up with a database.
- `Dataset(raw_data=..., pin=True)` can carry fixed in-memory data.
- `Metric(object=...)` is callable and receives full prediction and target sequences.
- `Validation(key=..., datasets=[...], metrics=[...])` maps dataset fields to model inputs and targets.
- `Model.fit_in_db` requires a `trainer`; it creates train and validation datasets using a `_fold` column with values `train` and `valid` when driven by a query.
- `Model.validate_in_db` writes metric results into `model.metric_values` and reapplies the model without jobs.

## Application Grouping

`Application` groups multiple components into a single component that can be applied, exported, encoded, or rebuilt as a workflow bundle.

```python
from superduper import Application

app = Application(
    identifier="document-pipeline",
    components=[table, clean_listener, score_listener],
)
db.apply(app)
```

Guidance:

- Include all components needed by the workflow, not transient listener output tables.
- Keep `upstream` on individual components; the grouping should not be the only place dependencies are encoded.
- `variables` and `template` support parametrized application builds. Use them when the same component graph is deployed with different table names or runtime values.

## Cron and Streamlit Components

`CronJob` and `FunctionCronJob` declare scheduled jobs. Their source notes mark cron deployment as an Enterprise/server feature, so local skills should describe them as component shapes unless the target deployment has the crontab service configured.

```python
from superduper import FunctionCronJob

def refresh_scores(db):
    # deterministic database maintenance logic here
    return None

job = FunctionCronJob(function=refresh_scores, schedule="0 * * * *")
```

`Streamlit` wraps a UI function and expects a Streamlit server/runtime.

```python
from superduper import Streamlit

def demo(db, title="Demo"):
    import streamlit as st
    st.title(title)

page = Streamlit(identifier="demo-page", demo_func=demo, demo_kwargs={"title": "Demo"})
```

Keep Streamlit and cron examples credential-free and avoid assuming the server service exists.
