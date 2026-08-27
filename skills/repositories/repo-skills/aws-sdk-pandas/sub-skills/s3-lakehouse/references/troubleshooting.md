# S3 Lakehouse Troubleshooting

## Purpose

Use this reference when an S3 read/write/vector workflow fails before the problem has been narrowed to a different sub-skill.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NoCredentialsError` or `NoRegionError` | The boto3 session is not configured | Create or pass an explicit `boto3.Session` with valid credentials and region. |
| `Missing optional dependency 'openpyxl'` | Excel support is not installed | Install `awswrangler[openpyxl]`. |
| `Missing optional dependency 'deltalake'` | Delta Lake support is not installed | Install `awswrangler[deltalake]`. |
| `Missing optional dependency 'pyiceberg'` | S3 Tables / Iceberg support is not installed | Install `awswrangler[pyiceberg]`. |
| `InvalidArgumentCombination` when targeting vectors | The call mixed `index_arn` with `index` / bucket name arguments, or passed both bucket name and ARN | Use one target style consistently. For name-based targeting, pass `index` plus exactly one bucket selector. |
| `InvalidArgumentCombination` from `query_vectors` | The call provided both `query_vector` and `query_text`, or neither | Provide exactly one query mode. |
| `InvalidArgumentValue` from vector helpers | The vector is not one-dimensional, contains NaN/Inf, or `top_k` is outside the allowed range | Flatten the vector, remove non-finite values, or reduce `top_k` to the 1-100 range. |
| Read/write functions return empty frames | The path prefix does not match any objects or the dataset filter excluded all rows | Confirm the path, partition values, and suffix filters. |
| Dataset writes create files but later reads miss rows | The read call forgot `dataset=True` or used the wrong partition root | Make the write/read semantics match and reuse the dataset root. |
| `ArrowInvalid`, dtype mismatch, or schema errors during writes | The frame columns do not match the file format expectations | Normalize the DataFrame dtypes before writing or pass explicit `dtype` / schema settings. |
| S3 Vectors mocks work but live calls fail | The workflow was only validated against the mocked client | Treat live S3 Vectors as an AWS prerequisite and verify the actual service, bucket, and index names. |

## Recovery order

1. Confirm the target path and required dataset flags.
2. Check whether an optional extra is missing.
3. Re-run the safe smoke script in this sub-skill if the path is local or moto-backed.
4. If the workflow depends on real AWS S3 Tables, Vectors, or Delta Lake integration, stop and ask for the required service access instead of guessing.

## Related guidance

- `../../../references/runtime-overview.md` for extras and base install facts.
- `../../../references/troubleshooting.md` for cross-cutting import and credential failures.
- `../../catalog-and-query/references/troubleshooting.md` for Athena or Glue metadata failures.
