# Bag and Bytes Workflows

## Choose Bag vs DataFrame vs Delayed

Use Bag when records are Python objects or semi-structured data and early transformations are embarrassingly parallel. Use DataFrame once records have stable columns and typed analytics matter. Use Delayed when each partition needs custom non-collection logic or side effects controlled by user code.

| Need | Best starting point |
| --- | --- |
| Text lines, JSON logs, dictionaries, arbitrary Python objects | `dask.bag` |
| CSV/parquet/table analytics, joins, dataframe groupby | `dask.dataframe` |
| Custom per-file loaders that return Python lists | `dask.delayed` + `db.from_delayed` |
| Raw binary chunks or custom parser boundaries | `dask.bytes.read_bytes` |

## Deterministic Small-file Text Workflow

For many tiny text files, avoid one task per line and reduce per-file overhead by grouping files:

```python
import json
import dask.bag as db

raw = db.read_text("incoming/*.jsonl", files_per_partition=25, include_path=True)


def parse_pair(pair):
    line, path = pair
    try:
        record = json.loads(line)
        record["source_path"] = path
        return {"ok": True, "record": record}
    except json.JSONDecodeError as exc:
        return {"ok": False, "source_path": path, "error": str(exc), "line": line.rstrip("\n")}

parsed = raw.map(parse_pair)
good = parsed.filter(lambda row: row["ok"]).pluck("record")
bad = parsed.remove(lambda row: row["ok"])
```

For deterministic user-facing output, compute to local data only when it is small and then sort by stable keys such as filename and event id. Do not rely on bag iteration order as a semantic guarantee.

## Malformed Newline JSON with Storage Options

For remote or authenticated storage, keep backend details in `storage_options`:

```python
import json
import dask.bag as db

storage_options = {"anon": True}
raw = db.read_text(
    "s3://example-bucket/events/*.jsonl.gz",
    compression="gzip",
    blocksize=None,
    include_path=True,
    storage_options=storage_options,
)


def parse_json(pair):
    line, path = pair
    try:
        return {"valid": True, "path": path, "record": json.loads(line)}
    except json.JSONDecodeError as exc:
        return {"valid": False, "path": path, "error": str(exc), "raw": line.rstrip("\n")}

rows = raw.map(parse_json)
valid_records = rows.filter(lambda row: row["valid"]).pluck("record")
invalid_rows = rows.remove(lambda row: row["valid"])
```

Use `blocksize=None` above because gzip streams are not generally splittable. For uncompressed JSONL, set `blocksize="64 MiB"` or similar to split large files while preserving newline boundaries.

## Counts and Per-key Aggregation

Use `frequencies` for direct value counts:

```python
status_counts = valid_records.pluck("status", default="missing").frequencies(sort=True)
```

Use `foldby` for efficient per-key reductions without collecting every group:

```python
def add_amount(total, record):
    return total + record.get("amount", 0)

amount_by_user = valid_records.foldby(
    key="user_id",
    binop=add_amount,
    initial=0,
    combine=lambda left, right: left + right,
    combine_initial=0,
)
```

Reach for `groupby` only when the downstream code truly needs all records per key, because it requires a full shuffle.

## Converting Heterogeneous Dicts to DataFrame

When bag records are irregular, normalize them and pass explicit metadata:

```python
import dask.bag as db

records = db.from_sequence(
    [
        {"user": "alice", "amount": 10},
        {"user": "bob", "amount": None, "country": "US"},
        {"user": "carol", "country": "CA"},
    ],
    npartitions=2,
)


def normalize(record):
    return {
        "user": record.get("user"),
        "amount": record.get("amount", 0),
        "country": record.get("country", "unknown"),
    }

meta = {"user": "object", "amount": "float64", "country": "object"}
df = records.map(normalize).to_dataframe(meta=meta)
```

Explicit `meta` avoids sampling the first partition, prevents failures when the first partition is empty, and fixes column order/dtypes before dataframe operations begin.

## Per-file Custom Loader with `from_delayed`

Use delayed for custom file parsing that naturally returns a list per file:

```python
from dask import delayed
import dask.bag as db


def load_records(path):
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle if line.strip()]

parts = [delayed(load_records)(path) for path in sorted(paths)]
bag = db.from_delayed(parts)
```

Each delayed value becomes one partition, so choose path grouping deliberately when there are many small files.

## Raw Byte Blocks for Custom Parsers

Use `read_bytes` when records are not text lines or when a custom byte delimiter is needed:

```python
from dask.bytes import read_bytes

sample, blocks = read_bytes("data/*.bin", delimiter=b"<END>", blocksize="32 MiB", sample=False)
```

The nested `blocks` structure is grouped by file. Flatten it only when per-file grouping is no longer needed.

## Writing Partitioned Outputs

For text:

```python
valid_records.map(json.dumps).to_textfiles("cleaned/part-*.jsonl", last_endline=True)
```

For delayed integration:

```python
writes = valid_records.map(json.dumps).to_textfiles("cleaned/part-*.jsonl", compute=False)
```

For dataframe analytics, convert first and then use dataframe-native writers:

```python
df = valid_records.map(normalize).to_dataframe(meta=meta)
# Route parquet/csv dataframe output decisions to dataframe-workflows.
```
