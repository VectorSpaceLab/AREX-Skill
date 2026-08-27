---
name: "petastorm"
description: "Routes Petastorm workflows for reading, writing, and converting
  Parquet-backed datasets for TensorFlow, PyTorch, Spark, and plain Python."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Petastorm

Petastorm is a data-access library for Apache Parquet datasets with ML-friendly schemas, readers, and Spark-based dataset creation tools.
Use this skill when the task mentions Petastorm, `make_reader`, `make_batch_reader`, `materialize_dataset`, `SparkDatasetConverter`,
`Unischema`, Petastorm metadata repair, or the `petastorm-*.py` console tools.

## Start here

- Read `references/repo-provenance.md` if you need to know whether this skill matches the current checkout snapshot.
- Run `scripts/check_install.py` to confirm the package imports, optional dependencies, and command entry points.
- Run `scripts/smoke_spark_session.py` when Spark or Java availability is in doubt.
- Read `references/install-and-prereqs.md` for installation, extras, and backend prerequisites.
- Read `references/workflow-overview.md` when you are choosing between the read, write, or Spark-converter routes.
- Read `references/filesystems-and-paths.md` before diagnosing URL, HDFS, S3, or GCS path problems.
- Read `references/schema-and-codecs.md` before designing or repairing a schema or codec.
- Read `references/troubleshooting.md` before chasing import-order, Spark, URL, or metadata errors.

## Choose a route

### `sub-skills/read-datasets/`

Use this route for reading Petastorm datasets or plain Parquet stores, applying predicates or NGrams, shuffling rows,
using TensorFlow or PyTorch adapters, reading into Spark RDDs, or running throughput benchmarks.

Helpful bundled files:

- `sub-skills/read-datasets/references/workflows.md`
- `sub-skills/read-datasets/references/cli-reference.md`
- `sub-skills/read-datasets/references/troubleshooting.md`
- `sub-skills/read-datasets/scripts/smoke_read_minimal_dataset.py`
- `sub-skills/read-datasets/scripts/smoke_read_plain_parquet.py`
- `sub-skills/read-datasets/scripts/smoke_read_tensorflow.py`
- `sub-skills/read-datasets/scripts/smoke_read_torch.py`

### `sub-skills/create-datasets/`

Use this route for defining schemas and codecs, materializing datasets, copying or filtering datasets, regenerating metadata,
and building row-group indexes or dataset fixes from existing Parquet data.

Helpful bundled files:

- `sub-skills/create-datasets/references/workflows.md`
- `sub-skills/create-datasets/references/cli-reference.md`
- `sub-skills/create-datasets/references/data-formats.md`
- `sub-skills/create-datasets/references/troubleshooting.md`
- `sub-skills/create-datasets/scripts/smoke_make_minimal_dataset.py`
- `sub-skills/create-datasets/scripts/smoke_copy_dataset.py`
- `sub-skills/create-datasets/scripts/smoke_generate_metadata.py`

### `sub-skills/spark-converter/`

Use this route for `make_spark_converter`, cached Spark DataFrame materialization, and creating TensorFlow or PyTorch loaders
from a Spark-backed cache directory.

Helpful bundled files:

- `sub-skills/spark-converter/references/workflows.md`
- `sub-skills/spark-converter/references/troubleshooting.md`
- `sub-skills/spark-converter/scripts/smoke_spark_converter.py`

## Installation and prerequisites

- Core install: `pip install petastorm`
- Common extras: `petastorm[tf]`, `petastorm[torch]`, `petastorm[opencv]`, `petastorm[s3fs]`
- Spark-backed workflows require a working Java runtime and PySpark.
- If you use PyTorch, import `pyarrow` before `torch`.

## Minimal import check

```bash
python - <<'PY'
import pyarrow
import petastorm
from petastorm import make_reader, make_batch_reader

print(petastorm.__version__)
print(make_reader.__name__, make_batch_reader.__name__)
PY
```

When you need TensorFlow, PyTorch, OpenCV, or S3/GCS support, read the relevant sub-skill reference first so you add only the needed extras.
