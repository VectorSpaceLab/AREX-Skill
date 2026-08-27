# CLI Reference

## Purpose

Read this when the user wants the package console tools rather than the Python API.
The verified commands in this route are the copy and metadata repair tools.

## `petastorm-copy-dataset.py`

### Shape

```text
petastorm-copy-dataset.py SOURCE_URL TARGET_URL [options]
```

### Verified options

| Option | Meaning |
| --- | --- |
| `source_url` | Source Petastorm dataset URL |
| `target_url` | Destination dataset URL |
| `--overwrite-output` | Allow overwriting an existing output path |
| `--field-regex FIELD_REGEX [FIELD_REGEX ...]` | Keep only matching columns |
| `--not-null-fields NOT_NULL_FIELDS [NOT_NULL_FIELDS ...]` | Drop rows with nulls in these fields |
| `--partition-count` | Repartition before write |
| `--row-group-size-mb` | Row-group size for the copied dataset |
| `--hdfs-driver` | HDFS driver selection |
| `--master` | Spark master |
| `--spark-session-config KEY=VALUE ...` | Extra Spark session settings |

### Example

```bash
petastorm-copy-dataset.py file:///tmp/source file:///tmp/target \
  --field-regex '^id$' '^score$' \
  --not-null-fields score \
  --overwrite-output
```

## `petastorm-generate-metadata.py`

### Shape

```text
petastorm-generate-metadata.py --dataset_url DATASET_URL [options]
```

### Verified options

| Option | Meaning |
| --- | --- |
| `--dataset_url` | Dataset directory to repair |
| `--unischema_class` | Fully qualified `Unischema` class string when inference is not possible |
| `--master` | Spark master |
| `--spark-driver-memory` | Driver memory setting |
| `--use-summary-metadata` | Rebuild metadata using Parquet summary metadata |
| `--hdfs-driver` | HDFS driver selection |

### Example

```bash
petastorm-generate-metadata.py \
  --dataset_url file:///tmp/target \
  --master local[1]
```

### Behavior notes

- The command can often infer the schema from existing metadata.
- Summary metadata is useful for some small or local repair cases, but large datasets may prefer the default path.
- If the dataset is missing the schema metadata entirely, supply `--unischema_class`.

## Spark session configuration helper

Both commands share the same Spark-session configuration parser.
The `--spark-session-config` values must be passed as `key=value` pairs.
