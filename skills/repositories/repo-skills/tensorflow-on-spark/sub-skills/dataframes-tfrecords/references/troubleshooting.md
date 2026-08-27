# Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| `Unsupported dtype: ...` | The DataFrame contains a type outside the supported primitive and primitive-array set. | Select or cast supported columns before calling `saveAsTFRecords`. Flatten structs and maps first. |
| Bytes reload as strings, or strings reload as raw bytes | `BytesList` was read without the correct `binary_features` hint. | Pass the same feature-name list to `infer_schema`, `fromTFExample`, and `loadTFRecords`. |
| `ClassNotFoundException` for `org.tensorflow.hadoop.io.TFRecordFileInputFormat` or `org.tensorflow.hadoop.io.TFRecordFileOutputFormat` | The TensorFlow Hadoop jar is missing from the Spark classpath. | Add the jar with `--jars` or your cluster classpath, then rerun. |
| `loadTFRecords` fails on an empty directory | The loader probes the first record with `take(1)[0]`. | Make sure the TFRecord directory contains at least one record before loading. |
| Row contents change shape or type between records | `loadTFRecords` infers schema from the first example only. | Keep the feature set and dtypes consistent across all records. |
| `mnist_reshape.py` rejects the input row | The CSV line does not contain one label plus 784 pixel values. | Verify the row shape before piping it into the helper. |

## Fast diagnosis order

1. Run [schema probe](../scripts/tfos_tfrecord_schema_probe.py) in pure mode.
2. If pure mode passes, but Spark mode fails, focus on classpath or Spark runtime setup.
3. If Spark mode passes, but your own job fails, the problem is usually a data-shape mismatch or a missing `binary_features` hint.

## Stop conditions

Do not keep retrying conversion when the input requires a nested schema, ragged structures, or other non-flat records. Normalize the data first, then try again.
