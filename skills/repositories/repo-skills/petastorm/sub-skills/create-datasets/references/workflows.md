# Workflows

## Purpose

Read this when you need to create a new Petastorm dataset, copy or filter an existing one, regenerate metadata, or add row-group indexes.
The examples are intentionally tiny and local by default.

## 1) Create a new dataset from rows

1. Define a `Unischema` with the shapes and codecs you need.
2. Convert row dictionaries into Spark rows with `dict_to_spark_row`.
3. Wrap the Spark write in `materialize_dataset`.
4. Write Parquet to the target URL.
5. Read the result back with `make_reader` to confirm the metadata and shapes.

```python
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType
from petastorm.codecs import ScalarCodec, NdarrayCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row

Schema = Unischema("Schema", [
    UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
    UnischemaField("vector", np.float32, (2,), NdarrayCodec(), False),
])
```

### Practical notes

- Use `row_group_size_mb` to control the row-group size written by Spark.
- Use `filesystem_factory` when the filesystem object should be recreated on workers.
- The writer should run in a Spark job, not in a pure Python loop.

## 2) Copy or filter an existing dataset

1. Start from a Petastorm dataset URL.
2. Decide which columns should survive the copy with `field_regex`.
3. Decide which fields must remain non-null with `not_null_fields`.
4. Optionally repartition and tune the row-group size.
5. Read the copied dataset back to confirm the output shape.

```python
from petastorm.tools.copy_dataset import copy_dataset

copy_dataset(
    spark,
    source_url="file:///tmp/source",
    target_url="file:///tmp/target",
    field_regex=[r"^id$"],
    not_null_fields=[],
    overwrite_output=True,
    partitions_count=1,
    row_group_size_mb=1,
)
```

### When to use this path

- You want a smaller fixture for testing.
- You want to drop rows with missing values in selected fields.
- You want to repartition a dataset without changing the schema logic.

## 3) Regenerate metadata for an existing dataset

1. Open the dataset URL.
2. Let `generate_petastorm_metadata` infer the schema, or pass a fully qualified unischema class string.
3. Choose summary metadata only when the dataset and environment can support it.
4. Reopen the dataset with a reader to verify that the metadata is usable.

```python
from petastorm.etl.petastorm_generate_metadata import generate_petastorm_metadata

generate_petastorm_metadata(spark, "file:///tmp/target", use_summary_metadata=False)
```

### Common recovery rule

If the dataset is readable only as plain Parquet but not as Petastorm data, metadata repair is usually the right next step.

## 4) Build a row-group index

1. Choose the field(s) you want to accelerate.
2. Create a matching indexer, such as `SingleFieldIndexer` or `FieldNotNullIndexer`.
3. Call `build_rowgroup_index` with a Spark context.
4. On the read side, use a selector such as `SingleIndexSelector`.

```python
from petastorm.etl.rowgroup_indexers import SingleFieldIndexer
from petastorm.etl.rowgroup_indexing import build_rowgroup_index

indexers = [SingleFieldIndexer("id_index", "id")]
build_rowgroup_index("file:///tmp/target", spark.sparkContext, indexers)
```

### Caveat

Indexing reads the dataset and updates metadata, so it is a real Spark job and not a tiny pure-Python helper.

## 5) Resolve filesystem URLs

- Use `file://` for local directories.
- Use `hdfs://` for HDFS-backed datasets.
- Use `s3://` or `gs://` / `gcs://` only when the matching filesystem support is installed.
- Use `normalize_dir_url` to trim trailing slashes before storing URLs in configs or metadata.

## 6) Confirm the result

After any write-side workflow, the next check is usually one of these:

- `make_reader` on the written dataset
- `get_schema_from_dataset_url` to verify metadata
- `scripts/smoke_make_minimal_dataset.py` for a local end-to-end check
- `scripts/smoke_copy_dataset.py` for filter and copy flows
- `scripts/smoke_generate_metadata.py` for metadata repair
