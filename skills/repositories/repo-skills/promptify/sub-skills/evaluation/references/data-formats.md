# Evaluation Data Formats

## Purpose

Read this when you need to prepare a dataset for Promptify evaluation or debug a dataset-loading failure.

## Accepted sources

`load_dataset()` accepts three source types:

- a Python list of dictionaries
- a JSON file path
- a CSV file path

## Common item schema

Every item must contain at least:

- input: the text passed to the task
- expected: the expected output value

Additional keys are preserved and passed through to `evaluate()` as extra kwargs for the task call.

## List of dictionaries

Example:

```python
[
    {"input": "Great product", "expected": "positive"},
    {"input": "Bad product", "expected": "negative"},
]
```

## JSON files

- The file must contain a JSON list of objects.
- Each object must still have input and expected.
- The loader rejects a JSON object at the top level.

Example:

```json
[
  {"input": "Great product", "expected": "positive"},
  {"input": "Bad product", "expected": "negative"}
]
```

## CSV files

- The CSV must have input and expected columns.
- Any other columns are preserved.
- The loader tries to JSON-decode the expected column before falling back to the raw string.

Example:

```csv
input,expected,reply
"Great product","positive","positive"
"Bad product","negative","negative"
```

JSON-decoded expected example:

```csv
input,expected
"Alice is 30","{\"name\": \"Alice\", \"age\": 30}"
```

In that case, the expected value becomes a dictionary after loading.

## Practical notes

- For QA tasks, extra keys such as question are forwarded to the task call.
- The dataset does not need to mirror the task output type exactly, but it should be comparable with the chosen metric.
- If a row is missing input or expected, the loader raises ValueError before evaluation begins.
