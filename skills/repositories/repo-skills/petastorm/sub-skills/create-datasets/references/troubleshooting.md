# Troubleshooting

## Purpose

Read this when a write-side workflow fails because of a schema, Spark, filesystem, or metadata problem.

## Failure map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Spark session will not start | Java or PySpark is missing | Run `scripts/smoke_spark_session.py` first |
| `ValueError` about a schema field or shape | The `Unischema` or row dictionary does not match the declared contract | Fix the field name, dtype, shape, or nullability |
| Non-scalar field without a codec | A multidimensional field was declared with `codec=None` | Add `NdarrayCodec`, `CompressedNdarrayCodec`, or `CompressedImageCodec` |
| Copy command says regexes matched nothing | The selected `field_regex` does not match any fields | Tighten the regex or inspect the schema first |
| Copy output still contains nulls | The field was not included in `--not-null-fields` | Add the field to the non-null list and rerun |
| Metadata regeneration fails | The dataset is missing the schema information needed for repair | Supply `--unischema_class` or write the schema back before repair |
| Row-group selection is ineffective | No row-group index was built | Call `build_rowgroup_index` before trying selector-aware reads |
| HDFS, S3, or GCS paths fail | The matching filesystem package or credentials are missing | Install the needed filesystem package or use a local `file://` smoke path first |
| `setuptools` incompatibility appears during install | The environment does not honor the repo pin | Install with `setuptools<70` in the inspection environment |
| Historical codec tests fail on NumPy 1.26+ | Archived test helpers still use removed `np.bool` or `np.float` aliases | Use the bundled smoke helpers and current schema/codecs guidance; patch the historical tests or run them in an older NumPy environment if you specifically need them |

## Recovery checklist

1. Run `scripts/check_install.py` to confirm the core install surface.
2. Run `scripts/smoke_spark_session.py` if Spark is not clearly available.
3. Start with `scripts/smoke_make_minimal_dataset.py` to confirm writing works.
4. Use `scripts/smoke_copy_dataset.py` to isolate copy/filter problems.
5. Use `scripts/smoke_generate_metadata.py` to isolate metadata repair problems.

## Practical tips

- Prefer tiny local `file://` paths until the logic is working.
- Do not guess at field regexes; verify the schema first.
- Keep row dictionaries and `Unischema` definitions synchronized.
- When using image or ndarray fields, confirm the codec and shape contract before touching Spark write code.
