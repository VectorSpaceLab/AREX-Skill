# Data-pipeline troubleshooting

- **`FileNotFoundError` or missing table:** confirm the dataset family and
  release-specific root/config; do not substitute a MIMIC-III layout for
  MIMIC-IV or OMOP. Stop if access or de-identification requirements are not
  satisfied.
- **Zero samples:** inspect source row counts, date filters, task pre-filter,
  patient IDs, and required event types. Validate the task separately on a
  synthetic patient before increasing worker count.
- **`Input schema does not match samples`:** print the union of sample keys and
  compare it with `input_schema`/`output_schema`; fix the task or fixture, not
  the serialization layer.
- **Processor shape/type error:** inspect `schema()`, `dim()`, `is_token()`, and
  one processed value. Do not pass a list where a processor expects a tensor or
  a tensor where a sequence tokenizer expects codes.
- **Unexpected patient overlap:** use `split_by_patient`, not visit/sample
  splitting. Assert partition ID sets are disjoint before fitting.
- **Graph/image/audio import error:** install only the relevant package extra
  and re-run the optional probe; a base-package success does not prove that
  optional modality support is installed.
- **Remote root hangs or downloads:** stop, replace it with an authorized local
  root or a bounded fixture, and record the skipped external-data verification.
