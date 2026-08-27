# Troubleshooting

## `ValueError: Data must be a pandas DataFrame`

Cause: `StructuredEngine()` defaults to `PandasDataProcessor`, but the data was a dict/list.

Fix:

```python
from presidio_structured import JsonDataProcessor, StructuredEngine
engine = StructuredEngine(data_processor=JsonDataProcessor())
```

## `ValueError: Data must be a JSON-like object`

Cause: `JsonDataProcessor` was selected but the input is a Pandas DataFrame or another unsupported object.

Fix: use the default `StructuredEngine()` for DataFrames, or convert the data to a dict/list before JSON processing.

## JSON builder fails on nested arrays

Symptom: automatic JSON analysis raises an error similar to `Analyzer.analyze_iterator only works on primitive types` when the JSON contains arrays of objects.

Cause: `JsonAnalysisBuilder` uses batch dictionary analysis. Lists of primitive values are supported; lists of objects are not an automatic-builder input.

Fix: provide a manual `StructuredAnalysis`, for example:

```python
analysis = StructuredAnalysis(
    entity_mapping={
        "users.name": "PERSON",
        "users.email": "EMAIL_ADDRESS",
    }
)
```

Then use `StructuredEngine(data_processor=JsonDataProcessor())`.

## Nested array output is not what you expected

Cause: list-wide dot paths apply to every matching object in a list. Numeric index paths are not a good general substitute. Per-element custom/hash behavior should be validated carefully.

Fixes:

- Use constant replacements for list-wide redaction when possible.
- Flatten the list of objects to a DataFrame, anonymize the columns, and rebuild the JSON.
- Or iterate over each object in the list with a non-array mapping such as `{ "email": "EMAIL_ADDRESS" }`.

## Mapping exists but values did not change

Check:

- For DataFrames, the mapping key exactly matches the column label.
- For JSON, each dot-path segment exactly matches a key in the payload.
- The mapped value is non-empty. Empty values are skipped by JSON processing.
- You copied the output from `StructuredEngine.anonymize(...)`; do not inspect an unrelated original object.
- The operator selected for the entity is not `keep` or another no-op by design.

## A non-PII column was anonymized

Cause: automatic analysis sampled values whose text matched a recognizer, or a manual override included the wrong key.

Fixes:

- Inspect `analysis.entity_mapping` before anonymization.
- Remove the bad key from the mapping.
- Add known identifiers to `keys_to_skip` in batch recipes.
- Tune recognizers, score thresholds, allow lists, or context in `../analyze-text/SKILL.md`.

## Wrong entity type for a column

Use a selection strategy or manual override.

- `most_common`: best for columns where most rows share the same PII type.
- `highest_confidence`: best when one high-confidence result should dominate.
- `mixed`: best when high-confidence signals should win only above a threshold.

If the column meaning is known, override directly:

```python
mapping = dict(analysis.entity_mapping)
mapping["employee_login"] = "EMPLOYEE_LOGIN"
analysis = StructuredAnalysis(entity_mapping=mapping)
```

Then add an `EMPLOYEE_LOGIN` operator or rely on `DEFAULT`.

## `Unsupported entity selection strategy` or invalid mixed threshold

Cause: `selection_strategy` was not one of `most_common`, `highest_confidence`, or `mixed`, or `mixed_strategy_threshold` was outside `0..1`.

Fix: use one of the supported strategy names and a threshold such as `0.5` or `0.75`.

## Missing pandas

Symptom: import errors for Pandas or `presidio_structured`.

Fix: install the structured distribution in the active runtime, for example `pip install presidio-structured`. Pandas is a required dependency of that distribution. If running from an isolated interactive runtime or kernel, verify that the kernel uses the same environment where the package was installed.

## Analyzer model requirement errors

Symptom: constructing a default `AnalyzerEngine` inside an analysis builder fails because the default NLP model is unavailable.

Fixes:

- Install the documented default analyzer model in the active environment.
- Or pass a preconfigured no-download/custom analyzer to `PandasAnalysisBuilder(analyzer=...)` or `JsonAnalysisBuilder(analyzer=...)`.
- For recognizers, languages, model choices, and score thresholds, use `../analyze-text/SKILL.md`.

## Operator is missing or wrong

Symptoms:

- `ValueError: Operator for entity ... not found`
- unexpected replacement text
- custom operator parameters fail

Fixes:

- Prefer calling `StructuredEngine.anonymize(...)`, which adds `DEFAULT` when missing.
- Include a `DEFAULT` operator when calling processors directly.
- Make sure each manual entity label either has an operator key or should use `DEFAULT`.
- Confirm operator names and parameter dictionaries in `../anonymize-text/SKILL.md`.

## Original data changed unexpectedly

Cause: `PandasDataProcessor` and `JsonDataProcessor` mutate the object passed into `anonymize()`.

Fix:

```python
result_df = engine.anonymize(df.copy(deep=True), analysis, operators)

from copy import deepcopy
result_json = json_engine.anonymize(deepcopy(payload), analysis, operators)
```

## CSV batch issues

- Empty CSV: create at least a header and one row before building a dictionary of columns.
- Header mismatch: `keys_to_skip` entries must match CSV header names exactly.
- Encoding/newline issues: open with `encoding="utf-8"` and `newline=""`.
- Large files: chunk with Pandas or stream in bounded batches; do not load very large CSVs all at once.
- CLI-style file scanning is not the same workflow; use `../cli-scans/SKILL.md` for the `presidio` command.
