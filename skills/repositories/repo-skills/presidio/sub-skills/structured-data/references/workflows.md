# Workflows

## 1. DataFrame auto-analysis and anonymization

```python
import pandas as pd
from presidio_structured import PandasAnalysisBuilder, StructuredEngine
from presidio_anonymizer.entities import OperatorConfig

df = pd.DataFrame(
    {
        "name": ["Alice Doe", "Bob Smith"],
        "email": ["alice@example.com", "bob@example.com"],
    }
)

builder = PandasAnalysisBuilder(analyzer=my_analyzer)
analysis = builder.generate_analysis(df, selection_strategy="most_common")

operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
}
result = StructuredEngine().anonymize(df.copy(deep=True), analysis, operators)
```

Use a custom analyzer when the default model is unavailable, when you need no-download pattern recognition, or when the workflow requires specific recognizers. Analyzer setup belongs in `../analyze-text/SKILL.md`.

## 2. DataFrame selection strategy choice

`PandasAnalysisBuilder` reduces many cell-level analyzer results to one entity type per column.

- Start with `most_common` for homogeneous columns with repeated evidence.
- Use `highest_confidence` when a rare but high-confidence detector should dominate.
- Use `mixed` when strong signals should win but weak outliers should not defeat the common case.

```python
analysis = PandasAnalysisBuilder(analyzer=my_analyzer).generate_analysis(
    df,
    n=100,
    selection_strategy="mixed",
    mixed_strategy_threshold=0.75,
)
```

If a field is important, inspect `analysis.entity_mapping` before anonymizing and override suspicious entries manually.

## 3. Manual mapping override

Manual overrides are normal for structured data because field meaning may be clearer than sampled cell values.

```python
from presidio_structured import StructuredAnalysis

auto = PandasAnalysisBuilder(analyzer=my_analyzer).generate_analysis(df)
mapping = dict(auto.entity_mapping)
mapping.update(
    {
        "employee_login": "EMPLOYEE_LOGIN",
        "support_ticket": "PROJECT_CODE",
    }
)
analysis = StructuredAnalysis(entity_mapping=mapping)

operators = {
    "EMPLOYEE_LOGIN": OperatorConfig("replace", {"new_value": "<LOGIN>"}),
    "PROJECT_CODE": OperatorConfig("replace", {"new_value": "<PROJECT_CODE>"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
}
result = StructuredEngine().anonymize(df.copy(deep=True), analysis, operators)
```

The custom entity labels are valid as long as they match operator keys. If the override should also influence detection, add or tune recognizers in the analyzer sub-skill.

## 4. Simple JSON auto-analysis

For nested dictionaries without arrays of objects, use `JsonAnalysisBuilder` and `JsonDataProcessor`.

```python
from copy import deepcopy
from presidio_structured import JsonAnalysisBuilder, JsonDataProcessor, StructuredEngine

data = {
    "name": "Alice Doe",
    "email": "alice@example.com",
    "address": {"city": "Seattle"},
}
analysis = JsonAnalysisBuilder(analyzer=my_analyzer).generate_analysis(data)
result = StructuredEngine(data_processor=JsonDataProcessor()).anonymize(
    deepcopy(data), analysis, operators
)
```

## 5. Nested JSON arrays with manual dot-path mapping

For arrays of objects, skip automatic JSON analysis and provide the mapping yourself.

```python
from copy import deepcopy
from presidio_structured import JsonDataProcessor, StructuredAnalysis, StructuredEngine

payload = {
    "users": [
        {"name": "Alice Doe", "email": "alice@example.com"},
        {"name": "Bob Smith", "email": "bob@example.com"},
    ],
    "owner": {"name": "Carol Jones"},
}
analysis = StructuredAnalysis(
    entity_mapping={
        "users.name": "PERSON",
        "users.email": "EMAIL_ADDRESS",
        "owner.name": "PERSON",
    }
)
result = StructuredEngine(data_processor=JsonDataProcessor()).anonymize(
    deepcopy(payload), analysis, operators
)
```

Validate nested outputs after anonymization. If per-element unique hashing/custom output matters, flatten the list or process each object independently before reassembling the payload.

## 6. Operator reuse across structured fields

Structured data uses the same `OperatorConfig` objects as text anonymization. A single operator map can serve DataFrame columns and JSON paths:

```python
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "PHONE_NUMBER": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 8, "from_end": True}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
}
```

For exact operator parameters, encryption/decryption details, custom operators, and error meanings, use `../anonymize-text/SKILL.md`.

## 7. CSV/batch recipe

For a small CSV where column-wise output is enough:

```python
import csv
from presidio_analyzer import BatchAnalyzerEngine
from presidio_anonymizer import BatchAnonymizerEngine

with open(csv_path, newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
column_dict = {field: [row[field] for row in rows] for field in rows[0]}

results = list(
    BatchAnalyzerEngine(analyzer_engine=my_analyzer).analyze_dict(
        column_dict,
        language="en",
        keys_to_skip=["id"],
    )
)
anonymized_columns = BatchAnonymizerEngine().anonymize_dict(results, operators=operators)
```

Use `scripts/presidio_csv_batch_smoke.py` for a portable version that creates a tiny fixture when no CSV is supplied.

## 8. Verification checks after a structured run

Always check:

- The mapping contains every sensitive field/path you expected.
- The mapping does not include ID, category, or non-PII fields that must remain unchanged.
- The processor matches the input type.
- The operator map includes entity-specific behavior or a safe `DEFAULT`.
- Output shape and row/list counts match input shape.
- The original object was copied if mutation would be unsafe.
