# GAIA Evaluation Workflow

## Construct and load

Create:

```python
benchmark = GAIABenchmark(data_dir="/secure/gaia-data", save_to="results.json", processes=1)
benchmark.load(force_download=False)
```

`load()` checks `data_dir/2023/validation` and `data_dir/2023/test`. Each split
needs `metadata.parquet` or `metadata.jsonl`. Parquet records are converted to
dictionaries; JSONL records are read line by line. The loader ignores the
sentinel task id `0-0-0-0-0` and turns a non-empty `file_name` into a path rooted
at the split directory. `download()` uses the Hugging Face dataset
`gaia-benchmark/GAIA` and writes into the selected data directory; this is a
network/data-download side effect.

`train` is deliberately unsupported. The benchmark has validation and test
sets only in this implementation.

## Select work

```python
summary = benchmark.run(
    user_role_name="user",
    assistant_role_name="assistant",
    user_agent_kwargs={"model": user_model},
    assistant_agent_kwargs={"model": assistant_model},
    on="valid",                 # or "test"
    level="all",                # 1, 2, 3, a list, or all
    randomize=False,
    subset=5,
    idx=None,
    save_result=True,
)
```

- `on` must be `valid` or `test`.
- `level` accepts integer 1, 2, 3, a list of those values, or `all`.
- `randomize=True` shuffles the selected records before `subset` truncation.
- `idx` selects positions in the already-filtered list. Use a stable, recorded
  selection when comparing runs.
- `save_result=True` loads an existing result JSON if readable, skips completed
  task ids, and writes results after each processed task. Keep the result path
  private and writable.

## Attached files

`_prepare_task` verifies an attachment exists. It appends an informative file
phrase to the question based on suffix: document (`.pdf`, `.docx`, `.doc`,
`.txt`), image (`.jpg`, `.jpeg`, `.png`), table (`.xlsx`, `.xls`, `.csv`),
Python (`.py`), or a generic file. Missing files cause a false preparation
result and a zero-score record with no model answer. Route actual parsing needs
to [document-processing](../../document-processing/SKILL.md).

## Loop and result shape

For each prepared task, OWL creates `OwlGAIARolePlaying` with the task prompt,
executes `run_society`, extracts the text between `<final_answer>` tags, and
records task id, question, level, model answer, ground truth, score, token info,
and history. The final summary is:

```json
{"total": 0, "correct": 0, "results": [], "accuracy": 0}
```

The actual result entries contain the detailed fields above. A model error is
logged and may leave the task without a normal result entry; inspect logs and
result counts rather than assuming it was scored.

## Scoring rules

1. If the ground truth parses as a float, remove `$`, `%`, and commas from the
   model answer and compare numeric values.
2. If the ground truth contains `,` or `;`, split both answers on either
   delimiter. Numeric elements use numeric normalization; string elements use
   lowercased, whitespace-free comparison while retaining punctuation.
3. Otherwise compare lowercased, whitespace-free strings with punctuation
   removed.

Use the exact format requested by each GAIA task. `<analysis>` is allowed in
GAIA role-playing, but `<final_answer>` must contain only the expected answer
form. Read [troubleshooting.md](troubleshooting.md) before interpreting a
zero-score or malformed-answer result.
