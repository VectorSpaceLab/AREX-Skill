# Data formats and mappings

Presidio Structured separates **analysis generation** from **operation over mapped fields**. The analysis is a field-to-entity mapping; the engine then applies anonymizer operators to those fields.

## Pandas DataFrames

Use DataFrames when the data is tabular and every PII-bearing field is a column.

```python
import pandas as pd
from presidio_structured import PandasAnalysisBuilder, StructuredEngine
from presidio_anonymizer.entities import OperatorConfig

df = pd.DataFrame(
    {
        "Full Name": ["Alice Doe", "Bob Smith"],
        "e-mail": ["alice@example.com", "bob@example.com"],
        "notes": ["not pii", "not pii"],
    }
)
analysis = PandasAnalysisBuilder(analyzer=my_analyzer).generate_analysis(df)
analysis.entity_mapping.update({"Full Name": "PERSON"})  # optional manual correction

operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
}
anonymized = StructuredEngine().anonymize(df.copy(deep=True), analysis, operators)
```

Format notes:

- Mapping keys must match column labels exactly, including spaces and punctuation.
- Only map columns whose values can be operated on as text. Cast or skip numeric/object columns unless you have tested the operator on those values.
- The default processor mutates the passed DataFrame; copy first if needed.
- Missing mapped columns fail with normal Pandas column lookup errors.

## JSON-like dictionaries

Use JSON processing for dictionaries with primitive text leaves or nested dictionaries.

```python
from copy import deepcopy
from presidio_structured import JsonAnalysisBuilder, JsonDataProcessor, StructuredEngine

record = {
    "name": "Alice Doe",
    "email": "alice@example.com",
    "address": {"city": "Seattle", "line1": "1 Main St"},
}
analysis = JsonAnalysisBuilder(analyzer=my_analyzer).generate_analysis(record)
result = StructuredEngine(data_processor=JsonDataProcessor()).anonymize(
    deepcopy(record), analysis, operators
)
```

Nested dictionary mappings use dot paths:

```python
analysis.entity_mapping == {
    "name": "PERSON",
    "email": "EMAIL_ADDRESS",
    "address.city": "LOCATION",
}
```

## Nested JSON arrays

Automatic JSON analysis does not support arrays of objects. Build a manual `StructuredAnalysis` for these shapes.

```python
from copy import deepcopy
from presidio_structured import JsonDataProcessor, StructuredAnalysis, StructuredEngine

payload = {
    "users": [
        {"name": "Alice Doe", "email": "alice@example.com"},
        {"name": "Bob Smith", "email": "bob@example.com"},
    ]
}
analysis = StructuredAnalysis(
    entity_mapping={
        "users.name": "PERSON",
        "users.email": "EMAIL_ADDRESS",
    }
)
anonymized = StructuredEngine(data_processor=JsonDataProcessor()).anonymize(
    deepcopy(payload), analysis, operators
)
```

Practical guidance for arrays:

- Prefer list-wide dot paths such as `users.email` for redacting the same key in every object of a list.
- Avoid numeric index paths such as `users.0.email` unless you have verified the exact behavior on the installed package version; list-wide mapping or pre-processing one item at a time is safer.
- Constant replacements are the safest array-list operator pattern. If a hash or custom operator must preserve a distinct value per element, flatten to a DataFrame or iterate over list items and process each object independently, then assert the output.

## Manual mapping overrides

Override the generated mapping when the analyzer result is technically correct but operationally wrong.

Examples:

- A column contains email-looking employee logins, but the workflow wants `EMPLOYEE_LOGIN` and a login-specific replacement.
- A mixed identifier column produces `URL` under `most_common`, but the task needs the strongest `EMAIL_ADDRESS` signal.
- A JSON key is known sensitive even when sample values are empty or too short for automatic analysis.

Pattern:

```python
auto_analysis = PandasAnalysisBuilder(analyzer=my_analyzer).generate_analysis(df)
manual_mapping = dict(auto_analysis.entity_mapping)
manual_mapping.update({"record_key": "EMPLOYEE_LOGIN"})
analysis = StructuredAnalysis(entity_mapping=manual_mapping)
```

The entity string only has to match an operator key later. For detection semantics and recognizer configuration, route to `../analyze-text/SKILL.md`.

## CSV inputs

Two supported approaches are common:

1. **DataFrame path:** read CSV with Pandas or `CsvReader`, generate a `StructuredAnalysis`, and call `StructuredEngine`.
2. **Batch dictionary path:** read the CSV into `{column_name: [values...]}`, call `BatchAnalyzerEngine.analyze_dict()`, then `BatchAnonymizerEngine.anonymize_dict()`.

Use the DataFrame path when you want DataFrame output and field-level `StructuredAnalysis`. Use the batch dictionary path when you need a simple column-wise anonymized dictionary or a small portable script. The bundled `scripts/presidio_csv_batch_smoke.py` demonstrates the second path with a tiny fixture and no source-checkout assumptions.
