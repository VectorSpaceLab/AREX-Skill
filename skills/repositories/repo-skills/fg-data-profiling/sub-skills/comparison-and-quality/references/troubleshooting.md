# Comparison and Quality Troubleshooting

## Too few or mixed reports

Symptom: `ValueError` for fewer than two reports, or `TypeError` when mixing
`ProfileReport` objects with raw description objects.

Recovery:
- Build at least two comparable inputs.
- Pass either all reports or all descriptions, not a mixture.

## Time-series mismatch

Symptom: comparison between time-series and tabular reports is rejected.

Recovery: compare like with like. If the user needs a cross-mode view, compute a
plain tabular comparison of the same preprocessing stage instead.

## Different columns warning

Symptom: the comparison warns that datasets have different column sets.

Recovery: align columns before comparing, or intentionally use the left report
as the base and explain that only shared columns will be compared.

## Sensitive values still appear

If raw names or identifiers are visible in the report, check:
- whether `sensitive=True` was enabled;
- whether samples or duplicates were explicitly turned off;
- whether the user supplied a custom sample with real data;
- whether numeric identifiers were coerced to numbers at file-read time.

For phone numbers and similar identifiers, force string dtype at load time.

## Great Expectations dependency errors

`to_expectation_suite()` still exists in source but depends on `great_expectations`.
If the package is missing, the method raises `ImportError`. If a user expects the
older full integration documented in historical examples, explain the current
version caveat and offer JSON/description-based quality outputs instead.

## Custom sample issues

If the custom sample is not shown or values are missing, verify that the sample
payload contains a DataFrame-like `data`, a readable `name`, and an optional
`caption`. The sample should be synthetic when privacy matters.
