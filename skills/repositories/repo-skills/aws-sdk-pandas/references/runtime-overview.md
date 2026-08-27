# Runtime Overview

## Purpose

Read this when you need the public package identity, the install command, optional extras, or the basic runtime facts that apply to every `awswrangler` workflow.

## Verified package facts

- Distribution name: `awswrangler`
- Public version in this checkout: `3.17.1`
- Import name: `awswrangler`
- Python support advertised by the project metadata: `3.10` through `3.14`
- This package is a Python API library; no public CLI entry points were discovered in the repository metadata.
- Base dependencies required for import are the AWS SDK / dataframe stack:
  `boto3`, `botocore`, `pandas`, `numpy`, `pyarrow`, `typing-extensions`, and `packaging`.

## Install

Base install:

```bash
pip install awswrangler
```

Editable install in a local checkout:

```bash
pip install -e .
```

The editable form is useful for repo contributors; the released package form is what future users should normally install.

## Optional extras by workflow family

Install only the extras needed for the route you are using.

| Extra | When to install |
| --- | --- |
| `redshift` | Redshift connector/copy/unload workflows. |
| `mysql` | MySQL connector workflows. |
| `postgres` | PostgreSQL connector workflows. |
| `sqlserver` | Microsoft SQL Server connector workflows. |
| `oracle` | Oracle connector workflows. |
| `openpyxl` | Excel read/write helpers. |
| `deltalake` | Delta Lake read/write helpers on S3. |
| `pyiceberg` | S3 Tables / Iceberg helpers. |
| `opensearch` | OpenSearch client, indexing, and search workflows. |
| `gremlin` | Neptune Gremlin workflows. |
| `sparql` | Neptune SPARQL workflows. |
| `opencypher` | Neptune openCypher workflows. |
| `modin,ray` | Distributed `wr.engine` / `wr.memory_format` mode. |
| `geopandas` | Geospatial dataframe workflows. |

Examples:

```bash
pip install 'awswrangler[redshift]'
pip install 'awswrangler[modin,ray]'
pip install 'awswrangler[deltalake,openpyxl]'
```

## Runtime prerequisites

- Most workflows need an AWS region and credentials through the default boto3 session or an explicit `boto3.Session`.
- Many higher-level helpers are lazy about optional dependencies: the import can succeed, but the first call to a feature may raise `Missing optional dependency ...` if the extra is absent.
- `wr.config` exposes repository-wide defaults and environment-variable overrides via the `WR_*` namespace.
- Distributed mode is off by default unless `ray` and `modin` are installed or the environment explicitly sets the engine / memory format.

## Shared config names

The most common configuration names exposed by `wr.config` are:

- `catalog_id`
- `database`
- `workgroup`
- `chunksize`
- `concurrent_partitioning`
- `ctas_approach`
- `dtype_backend`
- `suppress_warnings`
- `athena_query_wait_polling_delay`
- `cloudwatch_query_wait_polling_delay`
- `neptune_load_wait_polling_delay`
- `timestream_batch_load_wait_polling_delay`
- `emr_serverless_job_wait_polling_delay`
- service endpoint overrides such as `s3_endpoint_url`, `athena_endpoint_url`, `glue_endpoint_url`, `redshift_endpoint_url`, `dynamodb_endpoint_url`, `secretsmanager_endpoint_url`, `timestream_query_endpoint_url`, and `timestream_write_endpoint_url`
- distributed controls such as `address`, `cpu_count`, `gpu_count`, `object_store_memory`, and `configure_logging`

Use `wr.config.to_pandas()` when you need the full list in a live environment.

## Distributed mode

If `modin` and `ray` are installed, the package can switch to distributed mode. The important public switches are:

```python
import awswrangler as wr

wr.engine.get()
wr.engine.set("python")
wr.engine.set("ray")
wr.memory_format.get()
wr.memory_format.set("pandas")
wr.memory_format.set("modin")
```

The default installed mode in a plain environment is `python` execution with `pandas` memory format.
