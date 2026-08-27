---
name: bag-bytes-workflows
description: "Use for Dask Bag, dask.bytes, text/byte IO, JSON-like records,
  Avro, fsspec storage, compression, foldby/frequencies, and small-file
  deterministic workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dask Bag and Bytes Workflows

Use this sub-skill when an agent needs to build, debug, or explain Dask workflows around unordered Python objects, text lines, byte blocks, semi-structured records, and filesystem-backed small-file pipelines.

## Route Here For

- Creating bags with `dask.bag.from_sequence`, `read_text`, `read_avro`, `from_delayed`, `concat`, `map`, and `map_partitions`.
- Reading and writing local, cloud, compressed, text, byte, newline-delimited JSON, and Avro-like data with `dask.bag` or `dask.bytes`.
- Using bag reductions such as `frequencies`, `fold`, `foldby`, `distinct`, `topk`, and `count` without forcing dataframe shuffles too early.
- Converting bags to `dask.dataframe` with explicit `meta`, or to per-partition delayed values for custom outputs.
- Diagnosing partition sizing, delimiters, compression inference, `storage_options`, optional Avro dependencies, ordering surprises, and heterogeneous records.

## Route Elsewhere

- Use `dataframe-workflows` for dataframe-first analytics, joins, parquet/CSV dataframe IO, divisions, and dataframe groupby/shuffle tuning.
- Use `core-graphs-schedulers` for generic task graph, delayed, scheduler, `compute`, `persist`, and graph-optimization questions.
- Use `configuration-diagnostics-cli` for Dask configuration, CLI, diagnostics, dashboard, and environment-level reporting.

## Start With These References

- `references/api-reference.md` for public bag/bytes APIs and when to choose each one.
- `references/io-and-data-formats.md` for text, bytes, fsspec URLs, compression, Avro, and storage behavior.
- `references/workflows.md` for practical recipes, including malformed JSON rows and explicit dataframe metadata.
- `references/troubleshooting.md` for common failures and fixes.

## Bundled Smoke Check

Run `python scripts/bag_text_smoke.py --help` to inspect options. Run `python scripts/bag_text_smoke.py` to create a temporary newline-JSON fixture, parse it through Dask Bag, tolerate malformed rows, count records by status, convert to a dataframe with explicit `meta`, and clean up automatically.

## Core Operating Rules

- Keep bag pipelines lazy; do not call `compute()` or `persist()` while defining collection transformations unless the user explicitly wants a local result.
- Prefer `foldby` over `groupby` for per-key reductions because `groupby` performs a full shuffle.
- Treat bags as unordered collections. Sort only after computing or after converting to dataframe when deterministic presentation matters.
- Pass explicit `meta` to `Bag.to_dataframe` for heterogeneous records, empty first partitions, or production code where inference would be expensive or incorrect.
- Use `blocksize=None` for compressed text/bytes unless the compression format supports random access; chunked reads on typical gzip/bz2/xz streams fail or behave poorly.
