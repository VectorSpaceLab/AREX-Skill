# Troubleshooting

## Import or install failures
- Make sure the base `py-data-juicer` package is installed and importable.
- If a local operator is missing, check whether it depends on an optional extra.

## Dataset and config errors
- Confirm the input path exists.
- Check whether the recipe expects `dataset_path` or a structured dataset config.
- Simplify the process list if you are unsure which operator caused the failure.

## Export problems
- Verify the export path is writable.
- Make sure the requested export format matches the downstream consumer.
- If shard settings are present, test with one shard first.

## JSONL issues
- Use lenient loading if the input contains malformed or oversized rows.
- If a row still fails, isolate the row before changing the full recipe.

## Cache and tracing
- Turn cache off when debugging logic changes.
- Turn tracing off unless you need per-operator diagnostics.

## Custom operator issues
- Check that the custom operator path is correct.
- Avoid name collisions with built-in operators.
- If the operator needs extra packages, document them next to the recipe.
