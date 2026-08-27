# Metadata Reference

This reference covers scikit-bio metadata objects and their serialization routes. Use it for QIIME-style sample/feature metadata files, dataframe-backed metadata, missing-data schemes, column extraction, filtering/merging, and interval annotations.

## SampleMetadata Construction

Verified constructor signature:

```python
SampleMetadata(dataframe, column_missing_schemes=None, default_missing_scheme="blank")
```

Basic construction:

```python
import pandas as pd
from skbio.metadata import SampleMetadata

df = pd.DataFrame(
    {"body_site": ["gut", "skin"], "age": [34.0, 29.0]},
    index=pd.Index(["sample-1", "sample-2"], name="id"),
)
metadata = SampleMetadata(df)
```

Rules enforced in memory:

- The dataframe index supplies metadata IDs and must contain at least one string ID.
- The index name must be a supported ID header.
- IDs must be non-empty, unique, and must not start with `#`.
- Column names must be non-empty, unique strings and must not use reserved ID-header names.
- Object/categorical columns may contain strings and missing values; numeric columns may contain integers/floats and missing values.
- Integer numeric columns are normalized to floating dtype in the stored dataframe.

## ID Header Rules

Supported case-insensitive ID headers:

- `id`
- `sampleid`
- `sample id`
- `sample-id`
- `featureid`
- `feature id`
- `feature-id`

Supported exact-match ID headers:

- `#SampleID`
- `#Sample ID`
- `#OTUID`
- `#OTU ID`
- `sample_name`

Reserved ID-header values cannot be reused as metadata IDs or metadata column names. If pandas construction fails with an ID-header error, set `df.index.name` to a supported value such as `id` and rename any conflicting columns.

## Loading and Saving Metadata TSV

`SampleMetadata` has a default write format of `sample_metadata`, so these patterns are equivalent when the target route is clear:

```python
from skbio import read, write
from skbio.metadata import SampleMetadata

metadata = read(handle, format="sample_metadata", into=SampleMetadata)
metadata = SampleMetadata.read(handle, format="sample_metadata")

write(metadata, format="sample_metadata", into=out_handle)
metadata.write(out_handle, format="sample_metadata")
```

`SampleMetadata.load(filepath, column_types=None, column_missing_schemes=None, default_missing_scheme="blank")` and `metadata.save(filepath, ext=None)` are convenience file-path APIs for metadata TSV workflows.

Metadata TSV parsing behavior:

- Leading and trailing whitespace in cells is stripped before validation.
- Comment rows begin with `#`, except supported directives and supported exact-match ID headers.
- Empty rows are ignored.
- The first non-comment, non-empty row must be a supported ID header row.
- Optional `#sk:types` or `#q2:types` directives must appear immediately below the header.
- Optional `#sk:missing` or `#q2:missing` directives must also appear in the directives section immediately below the header.
- The writer emits `#sk:types` and emits `#sk:missing` when any column uses a non-default missing scheme.

## Column Types and MetadataColumn Objects

Supported column types are `categorical` and `numeric`.

| Object | How to obtain | Notes |
| --- | --- | --- |
| `MetadataColumn` | Abstract/common base for columns | Exposes ID metadata, missing scheme, `to_dataframe`, `filter_ids`, and `drop_missing_values`. |
| `CategoricalMetadataColumn` | `metadata.get_column("name")` when the column is categorical | Values must be strings or missing; empty strings are invalid when constructing categorical columns directly. |
| `NumericMetadataColumn` | `metadata.get_column("name")` when the column is numeric | Values must be real numeric values or missing; positive/negative infinity and text are invalid. |

Useful methods:

```python
column = metadata.get_column("body_site")
column_df = column.to_dataframe()
without_missing = column.drop_missing_values()
subset_column = column.filter_ids(["sample-1"])
```

`metadata.columns` exposes column properties, including each column's type and missing scheme. Use those properties when generating validation reports or writing round-trip tests.

## DataFrame Conversion

Use `metadata.to_dataframe(encode_missing=False)` to get a normalized pandas dataframe. Pass `encode_missing=True` when the dataframe is intended for serialization and missing terms should be encoded according to the metadata missing schemes.

Practical pattern:

```python
df = metadata.to_dataframe()
selected = df.loc[["sample-1", "sample-2"], ["body_site", "age"]]
roundtripped = SampleMetadata(selected)
```

Preserve the index name when slicing or rebuilding metadata. Pandas operations can drop or mutate `Index.name`, which will cause constructor errors.

## Filtering and Merging

`SampleMetadata` methods enforce strict IDs to avoid silent sample mismatch:

| Task | API | Failure modes |
| --- | --- | --- |
| Keep selected IDs | `metadata.filter_ids(ids_to_keep)` | Empty keep-list, duplicate requested IDs, or missing requested IDs. |
| Keep selected columns | `metadata.filter_columns(column_type=None, drop_all_unique=False, drop_zero_variance=False, drop_all_missing=False)` | Invalid `column_type`; filtering that removes all columns may still preserve IDs depending on method semantics. |
| Extract one column | `metadata.get_column(name)` | Missing column name. |
| Merge metadata | `metadata.merge(other, *more)` | Conflicting IDs, duplicate columns, incompatible data, or no meaningful intersection depending on inputs. |

Safe merge workflow:

```python
left_ids = set(left.ids)
right_ids = set(right.ids)
shared = sorted(left_ids & right_ids)
if not shared:
    raise ValueError("No shared sample IDs to merge.")
merged = left.filter_ids(shared).merge(right.filter_ids(shared))
```

Before filtering a table or tree with metadata, compare IDs explicitly and decide whether missing IDs should fail, be dropped, or trigger a relabeling step.

## Missing-Data Schemes

Supported built-in missing schemes:

| Scheme | Meaning | Notes |
| --- | --- | --- |
| `blank` | Default; only blank/`None`/`NaN` values are missing. | Best default for most pandas-created metadata. |
| `no-missing` | Missing values are not allowed. | Construction/loading fails if the column contains missing values. |
| `INSDC:missing` | Encodes lower-case INSDC missing terms. | Recognized terms: `not applicable`, `missing`, `not collected`, `not provided`, `restricted access`. Case-sensitive. |

Constructor example:

```python
metadata = SampleMetadata(
    df,
    column_missing_schemes={"collection_note": "INSDC:missing"},
    default_missing_scheme="blank",
)
```

Troubleshooting principle: if a literal string such as `NA`, `N/A`, or `Missing` should be interpreted as missing, normalize it before construction or use a supported scheme term exactly.

## Interval and IntervalMetadata

Use interval metadata for genomic features and annotations that occupy coordinate spans. Core objects:

```python
from skbio.metadata import IntervalMetadata

intervals = IntervalMetadata(100)
gene = intervals.add(
    bounds=[(10, 30), (40, 50)],
    fuzzy=[(False, False), (False, False)],
    metadata={"type": "gene", "ID": "geneA", "strand": "+"},
)
```

Key rules:

- Bounds are zero-based, inclusive at the start and exclusive at the end.
- `IntervalMetadata(upper_bound)` binds coordinates to a sequence length; `upper_bound=None` can represent unbound annotations but cannot be merged into bound objects without care.
- `fuzzy` must match the number of bounds and stores uncertainty at each coordinate end.
- `IntervalMetadata.add(...)` creates and stores an `Interval`; `Interval.drop()` or `IntervalMetadata.drop(...)` removes intervals.
- `IntervalMetadata.query(bounds=..., metadata=...)` selects intervals by coordinate overlap and/or metadata predicates.
- `IntervalMetadata.concat([...])` concatenates annotations across adjacent sequences; `merge` combines compatible annotation sets.

GFF3 route notes:

- `read(handle, format="gff3", into=IntervalMetadata, seq_id="...")` selects one sequence ID from a GFF3 file.
- GFF3 can also stream `(seq_id, IntervalMetadata)` pairs when the whole file contains multiple sequence IDs.
- Sequence formats such as GenBank and EMBL may populate `interval_metadata` on sequence objects.

Route interval-aware sequence operations to `../sequences-alignment/SKILL.md` after annotations are attached.
