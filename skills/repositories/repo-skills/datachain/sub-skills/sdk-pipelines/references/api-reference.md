# SDK API Reference

This reference summarizes DataChain's public SDK surfaces used by this skill.
Use it for parameter names and return-shape decisions; keep long query-function
details in sibling `query-engine`.

## Imports and Public Names

Prefer:

```python
import datachain as dc
```

The top-level package exports the main chain, model, file, UDF, query, and
reader entry points: `DataChain`, `DataModel`, `File`, `ImageFile`, `TextFile`,
`AudioFile`, `VideoFile`, `C`, `func`, `llm`, `read_storage`, `read_dataset`,
`read_values`, `read_csv`, `read_json`, `read_parquet`, `read_database`,
`read_records`, `read_pandas`, `read_hf`, and related helpers.

## Reader Entry Points

All `read_*` functions return a lazy `DataChain`.

| API | Use for | Important parameters |
| --- | --- | --- |
| `dc.read_storage(uri, *, type="binary", recursive=True, column="file", update=False, anon=None, delta=False, delta_on=(...), delta_compare=None, delta_retry=None, client_config=None)` | Object storage, local paths, and file-like sources. | `type` selects `File` subclass: `binary`, `text`, `image`, `video`, `audio`. Use trailing `/` for bucket/prefix URIs. `anon=True` for public buckets when you want to avoid credential probing. |
| `dc.read_dataset(name, namespace=None, project=None, version=None, delta=False, update=False, ...)` | Existing saved datasets by name/version. | Versions may be exact strings, PEP-style ranges, or legacy ints. Use fully qualified names when namespace/project ambiguity matters. |
| `dc.read_values(**fr_map)` | Tiny fixtures, literal columns, smoke tests. | Useful for examples and tests that avoid storage/network. |
| `dc.read_records(records, schema=...)` | Python dictionaries or objects with explicit schema. | Use when existing in-memory records need stable typed columns. |
| `dc.read_csv`, `dc.read_json`, `dc.read_parquet` | Structured files from storage or local filesystem. | JSON supports `jmespath`; CSV infers column types; Parquet supports glob/Hive-like layouts. |
| `dc.read_database(query, connection, params=...)` | SQLAlchemy-compatible databases. | Use parameterized queries for user-supplied values. |
| `dc.read_pandas(df)` | In-memory pandas dataframes. | Prefer DataChain-native operations after reading. |
| `dc.read_hf`, `dc.read_zarr` | Hugging Face and Zarr integrations. | May require optional dependencies, network, or dataset access. |

## Chain Processing Verbs

### `map`

`DataChain.map(func=None, params=None, output=None, **signal_map) -> DataChain`

Use for one output row per input row with Python callables, stateful `Mapper`s,
or `datachain.llm` specs. Examples:

```python
import datachain as dc

# Best: annotation supplies output type.
def ext(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()

chain = dc.read_storage("s3://bucket/images/", anon=True)
chain = chain.map(ext=ext, params=["file.path"])

# Non-str lambda needs output=.
chain = dc.read_values(x=[1, 2]).map(y=lambda x: x + 1, output={"y": int})
```

### `gen`

`DataChain.gen(func=None, params=None, output=None, **signal_map) -> DataChain`

Use for one input row to many output rows. A generator UDF should have an
iterator return annotation or an explicit `output=`.

```python
from collections.abc import Iterator
import datachain as dc

def parts(path: str) -> Iterator[str]:
    yield from [p for p in path.split("/") if p]

rows = dc.read_values(path=["a/b.txt"]).gen(part=parts, params=["path"])
```

### `agg`

Use Python aggregators only when SQL aggregates are insufficient. Native
`group_by` aggregates are usually faster and belong to `query-engine`.

### `setup`

Use `.setup(name=lambda: resource)` to initialize heavy resources inside worker
processes. UDF parameters can receive setup values by name.

```python
def score(text: str, model) -> float:
    return model.score(text)

chain.setup(model=lambda: load_model()).map(score=score)
```

## Save, Persist, and Dataset Metadata

| API | Use for | Notes |
| --- | --- | --- |
| `.save(name, version=None, description=None, attrs=None, update_version="patch")` | Named, versioned, reusable datasets. | Default for UDF-bearing and final pipeline stages. Attach descriptions and attrs for knowledge-base clarity. |
| `.persist()` | Anonymous materialization within one script. | Useful when the same expensive chain feeds multiple downstream branches but should not become a named shared dataset. |
| `dc.datasets()`, `dc.delete_dataset()`, `dc.move_dataset()` | Dataset management from Python. | Prefer CLI for simple interactive maintenance. |
| `dc.metrics.set/get`, `dc.param()` | Metrics and runtime parameters. | Metrics attach to dataset versions; params are captured in lineage. |

## Export and Terminal APIs

| API | Output | Notes |
| --- | --- | --- |
| `.to_pandas()` | pandas DataFrame | Use only for subsets that fit memory. Prefer native query operations for grouping/filtering. |
| `.to_csv(path)`, `.to_json(path)`, `.to_jsonl(path)`, `.to_parquet(path)` | File plus terminal execution | Nested models flatten into dotted column names for flat formats. |
| `.to_database(table, connection, on_conflict=..., column_mapping=...)` | SQL database table | Use `column_mapping` to rename or omit exported columns. |
| `.to_storage(output, signal="file", placement="fullpath", link_type="copy", anon=None, client_config=None)` | File payload export | Placement strategies include `filename`, `filepath`, `fullpath`, and `etag`; `checksum` is reserved. |
| `.to_values(*cols)`, `.to_list(*cols)`, `.to_iter(*cols)` | Python values/tuples | Use for small display/assertion tasks. Do not bypass `.save()` for expensive UDF results. |
| `.to_pytorch(...)` | PyTorch dataset | Requires `datachain[torch]`; import errors should point to that extra. |
| `.show(limit=...)`, `.count()` | Display or scalar | Good for quick inspection after saving. |

## LLM Operations

`datachain.llm` functions return specs used inside `.map()` or `.gen()`:

```python
from datachain import llm

llm.complete(col, prompt=None, *, schema=None, context=None, type=None,
             llm=None, retries=1, fallback=None, include_usage=False, **params)
llm.classify(col, into, prompt=None, *, context=None, type=None,
             llm=None, retries=1, fallback=None, include_usage=False, **params)
llm.score(col, prompt=None, *, context=None, type=None, llm=None,
          retries=1, fallback=None, include_usage=False, **params)
llm.embed(col, *, llm=None, retries=1, fallback=None,
          include_usage=False, **params)
```

Set the default model with `.settings(llm="provider/model")`. Per-call `llm=`
overrides it. `include_usage=True` emits a value plus `dc.llm.Usage` when named
with multi-output `output={...}`.

## Toolkit and Optional Extras

- `from datachain.toolkit import train_test_split` returns a list of split
  chains from a source chain and weight list.
- `datachain.torch` requires `datachain[torch]` and exposes helpers such as
  `PytorchDataset`, `convert_image`, `convert_text`, and CLIP utilities.
- Optional groups include `torch`, `audio`, `remote`, `vector`, `hf`, `video`,
  `postgres`, `zarr`, `docs`, `tests`, `dev`, and `examples`. Install only the
  groups needed for the selected workflow.
