# Pipeline foundations troubleshooting

## `Key Matching Error in following Operators during pipeline.compile()`

Meaning: an `input_*` parameter names a column that is not in the initial input file and was not produced by an earlier `output_*` parameter.

Fix:

1. Run `scripts/validate_tabular_input.py INPUT --required col_a col_b` for source columns.
2. Compare the missing key in the error message with the exact `input_*` value in pipeline `forward()`.
3. Check casing, spaces, singular/plural differences, and earlier `output_*` names.
4. If the missing key should be produced by an earlier operator, confirm the earlier operator appears first in `forward()` and writes `output_same_name`.
5. Reconstruct the pipeline object and call `compile()` again.

## Warning: unexpected key in operator node

DataFlow treats string keyword arguments whose names start with `input_` or `output_` as graph keys. Other captured kwargs can print warnings. Prefer constructor arguments for fixed configuration such as thresholds, modes, prompts, and batch sizes.

## `Storage must be a DataFlowStorage object`

Meaning: compile captured an operator call where the `storage` argument was missing or was not a DataFlow storage object.

Fix:

- Pass `storage=self.storage.step()` to every operator call in pipeline `forward()`.
- Keep `storage` as the first logical parameter in custom `OperatorABC.run` definitions.
- Do not pass a path string, dataframe, or unstepped storage factory in place of storage.

## `You must call storage.step() before reading or writing data`

Meaning: `read()` or `write()` was called while `operator_step == -1`.

Fix:

- Inside a pipeline, pass `self.storage.step()` into each operator.
- Outside a pipeline, do:

```python
storage = FileStorage("input.jsonl", cache_path="cache", file_name_prefix="run", cache_type="jsonl").reset()
storage.step()
dataframe = storage.read(output_type="dataframe")
```

- To read a later cache file, call `step()` until the desired step number is current.

## Output cache file not found

Likely causes:

- The pipeline was compiled but the compiled `forward()` was not run.
- The operator did not call `storage.write(...)`.
- You are looking at the wrong step number: a one-operator pipeline writes step 1; a two-operator pipeline writes step 2.
- A different `file_name_prefix` or `cache_path` was used.
- A batched run resumed from a last-success marker and skipped work.

Fix with a unique `file_name_prefix` and, for batched runs, set `resume_from_last=False` when you want to overwrite from the beginning.

## Unsupported file type or failed file load

- Use JSONL or CSV for the most portable fixtures.
- For `.xlsx`, pass `cache_type="xlsx"` and ensure Excel dependencies are installed.
- For Parquet, ensure a pandas Parquet engine is installed.
- For Pickle, use trusted files only.
- Remote `hf:` and `ms:` sources can fail offline; replace them with local fixture files when validating foundations.

## `DummyStorage()` cannot be instantiated

In `open-dataflow` 1.0.10, `DummyStorage` is public but may still be abstract because it does not implement `get_keys_from_dataframe`. If direct instantiation or `BatchWrapper` fails with `TypeError: Can't instantiate abstract class DummyStorage ...`, use one of these workarounds:

- Use `FileStorage` for smoke tests and custom pipeline verification.
- Use `BatchedPipelineABC` plus `BatchedFileStorage` instead of `BatchWrapper` when possible.
- In application code, define a tiny `DataFlowStorage` subclass that implements `get_keys_from_dataframe`, `read`, and `write`.

## `prompt_template` type errors

`prompt_restrict` accepts only:

- `None`.
- Instances of whitelisted prompt classes passed to the decorator.
- Instances of `DIYPromptABC` subclasses.

Fix by passing an instance, not the prompt class object itself, and by subclassing `DIYPromptABC` for custom prompts. If the operator has no `prompt_template` constructor parameter, the decorator records allowed prompts but cannot validate a nonexistent parameter.

## `draw_graph` fails

- `ImportError` mentioning `pyvis`: install `pyvis` in the runtime environment or skip graph rendering.
- `Pipeline is not compiled yet`: call `pipeline.compile()` first.
- Port already in use: pass `port=0` or a free explicit port.
- Non-interactive job hangs: `draw_graph` starts an HTTP server and blocks; use it only in interactive debugging.

## Batched resume surprises

Symptoms: a batched run skips steps, appends partial data, or resumes at an unexpected batch.

Fix:

- Use a unique `file_name_prefix` for every independent run.
- Delete or ignore `{file_name_prefix}_last_success_step.txt` when starting over.
- Use `resume_from_last=False` to overwrite from the beginning.
- Do not combine `resume_step > 0` with `resume_from_last=True`.
- For streaming, use `StreamBatchedFileStorage`; for ordinary batching, use `BatchedFileStorage`.

## Non-TTY `dataflow env` failure

The package CLI environment command can fail in non-interactive contexts with `Errno 25: Inappropriate ioctl for device` because it queries terminal size. This does not prove that the package import or pipeline APIs are broken. In CI or agent shells, prefer import-based diagnostics and the bundled smoke scripts. Use a real TTY only when you specifically need the CLI environment display.

## Boundary reminders

- Serving/API/model failures belong to the `serving-cli` sub-skill.
- Text/document workflow schema choices belong to the `text-workflows` or `document-vision-rag` sub-skills.
- Ray actor lifecycle and resource allocation belong to the `rayorch-acceleration` sub-skill.
