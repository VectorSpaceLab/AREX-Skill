# Superduper API Overview

Use this reference as a route map for Superduper's public Python API. It summarizes verified live signatures and then points to deeper sub-skill references.

## Public import surface

The base package imports as `superduper` and exposes these main objects through its top-level module:

```python
from superduper import (
    superduper, CFG, Document, Schema, Table, Base,
    Component, Application, Dataset, Metric, Validation, Trainer,
    Model, ObjectModel, QueryModel, APIBaseModel, Listener, VectorIndex,
    Plugin, CronJob, FunctionCronJob, Streamlit,
    pickle_serializer, dill_serializer,
)
```

Verified signatures for common entry points:

| API | Signature / shape | Owned by |
| --- | --- | --- |
| `superduper` | `superduper(item: str | None = None, **kwargs) -> Any` | `datalayer-and-config` |
| `Document` | `Document(*args, schema=None, db=None, **kwargs)` | `datalayer-and-config` |
| `Schema` | `Schema(fields: Dict[str, BaseDataType])` | `datalayer-and-config` |
| `Table` | `Table(identifier, *, fields=None, primary_id="id", data=None, path=None, is_component=False)` | `datalayer-and-config` |
| `Component` | `Component(identifier, upstream=None, compute_kwargs=<factory>)` | `components-and-workflows` |
| `ObjectModel` | `ObjectModel(identifier, *, object, method=None, datatype=None, predict_kwargs=<factory>, validation=None, trainer=None, ...)` | `components-and-workflows` |
| `Model` | `Model(identifier, *, datatype=None, model_update_kwargs=<factory>, predict_kwargs=<factory>, validation=None, num_workers=0, serve=False, trainer=None, ...)` | `components-and-workflows` |
| `Listener` | `Listener(identifier, *, key, model, select=None, predict_kwargs=<factory>, flatten=False, cdc_table="")` | `components-and-workflows` and `vector-search-and-retrieval` |
| `VectorIndex` | `VectorIndex(identifier, *, indexing_listener, compatible_listener=None, measure="cosine", metric_values=<factory>)` | `vector-search-and-retrieval` |
| `Application` | `Application(identifier, *, components, variables=None, template=None)` | `components-and-workflows` |
| `Dataset` | `Dataset(identifier, *, select=None, sample_size=None, raw_data=None, schema=None, pin=False, ...)` | `components-and-workflows` |
| `Metric` | `Metric(identifier, *, object)` | `components-and-workflows` |
| `Trainer` | `Trainer(identifier, *, key, select, transform=None, in_memory=True, validation=None, ...)` | `components-and-workflows` |
| `Validation` | `Validation(identifier, *, metrics=<factory>, key, datasets=<factory>)` | `components-and-workflows` |
| `Plugin` | `Plugin(path, *, cache_path="~/.superduper/plugins", identifier="")` | `plugins-and-integrations` |

## Configuration and backend selection

`superduper()` constructs a `Datalayer` from process configuration. `superduper("scheme://...")` overrides `data_backend` with the given URI. Important defaults:

- `data_backend`: `mongodb://localhost:27017/test_db`
- `artifact_store`: `filesystem://./artifact_store`
- `metadata_store`: empty string, meaning metadata uses the main Datalayer
- `vector_search_engine`: `local`
- `cluster_engine`: `local`
- `output_prefix`: `_outputs__`

Primary URI routing:

| URI | Plugin/import family |
| --- | --- |
| `mongomock://`, `mongodb://`, `mongodb+srv://` | `superduper_mongodb` |
| `sqlite://`, `duckdb://`, `postgresql://`, `mssql://`, `mysql://` | `superduper_sql` |
| `snowflake://` | `superduper_snowflake` |
| `redis://` | `superduper_redis` |
| `inmemory://` | builtin `superduper.backends.inmemory` |
| `local`, `simple`, `inmemory` cluster engines | builtin backend packages |
| other plugin names | `superduper_<name>` |

Read `datalayer-and-config` before changing config or building a connection.

## Data, documents, and query APIs

Use `Document`, `Schema`, `Table`, `Base`, and `db["table"]` query objects to define and query records. Common query operations include `insert`, `select`, `filter`, `get`, `replace`, `update`, `delete`, `outputs`, `missing_outputs`, and `like`. Read `datalayer-and-config/references/query-and-data-model.md` for safe examples and mutation warnings.

## Component workflow APIs

Use `ObjectModel` for deterministic callable wrappers, `Listener` to apply a model over table/query fields, `Application` to group dependency-ordered components, and `Trainer`/`Validation`/`Metric`/`Dataset` for training/validation scaffolds. Read `components-and-workflows` before applying components or translating a RAG/application design into Superduper objects.

## Vector search APIs

A retrieval workflow normally builds:

1. an embedding `ObjectModel` or plugin model;
2. an indexing `Listener` with a table/query `select` and source `key`;
3. a `VectorIndex(identifier, indexing_listener=..., compatible_listener=..., measure=...)`;
4. a query such as `db["documents"].like({"query": value}, vector_index="index", n=10).select().execute()`.

Read `vector-search-and-retrieval` for dimensions, measures, compatible listeners, and local/vector DB troubleshooting.

## Plugin API and optional backends

First-party plugin packages follow a `superduper_<name>` import convention but package names vary (`superduper-chromadb` uses a hyphen, while many pyprojects use underscores). Read `plugins-and-integrations` for the plugin catalog, install choices, exported classes, and credential/service/GPU boundaries.

## CLI state

The distribution metadata declares a `superduper` console script, but this source snapshot has no `superduper.__main__`. Treat CLI invocations as unavailable until a refreshed source/package version proves otherwise.
