# IO and Data Formats

## Text IO with `db.read_text`

Use `dask.bag.read_text` for text lines and line-delimited records:

```python
import json
import dask.bag as db

records = db.read_text("logs/*.json", blocksize="64 MiB").map(json.loads)
```

Important parameters:

| Parameter | Effect | Guidance |
| --- | --- | --- |
| `urlpath` | String, path-like, globstring, or list of paths | Lists must use the same protocol. No protocol means local filesystem. |
| `blocksize` | Splits uncompressed files into byte-sized partitions | Default `None` streams files. Use strings like `"64 MiB"` for large uncompressed files. Do not combine with `files_per_partition`. |
| `files_per_partition` | Groups many small files into each partition | Use for small-file overhead. Mutually exclusive with `blocksize`. |
| `compression` | Compression name or `"infer"` | Inferred from filename extensions. Use `blocksize=None` for typical compressed files. |
| `encoding` / `errors` | Text decoding behavior | Use `errors="ignore"` or `"replace"` only when data loss is acceptable. |
| `linedelimiter` | Text record delimiter | Supports custom delimiters; block splitting uses encoded delimiters when `blocksize` is set. |
| `include_path` | Emits `(line, path)` tuples | Useful for provenance, partition debugging, or deriving metadata from filenames. |
| `storage_options` | fsspec backend options | Pass cloud/auth/endpoint options here rather than hard-coding credentials into URLs. |

`read_text(..., collection=False)` returns delayed partition objects instead of a Bag. Use this when integrating with custom delayed workflows.

## Byte IO with `dask.bytes.read_bytes`

Use `read_bytes` when downstream code wants bytes rather than decoded strings:

```python
from dask.bytes import read_bytes
from dask import compute
from tlz import concat

sample, blocks = read_bytes("data/*.log", delimiter=b"\n", blocksize="128 MiB")
byte_chunks = compute(*concat(blocks))
```

`read_bytes` returns lazy delayed byte blocks. With a delimiter, Dask expands block boundaries so records are not split across chunks. This is a low-level building block for higher-level readers; prefer `db.read_text` for line-oriented text and `dask.dataframe.read_csv` for tabular CSV.

## fsspec URLs and Storage Options

Dask IO uses fsspec for local, network, cloud, and remote filesystems. Common protocols include:

| Protocol | Backend family | Notes |
| --- | --- | --- |
| no protocol / `file://` | Local or mounted filesystem | Simplest and always available. In distributed clusters, workers must see compatible paths. |
| `s3://` | Amazon S3 or compatible object stores | Usually requires `s3fs`. Prefer `storage_options` for `anon`, `key`, `secret`, `token`, `client_kwargs`, or endpoint settings. |
| `gcs://` / `gs://` | Google Cloud Storage | Usually requires `gcsfs`. |
| `abfs://`, `az://`, `adl://` | Azure storage | Usually requires `adlfs` and account options. |
| `hdfs://` | Hadoop filesystem | Usually depends on PyArrow or Hadoop configuration. |
| `http://`, `https://` | Web resources | Good for simple reads; authentication and range support depend on server/backend. |
| `hf://` | Hugging Face Hub datasets | Requires the relevant fsspec implementation. |

Do not put secrets into reusable skill content, logs, or examples. For user code, prefer environment/provider credentials or `storage_options` passed at runtime.

## Compression Behavior

- `compression="infer"` infers compression from filenames where possible.
- Common formats include gzip, bz2, xz, zip, and fsspec-registered codecs such as snappy or lz4 when installed.
- Most common compression formats do not support efficient random access. For `read_bytes`, chunked compressed reads raise with guidance to set `blocksize=None`.
- For `read_text`, use `blocksize=None` when reading compressed files unless the chosen codec and backend explicitly support safe splitting.
- `to_textfiles(..., compression="infer")` writes compressed output when the target filename extension indicates a known codec.

## JSON-like Records

For newline-delimited JSON, parse after `read_text`:

```python
import json
import dask.bag as db

raw = db.read_text("events/*.jsonl", blocksize="32 MiB")
parsed = raw.map(json.loads)
```

For malformed rows, wrap parsing and filter failures instead of letting one bad row fail the entire computation:

```python
def parse_or_error(line):
    try:
        return {"ok": True, "record": json.loads(line)}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": str(exc), "line": line.rstrip("\n")}

parsed = raw.map(parse_or_error)
good = parsed.filter(lambda row: row["ok"]).pluck("record")
bad = parsed.remove(lambda row: row["ok"])
```

Use `include_path=True` when error reporting must include the source file:

```python
raw = db.read_text("events/*.jsonl", include_path=True)
```

## Avro

`db.read_avro` and `Bag.to_avro` require the optional `fastavro` package.

```python
import dask.bag as db

records = db.read_avro("data/*.avro", blocksize=100_000_000)
```

Guidance:

- `read_avro` emits dictionary records according to the Avro schema.
- `blocksize=None` creates one partition per file.
- Externally compressed Avro files, such as `.avro.gz`, should use `blocksize=None` plus the appropriate `compression=` value.
- `to_avro` writes one file per bag partition and requires a fully specified Avro schema dictionary.
- Missing `fastavro` fails at use time with a dependency-specific import error.

## Writing Text Output

`Bag.to_textfiles` writes one output file per partition:

```python
import json

records.map(json.dumps).to_textfiles("out/part-*.jsonl", last_endline=True)
```

Notes:

- Convert non-string records to strings first.
- A glob `*` is replaced by partition numbers or `name_function(index)` values.
- `name_function` must preserve partition index ordering so output paths match partitions predictably.
- Set `compute=False` to return delayed write tasks for integration into a larger graph.
