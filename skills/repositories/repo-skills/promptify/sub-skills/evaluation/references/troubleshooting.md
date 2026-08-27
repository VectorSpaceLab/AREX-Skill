# Evaluation Troubleshooting

## Purpose

Read this when dataset loading or scoring fails.

## Empty dataset

### Symptoms
- `EvaluationError: Dataset is empty`

### Likely causes
- The dataset file is empty.
- The caller filtered away every row.

### Recovery
- Check the loaded sample count before evaluation.
- Confirm that the JSON list or CSV file really contains rows.

## Missing input or expected

### Symptoms
- `ValueError` about a dataset item missing input or expected

### Likely causes
- A row is malformed.
- A CSV column is missing or spelled differently.

### Recovery
- Ensure every sample has both input and expected.
- Standardize column names before loading the file.

## Unsupported dataset format

### Symptoms
- `ValueError: Unsupported file format`
- A file path with an unexpected suffix

### Likely causes
- The dataset is not JSON, CSV, or an in-memory list.
- The extension does not match the file contents.

### Recovery
- Convert the dataset to JSON or CSV.
- Re-check the file suffix.

## Unknown metric

### Symptoms
- `EvaluationError: Unknown metric`

### Likely causes
- The metric name is misspelled.
- The metric is not part of the registry.

### Recovery
- Use one of precision, recall, f1, accuracy, exact_match, or rouge.
- Confirm the spelling in the metric registry.

## ROUGE is missing

### Symptoms
- `ImportError` mentioning rouge-score
- ROUGE evaluation fails even though the rest of the package imports

### Likely causes
- The evaluation extra was not installed.

### Recovery
- Install the package with `python -m pip install -e '.[eval]'`.
- If you do not need ROUGE, use the other metrics instead.

## Task failures become zero scores

### Symptoms
- The evaluation run completes, but the score is unexpectedly low.
- A provider exception appears in the logs, but evaluation continues.

### Likely causes
- The task raised an exception for one or more samples.
- The provider returned malformed output.

### Recovery
- Re-run the task on the same sample outside evaluate().
- Fix the task prompt, provider configuration, or output schema.
- Remember that evaluate() converts a task exception into 0.0 for that sample and metric.

## CSV expected column decoded unexpectedly

### Symptoms
- The expected value turns into a dictionary or list instead of a raw string.

### Likely causes
- The expected cell was valid JSON, so the loader decoded it on purpose.

### Recovery
- Quote plain strings carefully if you want them to stay strings.
- Use JSON only when you want structured expected values.

## When to stop

If the remaining issue is not the dataset or metrics but the task prompt or provider output, switch back to the structured-tasks route.
