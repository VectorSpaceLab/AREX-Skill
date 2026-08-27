# Troubleshooting

## Missing or mismatched columns

Symptom:
- `KeyError`, `ValueError`, or an empty output after a run.

Likely cause:
- The operator expected a different input column name.
- An output column already existed and the operator refused to overwrite it.

Fix:
- Recheck the operator-specific keys in `references/data-formats.md`.
- Align `input_key` / `output_key` or the family-specific `input_*_key` / `output_*_key` names.
- Create a tiny fixture first and confirm the columns before running on a large corpus.

## CPU-safe filters do not need a model

Symptom:
- You only want cleanup or validation, but the workflow seems to call a backend.

Likely cause:
- A model-backed operator was selected too early.

Fix:
- Start with heuristic filters first.
- For text, prefer `general_text` and the pure validation operators in the reasoning, code, and Text2SQL families.
- Move to generation only after the cleaned input looks correct.

## API or remote model failures

Symptom:
- The generation stage fails, times out, or returns empty text.

Likely cause:
- Missing API key, wrong endpoint, wrong model name, or unsupported JSON schema.

Fix:
- Confirm the serving object and its credentials.
- Confirm the model name and endpoint format.
- Reduce the batch size or simplify the prompt before trying a full corpus.
- If the task is only validation, stay on CPU-safe stages.

## Text2Model failures

Symptom:
- `llamafactory` is missing, the config file is not found, or the adapter directory is empty.

Likely cause:
- The init step was skipped.
- The working directory does not contain the expected JSON / JSONL files.
- The local model or training backend is unavailable.

Fix:
- Run the init stage before training.
- Keep the input files in the working directory for the generated helper scripts.
- Check that `.cache/train_config.yaml` exists.
- Verify that `.cache/data/qa.json` was created before training starts.
- Confirm that the saved model directory contains adapter files before opening chat.

## Text2SQL failures

Symptom:
- The workflow cannot find a database, or SQL validation always drops the rows.

Likely cause:
- `db_id` does not match a registered database.
- The database root path is wrong.
- The SQL is not executable or is not a `SELECT` / `WITH` query.

Fix:
- Confirm the database path and database manager configuration.
- Check that each `db_id` is registered.
- Start with `SQLExecutionFilter` before any augmentation or judging stage.
- If you only need a fixture, use a tiny local SQLite database rather than a remote download.

## Downloads and sandbox side effects

Symptom:
- The workflow is slow, downloads weights, or executes unexpected code.

Likely cause:
- A local model, database snapshot, or sandbox evaluator is part of the chosen path.

Fix:
- Treat these stages as side-effecting.
- Do not point code sandbox evaluation at untrusted snippets.
- Do not assume a text2model or Text2SQL workflow is offline just because the source files are local.
- If you only need to check shapes, use `scripts/make_text_fixture.py` and the CPU-safe filters.

## Good recovery pattern

1. Validate the columns with a tiny fixture.
2. Run the pure CPU filters.
3. Run one model-backed stage.
4. Only then scale up to the full dataset.
