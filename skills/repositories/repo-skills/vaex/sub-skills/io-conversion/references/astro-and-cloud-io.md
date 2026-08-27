# Astro and Cloud IO

Astro formats and cloud/TAP paths are optional surfaces. This skill includes
local, safe guidance and skip conditions; bundled scripts intentionally do not
contact networks, cloud buckets, TAP servers, or credential stores.

## Optional plugin checklist

Before using these features, check imports in a user-authorized environment:

```python
import vaex

# HDF5 plugin
import vaex.hdf5

# Astro plugin for FITS/VOTable/TAP and coordinate helpers
import vaex.astro
```

If an import fails, install the corresponding Vaex distribution or optional
package set according to the root installation guidance, then retry a tiny local
fixture before attempting real data.

## Local FITS and VOTable workflows

Vaex's astro plugin registers local astronomy openers and accessors. Use it for
local files only by default.

```python
import vaex
import vaex.astro  # registers astro accessors/openers

df_fits = vaex.open("catalog.fits")
print(len(df_fits), df_fits.get_column_names())

df_vot = vaex.open("catalog.vot")
print(df_vot.get_column_names())
```

Local astro cautions:

- FITS opener support focuses on binary table/column-friendly layouts. Unsupported
  object-like columns, unusual dimensional metadata, or non-table HDUs can fail
  or be skipped.
- VOTable opener reads the first table and stores supported numeric, boolean,
  bytes/string, and similar column types. Object fields may be converted to
  strings or skipped.
- Column names may be sanitized or made Python-safe in some FITS paths. Always
  inspect `df.get_column_names()` after opening.
- FITS metadata such as units/UCDs can be present in Vaex dataset metadata, but
  downstream scripts should not assume all metadata survived conversion.
- Coordinate transformations such as `df.astro.eq2gal()` and virtual coordinate
  columns belong here only as local astro IO validation; expression-heavy or
  analytic workflows should route to `../expressions-analytics/SKILL.md`.

Tiny local validation example:

```python
import vaex
import vaex.astro

df = vaex.open("catalog.fits")
assert len(df) > 0
assert df.get_column_names()
# Pick a stable numeric column when available.
# print(df[df.get_column_names()[0]].count())
```

## TAP and SAMP boundaries

TAP and SAMP are network/integration workflows. They are not safe default
verification targets.

- TAP URLs use `tap+http...` or `tap+https...` style schemes and require network
  access to a remote astronomy service.
- TAP code may make metadata and chunked data requests as columns are accessed;
  it is not a simple local open.
- SAMP waits for external desktop/application events and is not appropriate for
  automated scripts unless the user explicitly sets up that workflow.

Skip TAP/SAMP by default when:

- The task is a general conversion/validation smoke test.
- No network authorization was given.
- Credentials, service quotas, or acceptable query limits are unclear.
- The user asked for local-only or reproducible CI behavior.

If the user explicitly authorizes TAP, first request the service URL, table name,
query/row limit, timeout, and cache/output policy. Record that remote data and
availability are outside this generated skill's local verification guarantee.

## Cloud path support overview

Vaex can open files from cloud/object storage when PyArrow/fsspec dependencies
and credentials are available.

Common schemes and options:

```python
import vaex

# Anonymous/public S3, if the bucket permits it.
df = vaex.open("s3://bucket/path/data.parquet", fs_options={"anon": True})

# S3 with explicit options. Prefer environment/profile-based credentials over
# embedding secrets in code.
df = vaex.open(
    "s3://bucket/path/data.hdf5",
    fs_options={"profile": "project", "region": "us-east-1", "cache": True},
)

# GCS anonymous or token-controlled access.
df = vaex.open("gs://bucket/path/data.parquet", fs_options={"token": "anon"})

# fsspec object supplied by the caller; useful for tests with in-memory FS.
# df = vaex.open("path/in/fs.parquet", fs=some_fsspec_filesystem)
```

Do not include real keys, tokens, signed URLs, private bucket names, or local
cache paths in public runtime files or logs.

## Cloud read/write caveats

- HDF5 remote reads may lazily download/cache byte ranges; subsequent access can
  be fast on the same machine, but the cache location is private state.
- Arrow and Parquet are generally better cloud interchange formats. Parquet is
  often preferred when storage size and network transfer cost matter.
- Writing remote HDF5 is limited; cloud writes are more practical for Arrow,
  Parquet, CSV, or multi-file outputs when the filesystem backend supports
  output streams.
- `df.export_many("s3://bucket/prefix/chunk_{i:05}.parquet", fs_options=...)`
  can be preferable to one large object, but requires explicit credentials and a
  failure/retry policy.
- Region mismatch can dominate performance. Prefer compute near the bucket for
  large remote analytics.

## Safe skip and diagnostic pattern

Use this pattern for future agents before any cloud/TAP action:

1. Confirm the path scheme (`s3`, `gs`, `fsspec+s3`, `arrow+s3`, `tap+http`,
   local path, etc.).
2. Confirm the user authorized network/credential use.
3. Check whether the needed optional packages are installed.
4. Run a metadata-only or tiny bounded operation first when supported.
5. Set timeouts/retry budgets outside Vaex if the execution harness supports
   them.
6. Never delete or overwrite remote objects unless explicitly requested.
7. If authorization is missing, stop with a clear skip reason and offer a local
   conversion/validation alternative.

Local alternative for cloud data:

```python
# User downloads or mounts a small sample locally first.
df = vaex.open("sample.parquet")
df.export_hdf5("sample_vaex.hdf5")
```

This keeps conversion logic testable without relying on cloud availability.
